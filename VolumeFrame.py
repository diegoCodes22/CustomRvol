from TWSIBAPI_MODULES.Dataframes import ohlcv_dataframe
from TWSIBAPI_MODULES.DataStreams import reqHistoricalDataStream
from TWSIBAPI_MODULES.exceptions_handler import HistoricalDataError
from Config import Config
from pandas_ta.volatility import atr


class VolumeFrame(Config):
    """
    This class is used to create a VolumeFrame object, which inherits from the Config object. It retrieves historical
    data for the security and creates a dataframe.

    Attributes:
    vol_df: Dataframe containing OHLCV, atr data of the specified security, for the period of time (duration) specified
    in the constructor, ending in end_date (also specified in constructor).
    avg_vol: Average volume of the latest vol_len bars.
    """
    def __init__(self, atr_len: int = 14, vol_len: int = 30, **kwargs):
        """
        :param atr_len: Lookback length for Average True Range calculation.
        :param vol_len: Lookback period for average volume calculation.
        :param **kwargs: Keyword arguments for the Config class construction.

        :raise HistoricalDataError: Raised if no data was returned from reqHistoricalDataStream from TWSIBAPI_MODULES
        """
        super().__init__(**kwargs)
        hds = reqHistoricalDataStream(self.CONN_VARS, self.contract, self.duration, self.bar_size, self.end_date)
        if len(hds) == 0:
            raise HistoricalDataError(f"{self.CONN_VARS}, {self.contract}, {self.duration}, {self.bar_size}, "
                                      f"{self.end_date}")
        self.vol_df = ohlcv_dataframe(hds)
        self.vol_df = self.vol_df.dropna()

        self.vol_df['atr'] = atr(self.vol_df['high'], self.vol_df['low'], self.vol_df['close'], atr_len)

        self.avg_vol = round(self.vol_df['volume'].iloc[-vol_len:].mean())
