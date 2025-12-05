from db.lotto_recommend import LottoRecommendDB

class RecommendService:
    @staticmethod
    def generate_recommendation(user_id):
        """
        통계 기반 추천 번호를 생성하고, user_id를 이용해 개인화 필터링을 적용합니다.
        """
        # 1. 추천 점수 계산을 위한 VIEW 생성/갱신
        LottoRecommendDB.create_recommend_view()
        
        # 2. VIEW를 활용하여 개인화 추천 번호 6개 가져오기
        recommendation = LottoRecommendDB.get_recommended_numbers(user_id, limit=6) 
        
        if not recommendation:
            return False, "❌ 추천 번호 생성에 실패했습니다. (통계 데이터 부족 또는 DB 오류)", []

        # 추천 번호 (숫자) 리스트만 추출
        numbers = [num[0] for num in recommendation]
        
        # True: 성공, numbers: 추천 번호 6개, recommendation: 상세 통계 정보
        return True, numbers, recommendation
    
    @staticmethod
    def create_recommend_view_only():
        """
        로또 통계 갱신 후, 추천 시스템이 사용하는 DB VIEW만 갱신합니다.
        """
        LottoRecommendDB.create_recommend_view()
        return True