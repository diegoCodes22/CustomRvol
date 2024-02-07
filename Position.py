from ibapi.contract import Contract
from VolumeFrame import VolumeFrame
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Position(Base):
    """
    This class is used to store trade data in a database.
    """
    __tablename__ = "trade_log"

    Tid = Column("tid", Integer, primary_key=True, autoincrement=True)
    Symbol = Column("Symbol", String)
    SecType = Column("SecType", String)
    TradeDate = Column("TradeDate", String)
    TradeSize = Column("TradeSize", Float)
    Direction = Column("Direction", Integer)
    RiskReward = Column("RiskReward", Float)
    Entry = Column("Entry", Float)
    EntryTime = Column("EntryTime", String)
    Exit = Column("Exit", Float)
    ExitTime = Column("ExitTime", String)
    Commission = Column("Commission", Float)
    Pnl = Column("Pnl", Float)
    PnlPerc = Column("PnlPerc", Float)
    TimeInTrade = Column("TimeInTrade", String)
    U_Chg = Column("U_Chg", Float)

    def __init__(self, vf: VolumeFrame):
        """
        :param vf: VolumeFrame, used to retrieve symbol, multiplier, and OHLCV and atr data.
        """
        self.symbol: str = vf.symbol
        self.sec_type: str = "OPT"
        self.multiplier: int = vf.multiplier
        self.trade_date: str = ""

        self.entry_time = None
        self.exit_time = None
        self.entry: float = 0.
        self.exit: float = 0.
        self.direction: int = 0

        self.take_profit: float = 0.
        self.stop_loss: float = 0.
        self.risk_reward: float = 0.
        self.commission: float = 0.
        self.pnl: float = 0.
        self.pnl_perc: float = 0.
        self.u_chg: float = 0.
        self.time_in_trade = None

        self.trade_size: float = 0.

        # --
        self.open = vf.vol_df['open'].iloc[-1]
        self.high = vf.vol_df['high'].iloc[-1]
        self.low = vf.vol_df['low'].iloc[-1]
        self.close = vf.vol_df['close'].iloc[-1]
        self.volume = vf.vol_df['volume'].iloc[1]
        self.atr = vf.vol_df['atr'].iloc[-1]

        self.in_position: bool = False
        self.underlying_entry_price: float = 0.
        self.underlying_exit_price: float = 0.

        self.opt_contract: Contract = Contract()
        self.expiration: str = ""
        self.strike: int = 0

    def define_columns(self):
        self.trade_size = round(self.entry * self.multiplier * 100, 1)
        self.u_chg = round(
            (abs(self.underlying_entry_price - self.underlying_exit_price) / self.underlying_entry_price) * 100, 1)

        self.time_in_trade = round((self.exit_time - self.entry_time).total_seconds(), 2)
        self.entry_time = self.entry_time.strftime("%H:%M:%S")
        self.exit_time = self.exit_time.strftime("%H:%M:%S")

        self.pnl = round(((self.exit - self.entry) * 100) - self.commission, 1)
        self.pnl_perc = round(self.pnl / self.entry, 1)

        self.Symbol = self.symbol
        self.SecType = self.sec_type
        self.TradeDate = self.trade_date
        self.TradeSize = self.trade_size
        self.Direction = self.direction
        self.RiskReward = self.risk_reward
        self.Entry = round(self.entry, 2)
        self.EntryTime = self.entry_time
        self.Exit = round(self.exit, 2)
        self.ExitTime = self.exit_time
        self.Commission = self.commission
        self.Pnl = self.pnl
        self.PnlPerc = self.pnl_perc
        self.TimeInTrade = self.time_in_trade
        self.U_Chg = self.u_chg

    def calculate_bracket(self):
        if self.direction == 1:
            self.take_profit = round(self.underlying_entry_price + self.atr, 2)
            self.stop_loss = self.low
        elif self.direction == -1:
            self.take_profit = round(self.underlying_entry_price - self.atr, 2)
            self.stop_loss = self.high
        self.risk_reward = round(abs(self.take_profit - self.underlying_entry_price) /
                                 abs(self.stop_loss - self.underlying_entry_price), 2)

    def __repr__(self):
        return f"{self.symbol}, {self.sec_type}, {self.trade_date}\n" \
               f"size: {self.trade_size}, RR: {self.risk_reward}, direction: {self.direction}\n" \
               f"pnl: {self.pnl}, pnl%: {self.pnl_perc}, time in trade: {self.time_in_trade}\n" \
               f"entry: {self.entry}, entry time: {self.entry_time}, exit: {self.exit}, exit time: {self.exit_time}\n" \
               f"commission: {self.commission}, underlying change: {self.u_chg}"

    def __eq__(self, other):
        if isinstance(other, Position):
            return self.symbol == other.symbol and self.sec_type == other.sec_type and self.trade_date == other.trade_date and \
                self.trade_size == other.trade_size and self.direction == other.direction and self.risk_reward == other.risk_reward and \
                self.entry == other.entry and self.entry_time == other.entry_time and self.exit == other.exit and self.exit_time == other.exit_time and \
                self.commission == other.commission and self.pnl == other.pnl and self.pnl_perc == other.pnl_perc and self.time_in_trade == other.time_in_trade and \
                self.u_chg == other.u_chg
        return False
