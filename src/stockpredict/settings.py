import os


class DataColumns:
    fillingDate = "fillingDate"
    acceptedDate = "acceptedDate"
    period = "period"
    link = "link"
    finalLink = "finalLink"
    reportedCurrency = "reportedCurrency"
    date = "date"
    open = "open"
    change = "change"
    high = "high"
    low = "low"
    adjClose = "adjClose"
    changePercent = "changePercent"
    label = "label"
    changeOverTime = "changeOverTime"
    volume = "volume"
    unadjustedVolume = "unadjustedVolume"
    vwap = "vwap"
    inventory = "inventory"
    depreciationAndAmortization = "depreciationAndAmortization"
    netIncome = "netIncome"
    calendarYear = "calendarYear"
    cik = "cik"
    symbol = "symbol"
    close = "close"


BALANCE_CASH_INCOME_DROP = [
    DataColumns.fillingDate,
    DataColumns.acceptedDate,
    DataColumns.period,
    DataColumns.link,
    DataColumns.finalLink,
    DataColumns.reportedCurrency,
    DataColumns.date
]
STOCK_DROP = [
    DataColumns.open,
    DataColumns.change,
    DataColumns.high,
    DataColumns.low,
    DataColumns.adjClose,
    DataColumns.changePercent,
    DataColumns.label,
    DataColumns.changeOverTime,
    DataColumns.volume,
    DataColumns.unadjustedVolume,
    DataColumns.vwap
]
CASH_ADDITIONAL_DROP = [DataColumns.inventory, DataColumns.depreciationAndAmortization, DataColumns.netIncome]
BALANCE_CASH_INCOME_JOIN_KEYS = [DataColumns.calendarYear, DataColumns.cik, DataColumns.symbol]

NETWORK_OUT_LABELS = [DataColumns.close]

BALANCE_SHEET_PATH = "balance_sheet"
CASH_FLOW_PATH = "cash_flow"
STOCK_PATH = "stock"
INCOME_STATEMENT_PATH = "income"

AZURE_KEYVAULT_NAME = os.getenv("AZURE_KEYVAULT_NAME")
AZURE_API_SECRET_NAME = os.getenv("AZURE_API_SECRET_NAME")
AZUREML_MODEL_DIR = os.getenv("AZUREML_MODEL_DIR")

MODEL_NAME = os.getenv("MODEL_NAME", "checkpoint.ckpt")
INFERENCE_DROP = [DataColumns.calendarYear, DataColumns.symbol]

DTYPE = os.getenv("DTYPE", "float64")

try:
    import torch

    TORCH_DTYPE = getattr(torch, DTYPE)
except ImportError:
    TORCH_DTYPE = DTYPE

OUTPUT_MODEL_METADA_FILE = "model_metadata.json"
