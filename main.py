from ibapi.common import TickerId, TickAttrib
from ibapi.ticktype import TickType
from ibapi.order import Order
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

from TWSIBAPI_MODULES.Contracts import option
from TWSIBAPI_MODULES.DataStreams import reqCurrentPrice
from TWSIBAPI_MODULES.Orders import place_order, NoSecDef

from VolumeFrame import VolumeFrame

from datetime import datetime, timedelta
from time import sleep
from pytz import timezone


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
    # if frame.volume > frame.avg_vol and abs(diff) > frame.atr * 1.2 and not frame.in_position:
    # Check if last row in dataframe is today
    if frame.direction != 0:  # TESTING ONLY
        strike_calc = frame.atr + frame.atr / 4
        frame.strike = round(frame.close + strike_calc) if frame.direction == 1 else round(frame.close - strike_calc)
        while True:
            frame.expiration = (datetime.strptime(ct.split(" ")[0], "%Y%m%d") + timedelta(days=delta)).strftime("%Y%m%d")
            frame.opt_contract = option(frame.symbol, frame.expiration, frame.strike, 'C' if frame.direction > 0 else 'P')
            try:
                lmt_price = reqCurrentPrice(frame.CONN_VARS, frame.opt_contract)
            except NoSecDef:
                delta += 1
                if delta > 10:
                    print("Could not find short term contract. Exiting...")
                    exit(-1)
                continue
            order = make_order(lmt_price, "BUY")
            frame.entry = place_order(frame.CONN_VARS, frame.opt_contract, order)
            break
        frame.underlying_entry_price = reqCurrentPrice(frame.CONN_VARS, frame.contract)
        frame.in_position = True
    else:
        frame.in_position = False


class LiveData(EClient, EWrapper):
    def __init__(self, frame: VolumeFrame):
        EClient.__init__(self, self)
        self.frame = frame

    def nextValidId(self, orderId: int):
        self.reqMarketDataType(2)
        # while self.isConnected():
        self.reqMktData(orderId, self.frame.contract, "", False, False, [])

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        ct = datetime.now(timezone("US/Eastern")).strftime("%H%M%S")
        if price == self.frame.take_profit or price == self.frame.stop_loss or ct == "15:30:00":
            print(f"tp {self.frame.take_profit}   sl {self.frame.stop_loss}  ct {ct}  price {price}")  # Debugging
            lmt_price = reqCurrentPrice(self.frame.CONN_VARS, self.frame.opt_contract)
            order = make_order(lmt_price, "SELL")
            self.frame.exit = place_order(self.frame.CONN_VARS, self.frame.opt_contract, order)
            self.frame.underlying_exit_price = price
            self.disconnect()
        else:
            print(f"{price}")
            sleep(1)


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
    vf.calculate_pnl()
