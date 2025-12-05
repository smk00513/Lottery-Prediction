import pandas as pd
from db.db_config import get_connection

def load_csv_to_db(csv_path):
    df = pd.read_csv(csv_path)

    # 컬럼 이름 통일 (추첨일, 1~6, 보너스)
    df = df.rename(columns={
        '회차': 'draw_no',
        '추첨일': 'draw_date',
        '1': 'n1',
        '2': 'n2',
        '3': 'n3',
        '4': 'n4',
        '5': 'n5',
        '6': 'n6',
        '보너스': 'bonus'
    })

    # 날짜 형식 통일
    df['draw_date'] = pd.to_datetime(df['draw_date'])

    # DB 연결
    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO lotto_draw (draw_no, draw_date, n1, n2, n3, n4, n5, n6, bonus)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (draw_no) DO NOTHING;
            """, (
                int(row['draw_no']),
                row['draw_date'],
                int(row['n1']),
                int(row['n2']),
                int(row['n3']),
                int(row['n4']),
                int(row['n5']),
                int(row['n6']),
                int(row['bonus'])
            ))
        except Exception as e:
            print(f"Error inserting row {row['draw_no']}: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"{csv_path} 데이터 로딩 완료!")

# ======================
# 두 CSV 파일 순차 처리
# ======================
csv_files = ["1600.csv", "6011200.csv"]

for file in csv_files:
    load_csv_to_db(file)
