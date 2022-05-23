from app.sqlite.client import SQLiteClient


class StatsSQLiteClient:
    def __init__(self, db_name: str):
        self.db_client = SQLiteClient(db_name)
        self.db_client.connect()

        self._create_tables()

    def _create_tables(self):
        self.db_client.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                figi str,
                direction TEXT,
                price REAL,
                quantity INTEGER,
                status TEXT
            )
            """
        )

    def add_order(
        self,
        order_id: str,
        figi: str,
        order_direction: str,
        price: float,
        quantity: int,
        status: str,
    ):
        self.db_client.execute_insert(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
            (order_id, figi, order_direction, price, quantity, status),
        )

    def get_orders(self):
        return self.db_client.execute_select("SELECT * FROM orders")

    def update_order_status(self, order_id: str, status: str):
        self.db_client.execute_update(
            "UPDATE orders SET status=? WHERE id=?",
            (status, order_id),
        )
