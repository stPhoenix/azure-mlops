import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).parent.parent.parent.as_posix()
sys.path.append(SOURCE_DIR)

from typing import List

from stockpredict.settings import AZURE_KEYVAULT_NAME, AZURE_API_SECRET_NAME

from stockpredict.util.helpers import get_api_key, async_resolver
from stockpredict.fetcher.api_client import FMPApi
from stockpredict.fetcher.core import Fetcher
from pyspark.sql import SparkSession


def execute(api_key: str, markers: List[str], input_path: str, spark: SparkSession) -> None:
    api_client = FMPApi(api_key)
    fetcher = Fetcher(markers, input_path, api_client, spark)
    task = fetcher.fetch_and_save()
    async_resolver(task)


def entrypoint(input_path: str, markers: str, az_kv_name: str = None, az_api_sname: str = None,
               _spark: SparkSession = None) -> None:
    az_kv_name = az_kv_name if az_kv_name else AZURE_KEYVAULT_NAME
    az_api_sname = az_api_sname if az_api_sname else AZURE_API_SECRET_NAME

    _api_key = get_api_key(az_kv_name, az_api_sname, _spark)
    markers = markers.split(',')
    execute(_api_key, markers, input_path, _spark)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str)
    parser.add_argument("--markers", type=str)
    parser.add_argument("--az_kv_name", type=str, default=None)
    parser.add_argument("--az_api_sname", type=str, default=None)

    args = parser.parse_args()
    print(args)

    spark = SparkSession.builder.getOrCreate()

    entrypoint(args.input_path, args.markers, args.az_kv_name, args.az_api_sname, spark)
