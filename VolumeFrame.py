from TWSIBAPI_MODULES.Dataframes import ohlcv_dataframe
from TWSIBAPI_MODULES.DataStreams import reqHistoricalDataStream
from Config import Config


class VolumeFrame(Config):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vol_df = ohlcv_dataframe(reqHistoricalDataStream(self.CONN_VARS, self.contract, self.period, self.bar_size,
                                                              self.end_date))
        print(self.vol_df)
        morning_filter = self.vol_df['date'].str.contains(r".\s09:30:00", regex=True)
        self.purged = self.vol_df.loc[morning_filter]
        print(self.purged)
        self.avg_vol = int(self.purged['volume'].mean())
