from ibapi.common import TickerId, TickAttrib
from ibapi.ticktype import TickType
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

from TWSIBAPI_MODULES.Contracts import option
from TWSIBAPI_MODULES.DataStreams import reqCurrentPrice
from TWSIBAPI_MODULES.Orders import place_order

from VolumeFrame import VolumeFrame
from datetime import datetime, timedelta
from pytz import timezone
from typing import List


def make_order(contract: Contract, act, CONN_VARS: List) -> Order:
    order = Order()
    order.orderId = 0
    order.action = act
    order.totalQuantity = 1
    order.orderType = "LMT"
    order.lmtPrice = reqCurrentPrice(CONN_VARS, contract)
    order.eTradeOnly = ''
    order.firmQuoteOnly = ''
    return order


def entry_algorithm(frame: VolumeFrame, ct: str) -> None:
    diff = frame.open - frame.close
    if frame.volume > frame.avg_vol and abs(diff) > frame.atr * 1.35 and not frame.in_position:
        frame.expiration = (datetime.strptime(ct.split(" ")[0], "%Y%m%d") + timedelta(days=2)).strftime("%Y%m%d")
        frame.strike = frame.close + round(frame.atr + frame.atr / 4)
        frame.opt_contract = option(frame.symbol, frame.expiration, frame.strike, 'c' if diff > 0 else 'p')
        order = make_order(frame.opt_contract, "BUY", frame.CONN_VARS)
        place_order(frame.CONN_VARS, frame.opt_contract, order)
        frame.direction = 1 if diff > 0 else -1
        frame.in_position = reqCurrentPrice(frame.CONN_VARS, frame.contract)
    else:
        frame.in_position = 0


class LiveData(EClient, EWrapper):
    def __init__(self, frame: VolumeFrame):
        EClient.__init__(self, self)
        self.frame = frame

    def nextValidId(self, orderId: int):
        self.reqMarketDataType(2)
        self.reqMktData(orderId, self.frame.contract, "", False, False, [])

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        ct = datetime.now(timezone("US/Eastern")).strftime("%H%M%S")
        self.frame.pnl = self.frame.entry - price if self.frame.direction == -1 else price - self.frame.entry
        if price == self.frame.take_profit or self.frame.stop_loss or ct == "15:30:00":
            order = make_order(self.frame.opt_contract, "SELL", self.frame.CONN_VARS)
            place_order(self.frame.CONN_VARS, self.frame.opt_contract, order)
            self.disconnect()
        else:
            print(self.frame.pnl)




if __name__ == "__main__":
    vf = VolumeFrame(symbol="SPY")
    current_time = datetime.now(timezone("US/Eastern")).strftime("%Y%m%d %H%M%S")
    if current_time.split(" ")[1] == "09:30:00":
        entry_algorithm(vf, current_time)
        if vf.in_position == 0:
            print("No trade was taken, Exiting...")
            exit(0)
        lv = LiveData(vf)
        lv.run()

