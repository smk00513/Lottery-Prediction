from db.lotto_stat import LottoStatDB

class StatService:
    @staticmethod
    def update_statistics():
        """
        [로또 통계 갱신]
        실제 DB의 통계 계산 및 갱신(TRUNCATE + INSERT)을 LottoStatDB에 위임합니다.
        
        *서비스 계층에서는 DB 연결(connection) 및 트랜잭션(commit/rollback)을 직접 처리하지 않습니다.*
        """
        # LottoStatDB의 트랜잭션 함수 호출 (DB 계층에 위임)
        success, msg = LottoStatDB.update_statistics_transaction()
        return success, msg
    
    @staticmethod
    def get_all_stats():
        """
        [로또 통계 조회]
        로또 통계 데이터를 DB에서 조회하여 반환합니다. 
        이 메서드가 app.py에서 호출되어 AttributeError를 해결합니다.
        """
        # LottoStatDB의 조회 메서드를 호출
        return LottoStatDB.get_all_stats()