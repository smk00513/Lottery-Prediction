# db/lotto_draw.py
from db.db_config import get_connection

class LottoDrawDB:
    @staticmethod
    def get_draw_data(offset, limit):
        """과거 당첨 번호를 페이징하여 조회합니다."""
        
        query = """
            SELECT draw_no, draw_date, n1, n2, n3, n4, n5, n6, bonus
            FROM LOTTO_DRAW
            ORDER BY draw_no DESC
            OFFSET %s LIMIT %s;
        """
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(query, (offset, limit))
            rows = cur.fetchall()
            return rows
        except Exception as e:
            print(f"DB Error (get_draw_data): {e}")
            return []
        finally:
            cur.close()
            conn.close()
        pass

    @staticmethod
    def get_total_count():
        """전체 데이터 개수를 조회하여 페이징에 사용합니다."""
        query = "SELECT COUNT(*) FROM LOTTO_DRAW;"
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(query)
            count = cur.fetchone()[0]
            return count
        except Exception as e:
            print(f"DB Error (get_total_count): {e}")
            return 0
        finally:
            cur.close()
            conn.close()
        pass
    
    @staticmethod
    def get_all_draws():
        """모든 과거 당첨 번호를 조회합니다. (비교 분석용)"""
        query = """
            SELECT draw_no, n1, n2, n3, n4, n5, n6, bonus
            FROM LOTTO_DRAW
            ORDER BY draw_no DESC; -- 최신 회차부터 정렬
        """
        conn = get_connection() # db/db_config.py에 정의된 함수를 사용한다고 가정
        cur = conn.cursor()

        try:
            cur.execute(query)
            # (draw_no, n1, n2, n3, n4, n5, n6, bonus) 형태의 튜플 리스트 반환
            rows = cur.fetchall()
            return rows
        except Exception as e:
            print(f"DB Error (get_all_draws): {e}")
            return []
        finally:
            cur.close()
            conn.close()