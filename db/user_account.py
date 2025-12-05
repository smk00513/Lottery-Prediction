from db.db_config import get_connection
from datetime import datetime

class UserAccountDB:
    @staticmethod
    def create_user(username, password_hash):
        query = """
            INSERT INTO user_account (username, password, join_date, status)
            VALUES (%s, %s, %s, %s)
        """
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(query, (username, password_hash, datetime.now(), 'active'))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print("DB Error (create_user):", e)
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_user_by_username(username):
        query = """
            SELECT user_id, username, password, status
            FROM user_account
            WHERE username = %s
        """
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(query, (username,))
        row = cur.fetchone()

        cur.close()
        conn.close()

        return row
