from ibapi.contract import Contract
from VolumeFrame import VolumeFrame
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

def init_engine():
    engine = create_engine("sqlite://")


class Position(Base):
    __tablename__ = "TradeLog"

    tid = Column("tid", Integer, primary_key=True)
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
        self.symbol: str = vf.symbol
        self.sec_type: str = vf.sec_type
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
        self.Symbol = self.symbol
        self.SecType = self.sec_type
        self.TradeDate = self.trade_date
        self.TradeSize = self.entry * self.multiplier * 100
        self.Direction = self.direction
        self.RiskReward = self.risk_reward
        self.Entry = self.entry
        self.EntryTime = self.entry_time.strftime("%H:%M:%S")
        self.Exit = self.exit
        self.ExitTime = self.exit_time.strftime("%H:%M:%S")
        self.Commission = self.commission
        self.Pnl = self.pnl
        self.PnlPerc = self.pnl_perc
        self.TimeInTrade = self.time_in_trade.total_seconds() / 60
        self.U_Chg = abs(self.underlying_exit_price - self.underlying_entry_price)

    def calculate_bracket(self):
        if self.direction == 1:
            self.take_profit = round(self.underlying_entry_price + self.atr, 2)
            self.stop_loss = self.low
        elif self.direction == -1:
            self.take_profit = round(self.underlying_entry_price - self.atr, 2)
            self.stop_loss = self.high
        self.risk_reward = abs(self.take_profit - self.underlying_entry_price) / abs(self.stop_loss - self.underlying_entry_price)

    def calculate_pnl(self):
        self.pnl = round(((self.exit - self.entry) * 100) - self.commission, 1)
        self.pnl_perc = round(self.pnl / self.entry, 1)
        print(f"{self.symbol} move from {self.underlying_entry_price} -> {self.underlying_exit_price}\n"
              f"trade direction {self.direction} yielded a profit or loss of {self.pnl}$ or {self.pnl_perc}%")
        self.u_chg = (abs(self.underlying_entry_price - self.underlying_exit_price) / self.underlying_entry_price) * 100
        self.time_in_trade = self.exit_time - self.entry_time
