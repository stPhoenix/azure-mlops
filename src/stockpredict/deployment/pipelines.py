from azure.ai.ml.dsl import pipeline
from azure.ai.ml.constants import AssetTypes as _, InputOutputModes as IOMode
from azure.ai.ml import spark, Input, Output, ManagedIdentityConfiguration
from azure.ai.ml.exceptions import ValidationException

from stockpredict.deployment.components import (pytorch_train_component, register_model_component, deploy_model_component)
from pathlib import Path

SOURCE_DIR = Path(__file__).parent.parent.parent.as_posix()

spark_etl_component = spark(
    experiment_name="ETL",
    display_name="Spark Job",
    code=SOURCE_DIR,
    entry={"file": "stockpredict/etl/cleaner.py"},
    driver_cores=1,
    driver_memory="8g",
    executor_cores=2,
    executor_memory="8g",
    executor_instances=2,
    conf={"spark.hadoop.aml.enable_cache": "true"},
    resources={
        "instance_type": "Standard_E4S_V3",
        "runtime_version": "3.3.0",
    },
    inputs={
        "input_data": Input(type=_.URI_FOLDER, mode=IOMode.DIRECT),
        "output_data": Input(type=_.URI_FOLDER, mode=IOMode.DIRECT),
    },
    outputs={
        "clean_data": Output(type=_.URI_FOLDER, mode=IOMode.DIRECT),
    },
    args="--input_data ${{inputs.input_data}} --output_data ${{outputs.clean_data}}",
)

spark_fetcher_component = spark(
    experiment_name="Fetcher",
    display_name="Spark Job",
    code=SOURCE_DIR,
    entry={"file": "stockpredict/fetcher/main.py"},
    driver_cores=1,
    driver_memory="2g",
    executor_cores=2,
    executor_memory="2g",
    executor_instances=2,
    conf={"spark.hadoop.aml.enable_cache": "true"},
    resources={
        "instance_type": "Standard_E4S_V3",
        "runtime_version": "3.3.0",
    },
    inputs={
        "input_path": Input(type=_.URI_FOLDER, mode=IOMode.DIRECT),
        "markers": Input(type="string"),
        "az_kv_name": Input(type="string", default=None),
        "az_api_sname": Input(type="string", default=None),
    },
    outputs={
        "raw_data": Output(type=_.URI_FOLDER, mode=IOMode.DIRECT),
    },
    args="--input_path ${{inputs.input_path}} --markers ${{inputs.markers}} --az_kv_name ${{inputs.az_kv_name}} --az_api_sname ${{inputs.az_api_sname}}",
)


@pipeline()
def etl_pipeline(
        input_data: Input(type=_.URI_FOLDER, mode=IOMode.DIRECT),
        output_data: Input(type=_.URI_FOLDER, mode=IOMode.DIRECT),
):
    spark_step = spark_etl_component(input_data=input_data, output_data=output_data)

    try:
        output = output_data.path
    except ValidationException:
        output = "azureml://datastores/cleaned/paths/"

    spark_step.outputs.clean_data = Output(type=_.URI_FOLDER, mode=IOMode.DIRECT, path=output)

    return {
        "clean_data": spark_step.outputs.clean_data
    }


@pipeline()
def fetch_data_pipeline(
        input_path: Input(type=_.URI_FOLDER, mode=IOMode.DIRECT),
        markers: Input(type="string", description="Comma separated list of markers to fetch"),
        keyvault_name: Input(type="string", default="keyvault-name"),
        api_secret_name: Input(type="string", default="apikey"),
):
    fetch_data_step = spark_fetcher_component(input_path=input_path, markers=markers, az_kv_name=keyvault_name,
                                              az_api_sname=api_secret_name)
    try:
        output = input_path.path
    except ValidationException:
        output = "azureml://datastores/raw/paths/data"

    fetch_data_step.outputs.raw_data = Output(type=_.URI_FOLDER, mode=IOMode.DIRECT, path=output)

    return {

        "data": fetch_data_step.outputs.raw_data
    }


@pipeline()
def train_register_pipeline(
        input_data: Input(type=_.URI_FOLDER, mode=IOMode.RO_MOUNT),
        epochs: Input(type="integer", default=100),
        batch_size: Input(type="integer", default=64),
        shuffle: Input(type="boolean", default=True),
        learning_rate: Input(type="number", default=0.01),
        subscription_id: Input(type="string"),
        resource_group: Input(type="string"),
        workspace_name: Input(type="string"),
        model_name: Input(type="string", default="stock_prediction_pytorch"),
        client_id: Input(type="string"),
):
    train_job = pytorch_train_component(input_data=input_data,
                                        epochs=epochs,
                                        learning_rate=learning_rate,
                                        batch_size=batch_size,
                                        shuffle=shuffle,
                                        )
    register_job = register_model_component(input_model=train_job.outputs.output_model,
                                            model_name=model_name,
                                            subscription_id=subscription_id,
                                            resource_group=resource_group,
                                            workspace_name=workspace_name,
                                            client_id=client_id)

    return {
        "model_dir": train_job.outputs.output_model,
        "registered_model_metadata": register_job.outputs.output_metadata
    }


@pipeline()
def fetch_etl_train_register_deploy_pipeline(
        input_data: Input(type=_.URI_FOLDER, mode=IOMode.DIRECT),
        markers: Input(type="string", description="Comma separated list of markers to fetch"),
        output_data: Input(type=_.URI_FOLDER, mode=IOMode.DIRECT),
        epochs: Input(type="integer", default=100),
        batch_size: Input(type="integer", default=64),
        shuffle: Input(type="boolean", default=True),
        learning_rate: Input(type="number", default=0.01),
        subscription_id: Input(type="string"),
        resource_group: Input(type="string"),
        workspace_name: Input(type="string"),
        model_name: Input(type="string", default="stock_prediction_pytorch"),
        client_id: Input(type="string"),
        keyvault_name: Input(type="string", default="keyvault-name"),
):
    fetch_data = fetch_data_pipeline(input_path=input_data, markers=markers, keyvault_name=keyvault_name)
    spark_job = etl_pipeline(input_data=fetch_data.outputs.data, output_data=output_data)
    train_job = pytorch_train_component(input_data=spark_job.outputs.clean_data,
                                        epochs=epochs,
                                        learning_rate=learning_rate,
                                        batch_size=batch_size,
                                        shuffle=shuffle,
                                        )
    train_job.identity = ManagedIdentityConfiguration(client_id=client_id)
    register_job = register_model_component(input_model=train_job.outputs.output_model,
                                            model_name=model_name,
                                            subscription_id=subscription_id,
                                            resource_group=resource_group,
                                            workspace_name=workspace_name,
                                            client_id=client_id)
    deploy_job = deploy_model_component(input_model=register_job.outputs.output_metadata,
                                        subscription_id=subscription_id,
                                        resource_group=resource_group,
                                        workspace_name=workspace_name,
                                        client_id=client_id,
                                        keyvault_name=keyvault_name)
