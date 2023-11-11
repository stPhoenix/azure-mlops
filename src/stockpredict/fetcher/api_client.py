import asyncio
import logging
from abc import ABC, abstractmethod

from aiohttp import ClientSession


class AbstractApi(ABC):
    MAX_RETRY = 3
    WAIT_TIME = 61

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.__aexit__(exc_type, exc_val, exc_tb)
        return await self.session.close()

    async def make_call(self, method: str, url: str, request: str = None, params: dict = None, retry_num: int = 1):
        async with self.session.request(method=method, url=url, json=request, params=params) as response:
            if response.status < 300:
                return await response.json()
            elif retry_num <= self.MAX_RETRY:
                logging.info(
                    f"Calling {url} got code: {response.status}. Will make retry in {self.WAIT_TIME} sec"
                )
                await asyncio.sleep(self.WAIT_TIME)
                return await self.make_call(method, url, request, params, retry_num + 1)
            else:
                error = await response.text(encoding="utf-8")
                logging.error(f"Received error from api server: {error}")
                raise ValueError(error)

    @abstractmethod
    async def get_balance_sheet(self, marker: str, period: str = "annual", limit: int = 0) -> dict:
        pass

    @abstractmethod
    async def get_cash_flow(self, marker: str, period: str = "annual", limit: int = 0) -> dict:
        pass

    @abstractmethod
    async def get_historical_price(self, marker: str, period: str = "annual", limit: int = 0) -> dict:
        pass

    @abstractmethod
    async def get_income_statement(self, marker: str, period: str = "annual", limit: int = 0) -> dict:
        pass


class FMPApi(AbstractApi):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.session = ClientSession(base_url="https://financialmodelingprep.com")
        self.auth = {"apikey": api_key}

    def get_params(self, period: str = "annual", limit: int = 0) -> dict:
        params = self.auth.copy()
        if period != "annual":
            params["period"] = period
        if limit != 0:
            params["limit"] = limit
        return params

    async def get_balance_sheet(self, marker: str, period: str = "annual", limit: int = 0) -> dict:
        url = f"/api/v3/balance-sheet-statement/{marker}"
        return await self.make_call("GET", url, params=self.get_params(period, limit))

    async def get_cash_flow(self, marker: str, period: str = "annual", limit: int = 0) -> dict:
        url = f"/api/v3/cash-flow-statement/{marker}"
        return await self.make_call("GET", url, params=self.get_params(period, limit))

    async def get_historical_price(self, marker: str, period: str = "annual", limit: int = 0) -> dict:
        url = f"/api/v3/historical-price-full/{marker}"
        params = self.get_params(period, limit)
        params["serietype"] = "bar"

        return await self.make_call("GET", url, params=params)

    async def get_income_statement(self, marker: str, period: str = "annual", limit: int = 0) -> dict:
        url = f"/api/v3/income-statement/{marker}"
        return await self.make_call("GET", url, params=self.auth)
