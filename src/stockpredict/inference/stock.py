import os.path
import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).parent.parent.parent.as_posix()
sys.path.append(SOURCE_DIR)

import os
import logging
import json
import pandas as pd

from stockpredict.model.network import StockNN
import torch
from stockpredict.settings import MODEL_NAME, DTYPE, DataColumns, AZURE_API_SECRET_NAME, AZURE_KEYVAULT_NAME, \
    AZUREML_MODEL_DIR
from stockpredict.util.helpers import get_api_key
from stockpredict.inference.data_fetcher import DataFetcher
from stockpredict.fetcher.api_client import FMPApi
from stockpredict.util.dto import InferenceRequest
import numpy as np

device = torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")


def init():
    """
    This function is called when the container is initialized/started, typically after create/update of the deployment.
    You can write the logic here to perform init operations like caching the model in memory
    """
    global model
    # AZUREML_MODEL_DIR is an environment variable created during deployment.
    # It is the path to the model folder (./azureml-models/$MODEL_NAME/$VERSION)
    # Please provide your model's folder name if there is one
    model_path = os.path.join(
        AZUREML_MODEL_DIR,
        MODEL_NAME
    )
    assert model_path, "Model path is not set"

    model = StockNN(1, 1).load_from_checkpoint(model_path)

    model.eval()
    logging.info(f"Model: {model}")
    logging.info("Model loaded")
    logging.info("Init complete")


def run(raw_data):
    """
    This function is called for every invocation of the endpoint to perform the actual scoring/prediction.
    In the example we extract the data from the json input and call the scikit-learn model's predict()
    method and return the result back
    """
    data = InferenceRequest(**json.loads(raw_data))

    api_key = get_api_key(keyvault_name=AZURE_KEYVAULT_NAME, secret_name=AZURE_API_SECRET_NAME)

    api_client = FMPApi(api_key=api_key)
    data_fetcher = DataFetcher(api_client)

    base_data = data_fetcher.get_data(data.symbol)
    time_range = pd.date_range(start=data.start_date, end=data.end_date, freq='D')
    input_df = time_range.to_frame(name=DataColumns.date).reset_index(drop=True)
    input_df[DataColumns.date] = input_df.date.values.astype(np.int64) // 10 ** 9

    input_data = input_df.join(base_data, how="cross").astype(DTYPE)
    input_data = torch.tensor(data=input_data.values, device=device)

    result = {}
    predictions = model(input_data)
    for date, data in zip(time_range.tolist(), predictions):
        result[date.strftime("%Y-%m-%d")] = data.item()

    logging.info("Request processed")
    return result
