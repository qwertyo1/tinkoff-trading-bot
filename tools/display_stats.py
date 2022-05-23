import sqlite3


def get_orders():
    with sqlite3.connect("stats.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders")
        return cursor.fetchall()


if __name__ == "__main__":
    orders = get_orders()
    for order in orders:
        print(order)
