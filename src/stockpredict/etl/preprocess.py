import os
from typing import List

from pyspark.sql import SparkSession, DataFrame, functions as F
from pyspark.sql.types import FloatType, DoubleType

from stockpredict.settings import BALANCE_CASH_INCOME_DROP, STOCK_DROP, CASH_ADDITIONAL_DROP, \
    BALANCE_CASH_INCOME_JOIN_KEYS, BALANCE_SHEET_PATH, STOCK_PATH, INCOME_STATEMENT_PATH, CASH_FLOW_PATH, DTYPE, \
    DataColumns

spark_types = {
    "float32": FloatType(),
    "float64": DoubleType(),
}


class Preprocess:

    def __init__(self, spark: SparkSession, input_data: str):
        self.spark = spark
        self.input_data = input_data

    def execute(self) -> DataFrame:
        balance, cash, stock, income = self.get_balance_cash_stock()

        balance_cash = (balance.join(cash, BALANCE_CASH_INCOME_JOIN_KEYS)
                        .join(income, BALANCE_CASH_INCOME_JOIN_KEYS))

        balance_cash = balance_cash.withColumnRenamed(DataColumns.calendarYear, "join_date")

        stock = stock.withColumn("join_date", F.date_format(F.col(DataColumns.date), "y"))

        balance_cash = balance_cash.dropna()
        stock = stock.dropna()

        final_df = stock.join(balance_cash, ["join_date", DataColumns.symbol])
        final_df = final_df.drop("join_date", DataColumns.symbol)

        final_df = final_df.withColumn(DataColumns.date, F.unix_timestamp(DataColumns.date, "yyyy-MM-dd"))

        final_df = final_df.select([F.col(c).cast(spark_types[DTYPE]) for c in final_df.columns])

        return final_df.dropDuplicates()

    def load_table(self, table_name: str) -> DataFrame:
        return self.spark.read.format("delta").load(os.path.join(self.input_data, table_name))

    def get_balance_cash_stock(self) -> List[DataFrame]:
        balance_sheet_df = self.load_table(BALANCE_SHEET_PATH)
        balance_sheet_df = balance_sheet_df.drop(
            *BALANCE_CASH_INCOME_DROP
        )

        cash_flow_df = self.load_table(CASH_FLOW_PATH)
        cash_flow_df = cash_flow_df.drop(
            *BALANCE_CASH_INCOME_DROP,
            *CASH_ADDITIONAL_DROP
        )

        stock_df = self.load_table(STOCK_PATH)
        stock_df = stock_df.drop(*STOCK_DROP)

        income_df = self.load_table(INCOME_STATEMENT_PATH)
        income_df = income_df.drop(*BALANCE_CASH_INCOME_DROP)

        return [balance_sheet_df, cash_flow_df, stock_df, income_df]
