from ibapi.common import TickerId, TickAttrib
from ibapi.ticktype import TickType
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from TWSIBAPI_MODULES.exceptions_handler import exceptions_factory
from TWSIBAPI_MODULES.utils import mkt_is_open, sleep_one_bar

from VolumeFrame import VolumeFrame
from Position import Position
from algos import entry_algorithm, exit_algorithm

from datetime import datetime
from time import sleep
from pytz import timezone


def log_trade(database_path: str, pos: Position):
    engine = create_engine(f"sqlite:///{database_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(pos)
    session.commit()


class LiveData(EClient, EWrapper):
    """
    Class to handle live data from TWS. Used to track when to sell an open position.
    """
    def __init__(self, frame: VolumeFrame, pos: Position):
        EClient.__init__(self, self)
        self.frame = frame
        self.pos = pos

    def nextValidId(self, orderId: int):
        self.reqMarketDataType(2)
        self.reqMktData(orderId, self.frame.contract, "", False, False, [])

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        if price == self.pos.take_profit or price == self.pos.stop_loss:
            self.pos.underlying_exit_price = price
            self.disconnect()
        else:
            print(f"{price}  ----  tp {self.pos.take_profit}   sl {self.pos.stop_loss}")
            sleep(1)

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        exceptions_factory(errorCode)


if __name__ == "__main__":
    """
    Main function to run the program.
    """
    while mkt_is_open() and datetime.now(timezone("US/Eastern")).strftime("%H:%M") < "15:30":
        vf = VolumeFrame()
        position = entry_algorithm(vf)
        if position.in_position:
            position.calculate_bracket()
            lv = LiveData(vf, position)
            lv.connect(vf.CONN_VARS[0], vf.CONN_VARS[1], vf.CONN_VARS[2])
            lv.run()
            exit_algorithm(vf, position)
            position.define_columns()
            log_trade(vf.db_path, position)
        else:
            print("No trade was taken.")
        sleep_one_bar(vf.bar_size)

