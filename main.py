from ibapi.common import TickerId, TickAttrib
from ibapi.tag_value import TagValue
from ibapi.ticktype import TickType
from ibapi.order import Order
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

from TWSIBAPI_MODULES.Contracts import option
from TWSIBAPI_MODULES.DataStreams import reqCurrentPrice
from TWSIBAPI_MODULES.Orders import place_order
from TWSIBAPI_MODULES import NoSecDef, ConnError

from VolumeFrame import VolumeFrame

from datetime import datetime, timedelta
from time import sleep
from pytz import timezone


# 2.38s on avg until entry

# Some functions should be slightly different depending on the security traded, like order, or the entry algo
# I have to keep adding live data to the dataframe, so it can continue to take trade, or after it takes the trade, and
# wants to scan for new ones, it requests historical data again, but I think that is not efficient.
# Make it so you can use a trailing stop.

# Decide exactly what time the program should run
# Log commissions
# Keep track of all data in a database

# Cancel order after duration of time or price movement   ! Complex ! Important !


def make_order(lmt_price: float, act) -> Order:
    order = Order()
    order.orderId = 0
    order.action = act
    order.totalQuantity = 1
    order.orderType = "LMT"
    order.lmtPrice = lmt_price
    order.eTradeOnly = ''
    order.firmQuoteOnly = ''
    return order


def entry_algorithm(frame: VolumeFrame) -> None:
    ct: str = datetime.now(timezone("US/Eastern")).strftime("%Y%m%d %H%M%S")
    delta: int = 1
    diff: float = frame.close - frame.open
    frame.direction = 1 if diff > 0 else -1
    # if frame.volume > frame.avg_vol and abs(diff) > frame.atr and not frame.in_position:
    # ---PSEUDO TESTING ONLY-------|
    if frame.direction != 0:  # .  |
        # -------------------------|
        strike_calc = frame.atr + frame.atr / 4
        frame.strike = round(frame.close + strike_calc) if frame.direction == 1 else round(frame.close - strike_calc)
        while True:
            frame.expiration = (datetime.strptime(ct.split(" ")[0], "%Y%m%d") + timedelta(days=delta)).strftime("%Y%m%d")
            frame.opt_contract = option(frame.symbol, frame.expiration, frame.strike, 'C' if frame.direction > 0 else 'P')
            try:
                lmt_price = reqCurrentPrice(frame.CONN_VARS, frame.opt_contract)
            except NoSecDef:
                delta += 1
                if delta > 7:
                    print("Could not find short term contract.")
                    raise
                continue
            order = make_order(lmt_price, "BUY")
            order.algoStrategy = 'Adaptive'
            order.algoParams = [TagValue('adaptivePriority', 'Normal')]
            order_details = place_order(frame.CONN_VARS, frame.opt_contract, order)
            frame.entry = order_details[0]
            frame.commission += order_details[1]
            break
        frame.underlying_entry_price = reqCurrentPrice(frame.CONN_VARS, frame.contract)
        frame.in_position = True
    else:
        frame.in_position = False


def exit_algorithm(frame: VolumeFrame):
    lmt_price = reqCurrentPrice(frame.CONN_VARS, frame.opt_contract)
    order = make_order(lmt_price, "SELL")
    order.algoStrategy = 'Adaptive'
    order.algoParams = [TagValue("adaptivePriority", 'Urgent')]
    order_details = place_order(frame.CONN_VARS, frame.opt_contract, order)
    frame.exit = order_details[0]
    frame.commission += order_details[1]
    frame.in_position = False


class LiveData(EClient, EWrapper):
    def __init__(self, frame: VolumeFrame):
        EClient.__init__(self, self)
        self.frame = frame

    def nextValidId(self, orderId: int):
        self.reqMarketDataType(2)
        self.reqMktData(orderId, self.frame.contract, "", False, False, [])

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        ct = datetime.now(timezone("US/Eastern")).strftime("%H:%M")

        # --------------------- PSEUDO TESTING ONLY -----------------------------------|
        self.frame.take_profit = round(self.frame.underlying_entry_price - 0.03, 2)  # |
        self.frame.stop_loss = round(self.frame.underlying_entry_price + 0.03, 2)    # |
        # -----------------------------------------------------------------------------|

        if price == self.frame.take_profit or price == self.frame.stop_loss or ct == "15:30":
            self.frame.underlying_exit_price = price
            self.disconnect()
        else:
            print(f"{price}  ----  tp {self.frame.take_profit}   sl {self.frame.stop_loss}")
            sleep(1)

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        if errorCode == 502:
            raise ConnError
        elif errorCode == 200:
            raise NoSecDef


if __name__ == "__main__":
    vf = VolumeFrame(symbol="SPY")
    entry_algorithm(vf)
    if vf.in_position is False:
        print("No trade was taken, Exiting...")
        exit(0)
    vf.calculate_bracket()
    lv = LiveData(vf)
    lv.connect(vf.CONN_VARS[0], vf.CONN_VARS[1], vf.CONN_VARS[2])
    lv.run()
    exit_algorithm(vf)
    vf.calculate_pnl()
