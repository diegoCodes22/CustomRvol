from TWSIBAPI_MODULES.Contracts import option
from TWSIBAPI_MODULES.Orders import place_order
from TWSIBAPI_MODULES.DataStreams import reqCurrentPrice
from TWSIBAPI_MODULES.exceptions_handler import NoSecDef
from VolumeFrame import VolumeFrame
from Position import Position
from ibapi.order import Order
from ibapi.tag_value import TagValue
from datetime import datetime, timedelta
from pytz import timezone


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
                lmt_price = reqCurrentPrice(frame.CONN_VARS, pos.opt_contract) - 0.2
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


def exit_algorithm(frame: VolumeFrame, pos: Position) -> None:
    lmt_price = reqCurrentPrice(frame.CONN_VARS, pos.opt_contract)
    order = make_order(lmt_price, "SELL", frame.multiplier)
    order.algoStrategy = 'Adaptive'
    order.algoParams = [TagValue("adaptivePriority", 'Urgent')]
    order_details = place_order(frame.CONN_VARS, pos.opt_contract, order)
    pos.exit = order_details[0]
    pos.exit_time = datetime.now(timezone("US/Eastern"))
    pos.commission += order_details[1]
    pos.in_position = False
