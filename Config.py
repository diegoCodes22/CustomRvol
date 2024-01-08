from typing import List
from TWSIBAPI_MODULES.Contracts import stock


class Config:
    def __init__(self, CONN_VARS: List[str] = None, symbol: str = None, period: str = "6 M", end_date: str = "",
                 **kwargs):
        if CONN_VARS is None:
            self.CONN_VARS = ["127.0.0.1", 7497, 0]
        if symbol is None:
            print("No symbol was provided")
            exit(-1)
        self.symbol = symbol.upper()
        try:
            self.contract = stock(symbol)
        except Exception:  # This exception should not be handled like this, instead it should be handled by the
            # TWSIBAPI_MODULES package
            print("Error retrieving symbol contract")
            exit(-1)
        valid_periods = ['S', 'D', 'W', 'M', 'Y']
        if period.split(" ")[1] not in valid_periods:
            print(f"Invalid period suffix, options are {valid_periods}")
            exit(-1)
        self.period = period
        self.end_date = end_date  # Check end_date format
        try:
            self.bar_size = kwargs["bar_size"]
        except KeyError:
            self.bar_size = "30 mins"
