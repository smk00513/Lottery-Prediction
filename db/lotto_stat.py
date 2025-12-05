from db.db_config import get_connection
import sys

# StatService에서 사용할 DB 접근 클래스
class LottoStatDB:

    # =========================================================================
    # 1. 통계 데이터 갱신 (트랜잭션 적용)
    # DDL: number, frequency, last_draw_gap 만 사용
    # =========================================================================
    @staticmethod
    def update_statistics_transaction():
        conn = None
        cur = None
        try:
            conn = get_connection()
            cur = conn.cursor()

            # 1. LOTTO_STAT 테이블 초기화
            cur.execute("TRUNCATE TABLE lotto_stat RESTART IDENTITY;")

            # 2. 통계 계산 및 삽입 (frequency, last_draw_gap 계산)
            stat_query = """
                WITH NumberCounts AS (
                    -- 모든 당첨 번호(n1~n6)를 행으로 변환하여, 마지막 출현 회차를 찾습니다.
                    SELECT 
                        unnest(ARRAY[n1, n2, n3, n4, n5, n6]) AS number_val,
                        draw_no
                    FROM lotto_draw
                ),
                AggregatedStats AS (
                    SELECT
                        g.number,
                        COALESCE(count(c.number_val), 0) AS frequency, -- ★ 수정: DDL에 맞게 frequency 사용
                        MAX(c.draw_no) AS last_draw_no,
                        COUNT(c.number_val) AS num_occurrences
                    FROM (
                        SELECT generate_series(1, 45) AS number 
                    ) AS g
                    LEFT JOIN NumberCounts AS c ON g.number = c.number_val
                    GROUP BY g.number
                    ORDER BY g.number
                )
                -- LOTTO_STAT 테이블에 최종 통계 데이터 삽입 (number, frequency, last_draw_gap)
                INSERT INTO lotto_stat (number, frequency, last_draw_gap)
                SELECT
                    number,
                    frequency,
                    -- last_draw_gap 계산: 현재 최대 회차 - 마지막 출현 회차
                    CASE 
                        WHEN num_occurrences > 0 AND (SELECT MAX(draw_no) FROM lotto_draw) IS NOT NULL
                            THEN (SELECT MAX(draw_no) FROM lotto_draw) - last_draw_no
                        ELSE NULL -- 한 번도 나오지 않은 번호는 NULL (last_draw_gap DDL에 맞춤)
                    END AS last_draw_gap
                FROM AggregatedStats;
            """
            cur.execute(stat_query)

            # 성공 시 커밋 (트랜잭션 완료)
            conn.commit()
            return True, "✅ 로또 통계가 성공적으로 갱신되었습니다. (Transaction Complete)"

        except Exception as e:
            if conn:
                # 오류 발생 시 롤백 (트랜잭션 취소)
                conn.rollback()
            print("DB Error (update_statistics_transaction):", e, file=sys.stderr)
            return False, f"❌ 로또 통계 갱신 실패 (DB 오류, 롤백됨): {e}"
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()


    # =========================================================================
    # 2. 통계 데이터 조회
    # DDL에 맞게 number, frequency, last_draw_gap 만 조회
    # =========================================================================
    @staticmethod
    def get_all_stats():
        query = """
            SELECT 
                number,
                frequency,
                last_draw_gap
            FROM lotto_stat
            ORDER BY number ASC;
        """
        conn = None
        cur = None 
        stats = []
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(query)
            
            # 조회 결과를 딕셔너리 리스트로 변환
            rows = cur.fetchall()
            
            for row in rows:
                stats.append({
                    'number': row[0],
                    'frequency': row[1], 
                    'last_draw_gap': row[2]
                })
                
            return stats
        except Exception as e:
            print("DB Error (get_all_stats):", e, file=sys.stderr)
            return []
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()