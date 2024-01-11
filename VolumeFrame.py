from TWSIBAPI_MODULES.Dataframes import ohlcv_dataframe
from TWSIBAPI_MODULES.DataStreams import reqHistoricalDataStream
from Config import Config
from ta.volatility import AverageTrueRange
from Position import Position


class VolumeFrame(Config, Position):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vol_df = ohlcv_dataframe(reqHistoricalDataStream(self.CONN_VARS, self.contract, self.period, self.bar_size,
                                                              self.end_date))
        morning_filter = self.vol_df['date'].str.contains(r".\s09:30:00", regex=True)
        self.purged = self.vol_df.loc[morning_filter]
        self.avg_vol = int(self.purged['volume'].mean())

        self.vol_df['atr'] = AverageTrueRange(self.vol_df['high'], self.vol_df['low'],
                                              self.vol_df['close']).average_true_range()

        self.eb_low = self.purged['low'].iloc[-1]
        self.eb_high = self.purged['high'].iloc[-1]
        self.close = self.purged['close'].iloc[-1]
        self.open = self.purged['open'].iloc[-1]
        self.volume = self.purged['volume'].iloc[1]
        self.atr = self.purged['atr'].iloc[-1]
