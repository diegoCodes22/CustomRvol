from TWSIBAPI_MODULES.Dataframes import ohlcv_dataframe
from TWSIBAPI_MODULES.DataStreams import reqHistoricalDataStream
from Config import Config


class VolumeFrame:
    def __init__(self, configurations: Config):
        self.configurations = configurations
        self.vol_df = ohlcv_dataframe(reqHistoricalDataStream(configurations.CONN_VARS, configurations.contract,
                                                              configurations.period, configurations.bar_size,
                                                              configurations.end_date))
