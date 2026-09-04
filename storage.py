import sqlite3
from scraper import parse_price
from scraper import scraping
import os


DB_PATH = os.getenv("DB_PATH", "database.db")

class Database:
    def __init__(self):
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
        self.c = self.conn.cursor()
        self.create_table()
        
        
        # self.conn = sqlite3.connect("database.db", check_same_thread = False, timeout = 10)
        # self.c = self.conn.cursor()
        # self.create_table()

    def create_table(self):

        self.c.execute("""
            CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
               name TEXT,
            last_price INTEGER
        )""")
            
        self.c.execute("""
            CREATE TABLE IF NOT EXISTS tracking(
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )""")
            
        self.c.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            price INTEGER,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )""")
        self.conn.commit()

    def track(self, url: str, user_id: int) -> tuple:
        name, price = parse_price(url)

        self.c.execute("SELECT id FROM products WHERE url = ?", (url,))
        row = self.c.fetchone()

        if row:
            product_id = row[0]
            self.c.execute("UPDATE products SET last_price = ? WHERE id = ?",
                           (price, product_id))
        else:
            self.c.execute("INSERT INTO products (url, name, last_price) VALUES (?,?,?)",
                           (url, name, price))
            product_id = self.c.lastrowid
        

        self.c.execute("SELECT id FROM tracking WHERE user_id = ? AND product_id = ?", 
                       (user_id, product_id))

        if not self.c.fetchone():
            self.c.execute("INSERT INTO tracking (user_id, product_id) VALUES (?, ?)",
                           (user_id, product_id))

        self.c.execute("INSERT INTO price_history (product_id, price) VALUES (?, ?)",
                       (product_id, price))

            
        self.conn.commit()
        return name, price

    def get_all_product(self) -> list:
        self.c.execute("SELECT id, url, name, last_price FROM products")
        return self.c.fetchall()
    
    def get_user_product(self, user_id: int) -> list:
        self.c.execute("""SELECT p.id, p.url, p.name, p.last_price FROM products p 
            JOIN tracking t ON p.id = t.product_id 
            WHERE t.user_id = ?""", (user_id,))
        return self.c.fetchall()

    def get_user(self, product_id: int) -> list:
        self.c.execute("SELECT user_id FROM tracking WHERE product_id = ?", 
                    (product_id, ))
        return [r[0] for r in self.c.fetchall()]

    def update_price(self, product_id: int, new_price: int) -> None:
        self.c.execute("UPDATE products SET last_price = ? WHERE id = ?", 
                    (new_price, product_id))
        
        self.c.execute("INSERT INTO price_history (product_id, price) VALUES (?, ?)",
                    (product_id, new_price))

        self.conn.commit()

    def remove_product(self, product_id: int, user_id:int) -> bool:
        self.c.execute("DELETE FROM tracking WHERE product_id = ? AND user_id = ?", 
                       (product_id, user_id))
        removed = self.c.rowcount > 0
        self.conn.commit()
        return removed
        

        

