from db.db_config import get_connection
from datetime import datetime

class UserPickDB:
    @staticmethod
    def save_user_pick(user_id, n1, n2, n3, n4, n5, n6):
        """
        [저장 함수] DB 컬럼 이름 'reg_date'를 사용하도록 수정합니다.
        """
        query = """
            INSERT INTO user_pick (user_id, draw_no, p1, p2, p3, p4, p5, p6, reg_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING pick_id;
        """
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            # draw_no에 None을 전달 (NULL로 저장)
            params = (user_id, None, n1, n2, n3, n4, n5, n6, datetime.now()) 
            cur.execute(query, params)
            pick_id = cur.fetchone()[0]
            conn.commit()
            return True, pick_id
        except Exception as e:
            conn.rollback()
            print(f"DB Error (save_user_pick): {e}")
            return False, str(e)
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_user_picks(user_id):
        """
        [조회 함수] DB 컬럼 이름 'reg_date'를 사용하며, 인덱스 4번부터 번호를 조회합니다.
        """
        query = """
            SELECT 
                pick_id, user_id, draw_no, reg_date, 
                p1, p2, p3, p4, p5, p6
            FROM user_pick
            WHERE user_id = %s
            ORDER BY reg_date DESC;
        """
        conn = get_connection()
        cur = conn.cursor()
        picks = []

        try:
            cur.execute(query, (user_id,))
            rows = cur.fetchall()
            
            for row in rows:
                picks.append({
                    'pick_id': row[0],
                    # p1은 인덱스 4번부터 시작합니다. (p1~p6: row[4] ~ row[9])
                    'numbers': [row[4], row[5], row[6], row[7], row[8], row[9]], 
                    'pick_date': row[3]
                })
            
            return picks
        except Exception as e:
            print(f"❌ DB Error (get_user_picks - Final Column Name Fix): {e}") 
            return []
        finally:
            cur.close()
            conn.close()
            
    @staticmethod
    def delete_pick(pick_id, user_id):
        """
        특정 pick_id의 번호를 삭제합니다. 사용자 ID를 WHERE 절에 추가하여 
        다른 사용자의 데이터를 삭제하지 못하도록 보호합니다.
        필수 SQL 기능: SFW, DELETE
        """
        query = """
            DELETE FROM user_pick
            WHERE pick_id = %s AND user_id = %s;
        """
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(query, (pick_id, user_id))
            row_count = cur.rowcount # 실제로 삭제된 행의 수
            conn.commit()
            
            if row_count > 0:
                return True, "✅ 번호가 성공적으로 삭제되었습니다."
            else:
                return False, "❌ 삭제할 번호가 없거나, 해당 번호에 대한 삭제 권한이 없습니다."
                
        except Exception as e:
            conn.rollback()
            print(f"DB Error (delete_pick): {e}")
            return False, f"❌ 번호 삭제 실패 (DB 오류): {e}"
        finally:
            cur.close()
            conn.close()