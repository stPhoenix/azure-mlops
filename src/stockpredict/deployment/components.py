import json
import os.path
import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).parent.parent.parent.as_posix()
sys.path.append(SOURCE_DIR)

from mldesigner import command_component
from azure.ai.ml import Input, Output
from azure.ai.ml.constants import AssetTypes as _, InputOutputModes as IOMode
from azure.ai.ml.entities import Model, ResourceConfiguration, ManagedOnlineDeployment, CodeConfiguration, \
    ManagedOnlineEndpoint
from stockpredict.deployment.environments import ENV_NAME
import logging
from azure.ai.ml import MLClient
from azure.identity import ManagedIdentityCredential
from stockpredict.settings import MODEL_NAME, OUTPUT_MODEL_METADA_FILE

logging.basicConfig(level=logging.DEBUG)


@command_component(
    display_name="Train Stock Prediction PyTorch",
    description="train stock prediction with pytorch",
    code=SOURCE_DIR,
    environment=ENV_NAME,
    resources=ResourceConfiguration(cpu=1, memory_in_gb=1, instance_type="STANDARD_D1_V2", instance_count=1)
)
def pytorch_train_component(
        input_data: Input(type=_.URI_FOLDER, mode=IOMode.RO_MOUNT),
        epochs: Input(type="integer", default=100),
        batch_size: Input(type="integer", default=64),
        shuffle: Input(type="boolean", default=True),
        learning_rate: Input(type="number", default=0.01),
        output_model: Output(type=_.URI_FOLDER),
):
    # avoid dependency issue, execution logic is in train() func in train.py file
    from stockpredict.train.main import run_train

    run_train(input_data, batch_size, shuffle, learning_rate, epochs, output_model)


@command_component(
    display_name="Register Stock Prediction PyTorch",
    description="register stock prediction with pytorch",
    resources=ResourceConfiguration(cpu=1, memory_in_gb=1, instance_type="STANDARD_D1_V2", instance_count=1),
    code=SOURCE_DIR,
)
def register_model_component(
        input_model: Input(type=_.URI_FOLDER, mode=IOMode.RO_MOUNT),
        model_name: Input(type="string", default="stock_prediction_pytorch"),
        subscription_id: Input(type="string"),
        resource_group: Input(type="string"),
        workspace_name: Input(type="string"),
        client_id: Input(type="string"),
        output_metadata: Output(type=_.URI_FOLDER, mode=IOMode.RW_MOUNT)
):
    ml_client = MLClient(credential=ManagedIdentityCredential(client_id=client_id),
                         subscription_id=subscription_id,
                         resource_group_name=resource_group,
                         workspace_name=workspace_name)

    model_uri = os.path.join(input_model, MODEL_NAME)
    model = Model(
        name=model_name,
        type="custom_model",
        path=model_uri,
        description="Stock prediction with pytorch model"
    )
    registered_model = ml_client.models.create_or_update(model)

    info = {
        "name": model.name,
        "version": model.version
    }

    with open(os.path.join(output_metadata, OUTPUT_MODEL_METADA_FILE), "w", encoding="utf-8") as f:
        f.write(json.dumps(info))


@command_component(
    display_name="Deploy Stock Prediction PyTorch",
    description="deploy stock prediction with pytorch",
    resources=ResourceConfiguration(cpu=2, memory_in_gb=1, instance_type="STANDARD_D1_V2", instance_count=1),
    code=SOURCE_DIR,
)
def deploy_model_component(
        input_model: Input(type=_.URI_FOLDER),
        subscription_id: Input(type="string"),
        resource_group: Input(type="string"),
        workspace_name: Input(type="string"),
        client_id: Input(type="string"),
        endpoint_name: Input(type="string", default="stock-endpt"),
        keyvault_name: Input(type="string", default="keyvault-name"),
        api_secret_name: Input(type="string", default="apikey"),
        deployment_name: Input(type="string", default="alpha")
):
    ml_client = MLClient(credential=ManagedIdentityCredential(client_id=client_id),
                         subscription_id=subscription_id,
                         resource_group_name=resource_group,
                         workspace_name=workspace_name)

    with open(os.path.join(input_model, OUTPUT_MODEL_METADA_FILE), "r", encoding="utf-8") as f:
        model_info = json.loads(f.read())

    model = ml_client.models.get(name=model_info["name"], version=model_info["version"])

    endpoint = ManagedOnlineEndpoint(
        name=endpoint_name,
        description="PyTorch Endpoint",
        auth_mode="key",
    )

    created_endpoint = ml_client.online_endpoints.begin_create_or_update(endpoint)

    created_endpoint.wait(timeout=300)

    deployment = ManagedOnlineDeployment(
        endpoint_name=endpoint_name,
        name=deployment_name,
        model=model,
        environment=ENV_NAME,
        code_configuration=CodeConfiguration(
            code=SOURCE_DIR, scoring_script="stockpredict/inference/stock.py"
        ),
        instance_type="Standard_E4s_v3",
        instance_count=1,
        environment_variables={
            "AZURE_CLIENT_ID": client_id,
            "AZURE_SUBSCRIPTION_ID": subscription_id,
            "AZURE_RESOURCE_GROUP": resource_group,
            "AZURE_WORKSPACE_NAME": workspace_name,
            "AZURE_KEYVAULT_NAME": keyvault_name,
            "AZURE_API_SECRET_NAME": api_secret_name,
        }
    )

    ml_client.online_deployments.begin_create_or_update(deployment)
