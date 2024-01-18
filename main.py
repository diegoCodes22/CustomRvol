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
from time import sleep, perf_counter
from pytz import timezone


# Check speed of relevant functions
# Decide exactly what time the program should run
# Add current pnl $  % on LiveData (if it doesn't affect speed)(I can also calculate that)
# Log commissions
# Keep track of all data in a database

# Cancel order after duration of time or price movement   ! Complex ! Important !
# Maybe remove in_position attribute, it is not used
# Check for open positions in portfolio in case of error


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
                cps = perf_counter()
                lmt_price = reqCurrentPrice(frame.CONN_VARS, frame.opt_contract)
                print(f"Request current price time: {perf_counter() - cps}")
            except NoSecDef:
                delta += 1
                if delta > 7:
                    print("Could not find short term contract.")
                    raise NoSecDef
                continue
            order = make_order(lmt_price, "BUY")
            order.algoStrategy = 'Adaptive'
            order.algoParams = [TagValue('adaptivePriority', 'Normal')]
            frame.entry = place_order(frame.CONN_VARS, frame.opt_contract, order)
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
    frame.exit = place_order(frame.CONN_VARS, frame.opt_contract, order)
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

        # --------------------- PSEUDO TESTING ONLY ------------------------
        self.frame.take_profit = round(self.frame.underlying_entry_price - 0.03, 2)
        self.frame.stop_loss = round(self.frame.underlying_entry_price + 0.03, 2)
        # ------------------------------------------------------------------

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
    vfs = perf_counter()
    vf = VolumeFrame(symbol="SPY")
    print(f"VF time: {perf_counter() - vfs}")

    eas = perf_counter()
    entry_algorithm(vf)
    print(f"Entry algo time: {perf_counter() - eas}")

    if vf.in_position is False:
        print("No trade was taken, Exiting...")
        exit(0)

    bs = perf_counter()
    vf.calculate_bracket()
    print(f"Bracket time: {perf_counter() - bs}")

    lv = LiveData(vf)
    lv.connect(vf.CONN_VARS[0], vf.CONN_VARS[1], vf.CONN_VARS[2])
    lv.run()
    exit_algorithm(vf)
    vf.calculate_pnl()
