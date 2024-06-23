import sqlite3
import hashlib
from datetime import datetime, timedelta
import json


class DataBase:
    def __init__(
        self,
        name_db: str
    ):
        self.name_db = name_db
        with sqlite3.connect(self.name_db) as conn:
            conn.execute(
                f"""CREATE TABLE IF NOT EXISTS users (
                id integer PRIMARY KEY,
                username text NOT NULL,
                first_name text,
                last_name text,
                category_name text,
                query text,
                url text,
                top_status boolean DEFAULT 0,
                tracking boolean DEFAULT 0
                );"""
            )
            conn.execute(
                f"""CREATE TABLE IF NOT EXISTS category (
                name text PRIMARY KEY,
                link text NOT NULL,
                picture text
                );"""
            )

    def _hash_name(self, name: str) -> str:
        return hashlib.md5(name.encode()).hexdigest()

    def check_user(self, user_id: int) -> bool:
        with sqlite3.connect(self.name_db) as conn:
            cursor = conn.execute(f"SELECT 1 FROM users WHERE id = {user_id}")
            return bool(cursor.fetchone())

    def sign_up_user(
        self,
        user_id: int,
        username: str,
        first_name: str,
        last_name: str
    ):
        with sqlite3.connect(self.name_db) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, last_name)
            )
            conn.commit()

    def get_users_list(self):
        with sqlite3.connect(self.name_db) as conn:
            cursor = conn.execute("SELECT * FROM users")
            users = cursor.fetchall()
        return users

    def get_query_info(self, user_id: int) -> tuple:
        with sqlite3.connect(self.name_db) as conn:
            cursor = conn.execute(
                "SELECT url, category_name, query, top_status FROM users WHERE id = ?", (
                    user_id,)
            )
            result = cursor.fetchone()
        return result

    def delete_all_users(self):
        with sqlite3.connect(self.name_db) as conn:
            conn.execute("DELETE FROM users")
            conn.commit()

    def add_category_records(self, category_data: list):
        with sqlite3.connect(self.name_db) as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO category (name, link, picture) VALUES (?, ?, ?)",
                category_data
            )
            conn.commit()

    def get_category_names(self):
        with sqlite3.connect(self.name_db) as conn:
            cursor = conn.execute("SELECT name FROM category")
            names = [row[0] for row in cursor.fetchall()]
        return names

    def get_category_link(self, category_name: str) -> str:
        with sqlite3.connect(self.name_db) as conn:
            cursor = conn.execute(
                "SELECT link FROM category WHERE name = ?", (category_name,)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
        return None

    def delete_all_categories(self):
        with sqlite3.connect(self.name_db) as conn:
            conn.execute("DELETE FROM category")
            conn.commit()

    def save_parse_data(self, table_name: str, parse_data: dict, threshold_days: int = None):
        db_data = []
        table_name_lower = table_name.lower()
        table_name_hashed = self._hash_name(table_name_lower)
        for id, data in parse_data.items():
            db_data.append(
                (
                    id,
                    data.get("link"),
                    data.get("promo"),
                    data.get("name"),
                    data.get("price"),
                    data.get("type"),
                    data.get("location"),
                    data.get("date")
                )
            )

        with sqlite3.connect(self.name_db) as conn:
            conn.execute(
                f"""CREATE TABLE IF NOT EXISTS "{table_name_hashed}" (
                id integer PRIMARY KEY,
                link text NOT NULL,
                promo boolean NOT NULL,
                name text NOT NULL,
                price text NOT NULL,
                type text,
                location text,
                date text
                );"""
            )

            if threshold_days:
                threshold_date = (
                    datetime.now() - timedelta(days=threshold_days)
                ).isoformat()
                conn.execute(
                    f"""DELETE FROM "{table_name_hashed}"
                    WHERE date < ?""",
                    (threshold_date,)
                )

            conn.executemany(
                f"""INSERT OR IGNORE INTO "{table_name_hashed}"
                (id, link, promo, name, price, type, location, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                db_data
            )
            conn.commit()

    def check_new_posts(self, user_id: int, name_parse: str, status_top: bool) -> list:
        name_parse_lower = name_parse.lower()
        name_parse_hashed = self._hash_name(name_parse_lower)
        with sqlite3.connect(self.name_db) as conn:
            if status_top:
                cursor = conn.execute(f"SELECT id FROM '{name_parse_hashed}'")
            else:
                cursor = conn.execute(
                    f"SELECT id FROM '{name_parse_hashed}' WHERE promo = ?", (False,))
            post_id_set = {row[0] for row in cursor.fetchall()}
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            if name_parse_hashed not in columns:
                conn.execute(
                    f"ALTER TABLE users ADD COLUMN '{name_parse_hashed}' TEXT")
            cursor = conn.execute(
                f"SELECT \"{name_parse_hashed}\" FROM users WHERE id = ?", (
                    user_id,)
            )
            result = cursor.fetchone()[0]
            old_posts_id_set = set(json.loads(result) if result else [])
            new_posts_id_list = list(post_id_set - old_posts_id_set)
            if not new_posts_id_list:
                return []
            updated_post_id_list = list(post_id_set)
            conn.execute(
                f"UPDATE users SET \"{name_parse_hashed}\" = ? WHERE id = ?",
                (json.dumps(updated_post_id_list), user_id)
            )
            conn.commit()
            placeholders = ','.join('?' for _ in new_posts_id_list)
            query = f"SELECT * FROM '{name_parse_hashed}' WHERE id IN ({placeholders}) ORDER BY date ASC"
            cursor = conn.execute(query, new_posts_id_list)
            new_posts_list = cursor.fetchall()
        return new_posts_list

    def set_tracking_users(self, user_id: int, status: bool):
        with sqlite3.connect(self.name_db) as conn:
            conn.execute(
                f"UPDATE users SET tracking = ? WHERE id = ?",
                (status, user_id)
            )
            conn.commit()

    def set_query_users(
        self,
        user_id: int,
        category_name: str = None,
        query: str = None,
        url: str = None
    ):
        with sqlite3.connect(self.name_db) as conn:
            if url is not None:
                conn.execute(
                    "UPDATE users SET url = ?, category_name = NULL, query = NULL WHERE id = ?",
                    (url, user_id)
                )
            else:
                update_values = []
                update_query = "UPDATE users SET "
                if category_name is not None:
                    update_query += "category_name = ?, "
                    update_values.append(category_name)
                if query is not None:
                    update_query += "query = ?, "
                    update_values.append(query)
                update_query += "url = NULL WHERE id = ?"
                update_values.append(user_id)
                conn.execute(update_query, update_values)
            conn.commit()

    def turn_top_status(self, user_id: int):
        with sqlite3.connect(self.name_db) as conn:
            conn.execute(
                f"UPDATE users SET top_status = NOT top_status WHERE id = ?",
                (user_id,)
            )
            conn.commit()

    def check_tracking_users(self, user_id: int) -> bool:
        with sqlite3.connect(self.name_db) as conn:
            cursor = conn.execute(
                f"SELECT tracking FROM users WHERE id = ?", (user_id,)
            )
            status = cursor.fetchone()
            if status is None:
                return False
        return bool(status[0])

    def check_top_status(self, user_id: int) -> bool:
        with sqlite3.connect(self.name_db) as conn:
            cursor = conn.execute(
                f"SELECT top_status FROM users WHERE id = ?", (user_id,)
            )
            status = cursor.fetchone()[0]
        return bool(status)
