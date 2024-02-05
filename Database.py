import sqlite3


class Database:
    def __init__(self, db_path: str):
        self.conn = None
        self.cur = None
        self.db_path = db_path

    def start_db(self) -> None:
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cur = self.conn.cursor()
        except sqlite3.OperationalError:
            print("Invalid database file, Operational Error raised.")
            exit(1)

    def close_db(self) -> None:
        self.cur.close()
        self.conn.close()

    def log_entry(self) -> None:
        pass

    def log_exit(self) -> None:
        pass
