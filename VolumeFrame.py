from TWSIBAPI_MODULES.Dataframes import ohlcv_dataframe
from TWSIBAPI_MODULES.DataStreams import reqHistoricalDataStream
from TWSIBAPI_MODULES import NoSecDef
from Config import Config
from pandas_ta.volatility import atr

# from ta.volatility import AverageTrueRange  Uninstall--


class VolumeFrame(Config):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            hds = reqHistoricalDataStream(self.CONN_VARS, self.contract, self.duration, self.bar_size, self.end_date)
        except NoSecDef:
            exit(-1)
        if len(hds) == 0:
            print("Could not retrieve historical data.")  # Historical data exception
            print(f"{self.CONN_VARS}---{self.contract}--duration: {self.duration}--bar size: {self.bar_size}--end date: {self.end_date}\nExiting...")
            exit(-1)
        self.vol_df = ohlcv_dataframe(hds)
        self.vol_df = self.vol_df.dropna()

        self.vol_df['atr'] = atr(self.vol_df['high'], self.vol_df['low'], self.vol_df['close'], 14)

        self.avg_vol = round(self.vol_df['volume'].iloc[-30:].mean())
