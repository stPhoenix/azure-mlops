import os
import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).parent.parent.parent.as_posix()
sys.path.append(SOURCE_DIR)

from azure.ai.ml.entities import Environment, BuildContext

ENV_NAME = "azureml:pytorch-2-cu11-7@latest"
default_environment = Environment(name="pytorch-2-cu11-7",
                                  build=BuildContext(
                                      path=os.path.join(SOURCE_DIR, "stockpredict/docker-contexts/default"),
                                      dockerfile_path="Dockerfile"))
