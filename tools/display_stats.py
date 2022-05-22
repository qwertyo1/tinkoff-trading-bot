import sqlite3
import sys


def get_orders(figi: str):
    with sqlite3.connect("stats.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM orders WHERE figi=?",
            (figi,),
        )
        return cursor.fetchall()


if __name__ == "__main__":
    orders = get_orders(figi=sys.argv[1])
    for order in orders:
        print(order)
