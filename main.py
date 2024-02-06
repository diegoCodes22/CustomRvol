from ibapi.common import TickerId, TickAttrib
from ibapi.ticktype import TickType
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from TWSIBAPI_MODULES.exceptions_handler import exceptions_factory

from VolumeFrame import VolumeFrame
from Position import Position
from algos import entry_algorithm, exit_algorithm

from datetime import datetime
from time import sleep
from pytz import timezone


# Must calculate the amount of bars passed, and I must update after every bar.
# 0.4243 to reqHistData for 2 bars

# Make it so you can use a trailing stop.
# Option to add a trend filter

# 2.38s on avg until entry
# Creating frame and running entry algo


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
        exceptions_factory(errorCode)


if __name__ == "__main__":
    """
    Main function to run the program.
    """
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

    position.define_columns()
    engine = create_engine(f"sqlite:///{vf.db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(position)
    session.commit()
