from ibapi.contract import Contract


class Position:
    def __init__(self):
        self.close: float = 0
        self.open: float = 0
        self.eb_low: float = 0
        self.eb_high: float = 0
        self.volume: int = 0
        self.atr: float = 0

        self.in_position: bool = False
        self.entry: float = 0
        self.direction: int = 0
        self.expiration: str = ""
        self.strike: int = 0

        self.take_profit: float = 0
        self.stop_loss: float = 0

        if self.direction == 1:
            self.take_profit = self.entry + self.atr
            self.stop_loss = self.eb_low
        elif self.direction == -1:
            self.take_profit = self.entry - self.atr
            self.stop_loss = self.eb_high

        self.opt_contract: Contract = Contract()
        self.pnl: float = 0
