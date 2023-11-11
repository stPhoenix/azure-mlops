import asyncio

import pandas as pd
from stockpredict.fetcher.api_client import AbstractApi

from stockpredict.settings import BALANCE_CASH_INCOME_DROP, CASH_ADDITIONAL_DROP, BALANCE_CASH_INCOME_JOIN_KEYS, \
    INFERENCE_DROP, DTYPE
from stockpredict.util.helpers import async_resolver


class DataFetcher:
    def __init__(self, client: AbstractApi):
        self.client = client

    def get_data(self, marker: str, period: str = "annual") -> pd.DataFrame:
        task = (asyncio.gather(self.client.get_balance_sheet(marker=marker, period=period, limit=1),
                               self.client.get_cash_flow(marker=marker, period=period, limit=1),
                               self.client.get_income_statement(marker=marker, period=period, limit=1)
                               ))
        balance, cash, income = async_resolver(task)
        balance_df = pd.DataFrame.from_dict(balance)
        cash_flow_df = pd.DataFrame.from_dict(cash)
        income_df = pd.DataFrame.from_dict(income)

        return self.preprocess(balance_df, cash_flow_df, income_df)

    def preprocess(self, balance_sheet: pd.DataFrame, cash_flow: pd.DataFrame, income: pd.DataFrame) -> pd.DataFrame:
        balance_sheet.drop(columns=BALANCE_CASH_INCOME_DROP, inplace=True)
        cash_flow.drop(columns=[*BALANCE_CASH_INCOME_DROP, *CASH_ADDITIONAL_DROP], inplace=True)
        income.drop(columns=BALANCE_CASH_INCOME_DROP, inplace=True)

        balance_sheet.set_index(BALANCE_CASH_INCOME_JOIN_KEYS, inplace=True)
        cash_flow.set_index(BALANCE_CASH_INCOME_JOIN_KEYS, inplace=True)
        income.set_index(BALANCE_CASH_INCOME_JOIN_KEYS, inplace=True)

        df = balance_sheet.join(cash_flow).join(income)
        df.reset_index(inplace=True)
        df.drop(columns=INFERENCE_DROP, inplace=True)
        df.fillna(value=0, inplace=True)
        df = df.astype(DTYPE)

        return df
