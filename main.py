
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
from time import sleep
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


def entry_algorithm(frame: VolumeFrame) -> None:
    ct = datetime.now(timezone("US/Eastern")).strftime("%Y%m%d %H%M%S")
    frame.direction = 1 if (frame.close - frame.open) > 0 else -1
    # if frame.volume > frame.avg_vol and abs(diff) > frame.atr * 1.2 and not frame.in_position:
    if frame.direction != 0:
        frame.expiration = (datetime.strptime(ct.split(" ")[0], "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
        strike_calc = frame.atr + frame.atr / 4
        if frame.direction == 1:
            frame.strike = round(frame.close + strike_calc)
        else:
            frame.strike = round(frame.close - strike_calc)
        frame.opt_contract = option(frame.symbol, frame.expiration, frame.strike, 'C' if frame.direction > 0 else 'P')
        order = make_order(frame.opt_contract, "BUY", frame.CONN_VARS)
        frame.entry = place_order(frame.CONN_VARS, frame.opt_contract, order)
        frame.underlying_entry_price = reqCurrentPrice(frame.CONN_VARS, frame.contract)
        frame.in_position = 1
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
        print(f"tp {self.frame.take_profit}   sl {self.frame.stop_loss}  ct {ct}")
        if price == self.frame.take_profit or price == self.frame.stop_loss or ct == "15:30:00":
            order = make_order(self.frame.opt_contract, "SELL", self.frame.CONN_VARS)
            self.frame.exit = place_order(self.frame.CONN_VARS, self.frame.opt_contract, order)
            self.frame.underlying_exit_price = price
            self.disconnect()
        else:
            print(f"{price}")
            sleep(1)


if __name__ == "__main__":
    vf = VolumeFrame(symbol="SPY")
    entry_algorithm(vf)
    if vf.in_position == 0:
        print("No trade was taken, Exiting...")
        exit(0)
    vf.calculate_bracket()
    lv = LiveData(vf)
    lv.connect(vf.CONN_VARS[0], vf.CONN_VARS[1], vf.CONN_VARS[2])
    lv.run()
    vf.calculate_pnl()
