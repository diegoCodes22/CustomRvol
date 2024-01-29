from ibapi.contract import Contract
from VolumeFrame import VolumeFrame


class Position:
    def __init__(self, vf: VolumeFrame):
        self.symbol = vf.symbol
        self.open = vf.vol_df['open'].iloc[-1]
        self.high = vf.vol_df['high'].iloc[-1]
        self.low = vf.vol_df['low'].iloc[-1]
        self.close = vf.vol_df['close'].iloc[-1]
        self.volume = vf.vol_df['volume'].iloc[1]
        self.atr = vf.vol_df['atr'].iloc[-1]

        self.in_position: bool = False
        self.underlying_entry_price: float = 0.
        self.underlying_exit_price: float = 0.
        self.entry: float = 0.
        self.exit: float = 0.
        self.direction: int = 0
        self.expiration: str = ""
        self.strike: int = 0

        self.take_profit: float = 0.
        self.stop_loss: float = 0.

        self.opt_contract: Contract = Contract()
        self.commission: float = 0.
        self.pnl: float = 0.
        self.pnl_perc: float = 0.
        self.u_chg: float = 0.

    def calculate_bracket(self):
        if self.direction == 1:
            self.take_profit = round(self.underlying_entry_price + self.atr, 2)
            self.stop_loss = self.low
        elif self.direction == -1:
            self.take_profit = round(self.underlying_entry_price - self.atr, 2)
            self.stop_loss = self.high

    def calculate_pnl(self):
        self.pnl = round(((self.exit - self.entry) * 100) - self.commission, 1)
        self.pnl_perc = round(self.pnl / self.entry, 1)
        print(f"{self.symbol} move from {self.underlying_entry_price} -> {self.underlying_exit_price}\n"
              f"trade direction {self.direction} yielded a profit or loss of {self.pnl}$ or {self.pnl_perc}%")
