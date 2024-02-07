from TWSIBAPI_MODULES.Contracts import stock
from TWSIBAPI_MODULES.Configurations import Configurations


class Config(Configurations):
    """
    This class is used to create a Config object, which inherits from the Configurations object. It is used to store the
    configuration settings for the trading algorithm.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 0, symbol: str = "SPY",
                 duration: str = "30 D", end_date: str = "", bar_size: str = "30 mins", multiplier: int = 1,
                 database_path: str = "TradeLog.sqlite"):
        """
        :param host: TWS or ib_gateway connection host
        :param port: TWS or ib_gateway connection port
        :param client_id: TWS or ib_gateway client id
        :param symbol: Symbol to be traded
        :param duration: Lookback period for dataframe creation (ends in end_date)
        :param end_date: Last date of the lookback period. Default is current date
        :param bar_size: Size of historical bars to be retrieved
        :param multiplier: How many contracts to be traded
        :param database_path: Path to trade log database

        :raise InvalidPeriod: Raised if the duration period is not valid
        :raise EndDateFormatError: Raised if the end_date format is not valid
        """
        super().__init__(host, port, client_id)
        self.symbol = symbol.upper()
        self.contract = stock(symbol)
        self.multiplier = multiplier
        self.duration = self.check_periods(duration)
        self.end_date = self.check_end_date_format(end_date)
        self.bar_size = self.check_bar_size_format(bar_size)
        self.db_path = database_path
