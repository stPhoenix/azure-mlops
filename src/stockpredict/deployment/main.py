import sys
from pathlib import Path

from azure.core.exceptions import ResourceNotFoundError

SOURCE_DIR = Path(__file__).parent.parent.parent.as_posix()
sys.path.append(SOURCE_DIR)

import logging
import argparse
from azure.ai.ml import MLClient
import stockpredict.deployment.environments as custom_environments
import stockpredict.deployment.components as custom_components
import stockpredict.deployment.pipelines as custom_pipelines
from azure.identity import DefaultAzureCredential


def register_environments(ml_client: MLClient):
    for name in dir(custom_environments):
        if name.endswith("_environment"):
            e = getattr(custom_environments, name)
            try:
                environment = ml_client.environments.get(name=e.name, label="latest")
                version = int(environment.version) + 1
            except ResourceNotFoundError:
                version = 1
            e.version = str(version)
            ml_client.environments.create_or_update(e)
            logging.info(f"Registered environment {e.name}")
    logging.info("Finished registering environments")


def register_components(ml_client: MLClient):
    for name in dir(custom_components):
        if name.endswith("_component") and name != "command_component":
            c = getattr(custom_components, name)
            try:
                component = ml_client.components.get(name=name)
                version = int(component.version) + 1
            except ResourceNotFoundError:
                version = 1
            ml_client.components.create_or_update(c, str(version))
            logging.info(f"Registered component {name}")
    logging.info("Finished registering components")


def register_pipelines(ml_client: MLClient):
    for name in dir(custom_pipelines):
        if name.endswith("_pipeline"):
            p = getattr(custom_pipelines, name)
            try:
                pipeline = ml_client.components.get(name=name)
                version = int(pipeline.version) + 1
            except ResourceNotFoundError:
                version = 1
            ml_client.components.create_or_update(p, str(version))
            logging.info(f"Registered pipeline {name}")
    logging.info("Finished registering pipelines")


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--subscription_id", type=str)
    parser.add_argument("--resource_group", type=str)
    parser.add_argument("--workspace_name", type=str)

    args = parser.parse_args()
    logging.info(args)

    _ml_client = MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=args.subscription_id,
        resource_group_name=args.resource_group,
        workspace_name=args.workspace_name,
    )

    register_environments(_ml_client)
    register_components(_ml_client)
    register_pipelines(_ml_client)
    logging.info('Finished registering all components and pipelines in the Azure ML workspace. '
                 'You can now start creating your first pipeline using the CLI or the Python SDK '
                 )


if __name__ == '__main__':
    main()
