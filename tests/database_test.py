from Position import Position
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from VolumeFrame import VolumeFrame
from datetime import datetime, timedelta
from pytz import timezone
from TWSIBAPI_MODULES.Contracts import option
from time import sleep


vf = VolumeFrame(symbol="SPY")
pos = Position(vf)

pos.trade_date = datetime.now(timezone("US/Eastern")).strftime("%Y%m%d")
diff = pos.close - pos.open
pos.direction = 1 if diff > 0 else -1
pos.strike = pos.close
pos.expiration = (datetime.strptime(pos.trade_date, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
pos.opt_contract = option(pos.symbol, pos.expiration, pos.strike, 'C' if pos.direction > 0 else 'P')
pos.entry = pos.close / 100
pos.entry_time = datetime.now(timezone("US/Eastern"))
pos.underlying_entry_price = pos.close
pos.commission += 1.3
pos.in_position = True

pos.calculate_bracket()

pos.underlying_exit_price = pos.close + 1
pos.exit = (pos.close / 100) + 1
sleep(10)
pos.exit_time = datetime.now(timezone("US/Eastern"))
pos.commission += 0.8

pos.define_columns()

print(pos)

engine = create_engine("sqlite:///../TradeLog.sqlite")
Session = sessionmaker(bind=engine)
session = Session()
session.add(pos)
session.commit()

session.close()
engine.dispose()