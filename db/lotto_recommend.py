# db/lotto_recommend.py
from db.db_config import get_connection

class LottoRecommendDB:
    @staticmethod
    def create_recommend_view():
        """
        추천 점수 계산을 위한 VIEW를 생성합니다.
        필수 SQL 기능: VIEW, RANK() OVER (Window Function)
        """
        # LOTTO_STAT 테이블의 frequency와 last_draw_gap을 활용
        query = """
        CREATE OR REPLACE VIEW v_lotto_recommend_score AS
        SELECT
            number,
            frequency,
            last_draw_gap,
            -- 빈도 순위 (높은 빈도일수록 1등. DESC)
            RANK() OVER (ORDER BY frequency DESC) AS frequency_rank,
            -- 미출현 간격 순위 (긴 간격일수록 1등. DESC)
            RANK() OVER (ORDER BY last_draw_gap DESC) AS gap_rank,
            -- ⭐ 최종 추천 점수 (순위 합산, 낮을수록 좋음) ⭐
            (RANK() OVER (ORDER BY frequency DESC) + RANK() OVER (ORDER BY last_draw_gap DESC)) AS total_score
        FROM LOTTO_STAT;
        """
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query)
            conn.commit()
            print("✅ VIEW 'v_lotto_recommend_score' 생성/갱신 완료.")
            return True
        except Exception as e:
            conn.rollback()
            print(f"DB Error (create_recommend_view): {e}")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_recommended_numbers(user_id, limit=6):
        """
        VIEW와 JOIN/WHERE를 활용하여 개인화된 추천 번호 6개를 조회합니다.
        (사용자가 과거에 선택한 번호(USER_PICK)는 제외합니다.)
        """
        query = f"""
        WITH 
        -- 1. 사용자가 과거에 선택한 모든 번호를 추출 (JOIN 및 UNNEST 사용)
        user_cold_picks AS (
            SELECT DISTINCT unnest(ARRAY[p1, p2, p3, p4, p5, p6]) AS cold_number
            FROM USER_PICK up
            WHERE up.user_id = %s -- WHERE 절로 특정 사용자의 데이터만 필터링
        )
        -- 2. 추천 점수 VIEW에서 데이터를 가져와, 사용자의 cold_picks를 제외 (LEFT JOIN / WHERE NOT NULL)
        SELECT
            vrs.number,
            vrs.total_score,
            vrs.frequency,
            vrs.last_draw_gap
        FROM v_lotto_recommend_score vrs
        LEFT JOIN user_cold_picks ucp ON vrs.number = ucp.cold_number
        WHERE ucp.cold_number IS NULL -- 과거 선택한 번호(cold_number)가 없는 행만 선택
        ORDER BY vrs.total_score ASC, vrs.frequency DESC 
        LIMIT {limit};
        """
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query, (user_id,))
            results = cur.fetchall()
            return results
        except Exception as e:
            print(f"DB Error (get_recommended_numbers with join/where): {e}")
            return []
        finally:
            cur.close()
            conn.close()