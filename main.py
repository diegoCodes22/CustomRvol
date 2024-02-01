from ibapi.common import TickerId, TickAttrib
from ibapi.tag_value import TagValue
from ibapi.ticktype import TickType
from ibapi.order import Order
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from TWSIBAPI_MODULES.Contracts import option
from TWSIBAPI_MODULES.DataStreams import reqCurrentPrice
from TWSIBAPI_MODULES.Orders import place_order
from TWSIBAPI_MODULES import NoSecDef, ConnError

from VolumeFrame import VolumeFrame
from Position import Position

from datetime import datetime, timedelta
from time import sleep
from pytz import timezone


# Test database

# Sectype error, since I always pass a stock ticker, sectype is always stk

# Must calculate the amount of bars passed, and I must update after every bar.
# 0.4243 to reqHistData for 2 bars

# Cancel order after duration of time or price movement   ! Complex ! Important !
# I will need to start a new thread, to monitor price and time

# Some functions should be slightly different depending on the security traded, like order, or the entry algo

# Make it so you can use a trailing stop.

# 2.38s on avg until entry
# Creating frame and running entry algo

def make_order(lmt_price: float, act: str, size: int) -> Order:
    order = Order()
    order.orderId = 0
    order.action = act
    order.totalQuantity = size
    order.orderType = "LMT"
    order.lmtPrice = lmt_price
    order.eTradeOnly = ''
    order.firmQuoteOnly = ''
    return order


def entry_algorithm(frame: VolumeFrame) -> Position:
    pos = Position(frame)
    pos.trade_date = datetime.now(timezone("US/Eastern")).strftime("%Y%m%d")
    delta: int = 1
    diff: float = pos.close - pos.open
    pos.direction = 1 if diff > 0 else -1
    # if pos.volume > frame.avg_vol and abs(diff) > pos.atr and not pos.in_position:
    # ---PSEUDO TESTING ONLY-------|
    if pos.direction != 0:  # .    |
        # -------------------------|
        strike_calc = pos.atr + pos.atr / 4
        pos.strike = round(pos.close + strike_calc) if pos.direction == 1 else round(pos.close - strike_calc)
        while True:
            pos.expiration = (datetime.strptime(pos.trade_date, "%Y%m%d") + timedelta(days=delta)).strftime("%Y%m%d")
            pos.opt_contract = option(pos.symbol, pos.expiration, pos.strike, 'C' if pos.direction > 0 else 'P')
            try:
                lmt_price = reqCurrentPrice(frame.CONN_VARS, pos.opt_contract)
            except NoSecDef:
                delta += 1
                if delta > 7:
                    print("Could not find short term contract.")
                    raise
                continue
            order = make_order(lmt_price, "BUY", frame.multiplier)
            order.algoStrategy = 'Adaptive'
            order.algoParams = [TagValue('adaptivePriority', 'Normal')]
            order_details = place_order(frame.CONN_VARS, pos.opt_contract, order)
            pos.entry = order_details[0]
            pos.commission += order_details[1]
            break
        pos.entry_time = datetime.now(timezone("US/Eastern"))
        pos.underlying_entry_price = reqCurrentPrice(frame.CONN_VARS, frame.contract)
        pos.in_position = True
    else:
        pos.in_position = False
    return pos


def exit_algorithm(frame: VolumeFrame, pos: Position):
    lmt_price = reqCurrentPrice(frame.CONN_VARS, pos.opt_contract)
    order = make_order(lmt_price, "SELL", frame.multiplier)
    order.algoStrategy = 'Adaptive'
    order.algoParams = [TagValue("adaptivePriority", 'Urgent')]
    order_details = place_order(frame.CONN_VARS, pos.opt_contract, order)
    pos.exit = order_details[0]
    pos.exit_time = datetime.now(timezone("US/Eastern"))
    pos.commission += order_details[1]
    pos.in_position = False


class LiveData(EClient, EWrapper):
    def __init__(self, frame: VolumeFrame, pos: Position):
        EClient.__init__(self, self)
        self.frame = frame
        self.pos = pos

    def nextValidId(self, orderId: int):
        self.reqMarketDataType(2)
        self.reqMktData(orderId, self.frame.contract, "", False, False, [])

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        ct = datetime.now(timezone("US/Eastern")).strftime("%H:%M")

        # --------------------- PSEUDO TESTING ONLY -----------------------------------|
        self.pos.take_profit = round(self.pos.underlying_entry_price - 0.03, 2)  # |
        self.pos.stop_loss = round(self.pos.underlying_entry_price + 0.03, 2)  # |
        # -----------------------------------------------------------------------------|

        if price == self.pos.take_profit or price == self.pos.stop_loss or ct == "15:30":
            self.pos.underlying_exit_price = price
            self.disconnect()
        else:
            print(f"{price}  ----  tp {self.pos.take_profit}   sl {self.pos.stop_loss}")
            sleep(1)

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        if errorCode == 502:
            raise ConnError
        elif errorCode == 200:
            raise NoSecDef


if __name__ == "__main__":
    vf = VolumeFrame(symbol="SPY")
    position = entry_algorithm(vf)
    if position.in_position is False:
        print("No trade was taken, Exiting...")
        exit(0)
    position.calculate_bracket()
    lv = LiveData(vf, position)
    lv.connect(vf.CONN_VARS[0], vf.CONN_VARS[1], vf.CONN_VARS[2])
    lv.run()
    exit_algorithm(vf, position)

    engine = create_engine(f"sqlite:///{vf.db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(position)
    session.commit()
