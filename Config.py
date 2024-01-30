from typing import List
from TWSIBAPI_MODULES.Contracts import stock


class NoSym(Exception):
    def __init__(self):
        self.exit_code = -2
        print("No symbol was provided")
        exit(self.exit_code)


class InvalidPeriod(Exception):
    def __init__(self, valid_periods: List[str]):
        self.exit_code = -3
        print(f"Invalid period suffix, options are {valid_periods}")
        exit(self.exit_code)


class Config:
    def __init__(self, CONN_VARS: List[str] = None, symbol: str = None, duration: str = "2 M", end_date: str = "",
                 bar_size: str = "30 mins", multiplier: int = 1, database_path: str = "TradeLog.sqlite"):
        if CONN_VARS is None:
            self.CONN_VARS = ["127.0.0.1", 7497, 0]
        else:
            self.CONN_VARS = CONN_VARS
        if symbol is None:
            raise NoSym
        self.symbol = symbol.upper()
        self.contract = stock(symbol)
        self.sec_type = self.contract.secType
        self.multiplier = multiplier
        valid_periods = ['S', 'D', 'W', 'M', 'Y']
        if duration.split(" ")[1] not in valid_periods:
            raise InvalidPeriod(valid_periods)
        self.duration = duration
        self.end_date = end_date  # Check end_date format
        self.bar_size = bar_size
        self.db_path = database_path
