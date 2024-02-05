from unittest import main, TestCase
from Position import Position
from VolumeFrame import VolumeFrame
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pytz import timezone


class DatabaseTest(TestCase):
    def setUp(self) -> None:
        self.vf = VolumeFrame(symbol="SPY")
        self.pos = Position(self.vf)
        self.define_pos()
        self.engine = create_engine("sqlite:///database_tests.sqlite")
        self.Session = sessionmaker(bind=self.engine)

    def tearDown(self) -> None:
        session = self.Session()
        session.query(Position).delete()
        session.commit()
        session.close()
        self.engine.dispose()

    def test_database_insertion(self):
        session = self.Session()
        session.add(self.pos)
        session.commit()
        db_insertion = session.query(Position).first()
        session.close()

        self.assertEqual(db_insertion, self.pos)

    def define_pos(self):
        self.pos.trade_date = datetime.now(timezone("US/Eastern")).strftime("%Y%m%d")
        diff = self.pos.close - self.pos.open
        self.pos.direction = 1 if diff > 0 else -1
        self.pos.entry = self.pos.close / 100
        self.pos.entry_time = datetime.now(timezone("US/Eastern"))
        self.pos.underlying_entry_price = self.pos.close
        self.pos.commission += 1.3
        self.pos.in_position = True
        self.pos.calculate_bracket()
        self.pos.underlying_exit_price = self.pos.close + 1
        self.pos.exit = (self.pos.close / 100) + 1
        self.pos.exit_time = datetime.now(timezone("US/Eastern"))
        self.pos.commission += 0.8
        self.pos.define_columns()


if __name__ == "__main__":
    main()
