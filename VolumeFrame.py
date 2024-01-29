from TWSIBAPI_MODULES.Dataframes import ohlcv_dataframe
from TWSIBAPI_MODULES.DataStreams import reqHistoricalDataStream
from TWSIBAPI_MODULES import NoSecDef
from Config import Config
from ta.volatility import AverageTrueRange
from Position import Position


class VolumeFrame(Config, Position):
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

        # Deprecate purged, trades can be taken at any time
        morning_filter = self.vol_df['date'].str.contains(r".\s09:30:00", regex=True)
        self.purged = self.vol_df.loc[morning_filter]

        self.avg_vol = round(self.purged['volume'].mean())

        self.vol_df['atr'] = AverageTrueRange(self.vol_df['high'], self.vol_df['low'],
                                              self.vol_df['close']).average_true_range()  # Maybe I can calculate this
        # myself for optimization purposes. Use numpy to calculate that.

        # Deprecate
        self.eb_low = self.purged['low'].iloc[-1]
        self.eb_high = self.purged['high'].iloc[-1]
        self.close = self.purged['close'].iloc[-1]
        self.open = self.purged['open'].iloc[-1]
        self.volume = self.purged['volume'].iloc[1]
        self.atr = self.vol_df['atr'].iloc[-1]

    def calculate_bracket(self):
        if self.direction == 1:
            self.take_profit = round(self.underlying_entry_price + self.atr, 2)
            self.stop_loss = self.eb_low
        elif self.direction == -1:
            self.take_profit = round(self.underlying_entry_price - self.atr, 2)
            self.stop_loss = self.eb_high

    def calculate_pnl(self):
        self.pnl = round(((self.exit - self.entry) * 100) - self.commission, 1)
        self.pnl_perc = round(self.pnl / self.entry, 1)
        print(f"{self.symbol} move from {self.underlying_entry_price} -> {self.underlying_exit_price}\n"
              f"trade direction {self.direction} yielded a profit or loss of {self.pnl}$ or {self.pnl_perc}%")
