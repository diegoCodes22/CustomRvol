from TWSIBAPI_MODULES.Contracts import stock
from TWSIBAPI_MODULES.Configurations import Configurations


class Config(Configurations):
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 0, symbol: str = None,
                 duration: str = "2 M", end_date: str = "", bar_size: str = "30 mins", multiplier: int = 1,
                 database_path: str = "TradeLog.sqlite"):
        super().__init__(host, port, client_id)
        self.symbol = symbol.upper()
        self.contract = stock(symbol)
        self.multiplier = multiplier

        self.check_periods(duration)
        self.duration = duration

        self.check_end_date_format(end_date)
        self.end_date = end_date

        self.bar_size = bar_size
        self.db_path = database_path
