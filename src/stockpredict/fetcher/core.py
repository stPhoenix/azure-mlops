import asyncio
import logging
import os.path
from abc import ABC, abstractmethod
from typing import List

import pandas as pd
from stockpredict.fetcher.api_client import AbstractApi
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.utils import AnalysisException

from stockpredict.settings import BALANCE_SHEET_PATH, CASH_FLOW_PATH, INCOME_STATEMENT_PATH, STOCK_PATH, DataColumns


class AbstractFetcher(ABC):
    def __init__(self, markers: List[str], save_path: str, api_client: AbstractApi, spark: SparkSession,
                 **kwargs):
        self.markers = markers
        self.api_client = api_client
        self.save_path = save_path
        self.spark = spark

    @abstractmethod
    async def fetch_and_save(self) -> bool:
        pass

    @abstractmethod
    async def save(self, df: DataFrame, table_name: str) -> bool:
        pass


class Fetcher(AbstractFetcher):
    def flat_list(self, l: List) -> List[dict]:
        return [item for sublist in l for item in sublist]

    async def fetch_and_save(self) -> bool:
        async with self.api_client:
            balance = await asyncio.gather(*[self.api_client.get_balance_sheet(item) for item in self.markers])
            cash = await asyncio.gather(*[self.api_client.get_cash_flow(item) for item in self.markers])
            stock = await asyncio.gather(*[self.api_client.get_historical_price(item) for item in self.markers])
            income = await asyncio.gather(*[self.api_client.get_income_statement(item) for item in self.markers])

        stock_data = []
        for item in stock:
            data = item["historical"]
            for stock in data:
                stock[DataColumns.symbol] = item[DataColumns.symbol]
            stock_data.extend(data)

        balance_sheet_df = self.spark.createDataFrame(self.flat_list(balance))
        cash_flow_df = self.spark.createDataFrame(self.flat_list(cash))

        stock_df = pd.DataFrame.from_dict(stock_data)  # need this to overcome type merge errors
        stock_df.iteritems = stock_df.items  # this is to fix error converting to spark data frame
        stock_df = self.spark.createDataFrame(stock_df)

        income_df = pd.DataFrame.from_dict(self.flat_list(income))
        income_df.iteritems = income_df.items
        income_df = self.spark.createDataFrame(income_df)

        saved = await asyncio.gather(
            self.save(balance_sheet_df, BALANCE_SHEET_PATH),
            self.save(cash_flow_df, CASH_FLOW_PATH),
            self.save(stock_df, STOCK_PATH),
            self.save(income_df, INCOME_STATEMENT_PATH)
        )

        return all(saved)

    async def save(self, df: DataFrame, table_name: str) -> bool:
        logging.info(f"saving {table_name}")

        table_path = os.path.join(self.save_path, table_name)
        try:
            old_table = self.spark.read.format("delta").load(path=table_path)
            old_table.createOrReplaceTempView(table_name)
            merged_table = df.union(old_table).drop_duplicates()
        except AnalysisException:
            old_table = None
            merged_table = df

        merged_table.write.format("delta").save(path=table_path, mode="overwrite", vacuum=True)
        return True
