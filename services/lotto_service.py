from db.lotto_draw import LottoDrawDB
from db.user_pick import UserPickDB
import math
from datetime import datetime
import random

# ---------------------------------------------------------
# 당첨 판정 함수
# ---------------------------------------------------------

def get_match_counts(user_numbers, win_numbers, bonus_number):
    user_set = set(user_numbers)
    win_set = set(win_numbers)

    match_count = len(user_set.intersection(win_set))
    has_bonus = bonus_number in user_set

    if match_count == 6:
        return 1
    elif match_count == 5 and has_bonus:
        return 2
    elif match_count == 5:
        return 3
    elif match_count == 4:
        return 4
    elif match_count == 3:
        return 5
    return 0


# ---------------------------------------------------------
# Mock LottoStatDB
# ---------------------------------------------------------

class LottoStatDB:
    @staticmethod
    def get_stat_for_numbers(numbers):
        stat_details = []
        current_draw_id = 1100
        for number in numbers:
            freq = random.randint(100, 150)
            last_draw_id = current_draw_id - random.randint(1, 30)
            gap = current_draw_id - last_draw_id
            stat_details.append({
                "number": number,
                "frequency": freq,
                "last_draw_id": last_draw_id,
                "last_draw_gap": gap
            })
        return stat_details


# ---------------------------------------------------------
# Lotto Service
# ---------------------------------------------------------

class LottoService:

    # 페이징 조회
    @staticmethod
    def get_paginated_draws(page=1, per_page=20):
        total_count = LottoDrawDB.get_total_count()
        total_pages = math.ceil(total_count / per_page)
        offset = (page - 1) * per_page
        draws = LottoDrawDB.get_draw_data(offset, per_page)

        return {
            "draws": draws,
            "total_pages": total_pages,
            "current_page": page,
            "total_count": total_count
        }

    # 분석 코멘트 생성기
    @staticmethod
    def check_analysis_comments(numbers):
        numbers = sorted(numbers)

        stat_details = LottoStatDB.get_stat_for_numbers(numbers)
        total_freq = sum(s["frequency"] for s in stat_details)

        num_sum = sum(numbers)
        odd_count = sum(n % 2 != 0 for n in numbers)
        low_count = sum(n <= 22 for n in numbers)
        consecutive_count = sum(1 for i in range(5) if numbers[i+1] == numbers[i] + 1)

        return LottoService._get_analysis_comment(
            num_sum, odd_count, low_count, consecutive_count, total_freq
        )

    # 사용자 선택 번호 분석
    @staticmethod
    def check_pick_analysis(user_numbers):
        """
        사용자 번호를 과거 당첨 번호와 비교하여 당첨 이력 및 분석 결과를 반환합니다.
        오류 발생 시에도 절대 None을 반환하지 않도록 방어적으로 작성됨.
        """

        try:
            # 1. 모든 과거 당첨번호 조회
            all_draws = LottoDrawDB.get_all_draws()
            if not all_draws:
                all_draws = []

            # 2. 당첨이력 초기화
            history_analysis_results = {
                'total_draws': len(all_draws),
                1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 0: 0
            }

            # 3. 당첨 비교
            for draw in all_draws:
                if len(draw) < 8:
                    continue  # 데이터 불완전하면 스킵

                win_numbers = list(draw[1:7])
                bonus_number = draw[7]

                rank = get_match_counts(user_numbers, win_numbers, bonus_number)
                history_analysis_results[rank] += 1

            # 4. 코멘트 + 개별 통계
            comments = LottoService.check_analysis_comments(user_numbers)

            detailed_stats = LottoStatDB.get_stat_for_numbers(user_numbers)
            if not detailed_stats:
                detailed_stats = []

            # 안전한 점수 계산 (문자열 필터링 포함)
            import re

            freqs = []
            gaps = []

            for s in detailed_stats:
                freq_raw = s.get("frequency", 0)
                freq_num = re.sub(r"\D", "", str(freq_raw))
                s["frequency"] = int(freq_num) if freq_num.isdigit() else 0

                gap_raw = s.get("last_draw_gap", 0)
                gap_num = re.sub(r"\D", "", str(gap_raw))
                s["last_draw_gap"] = int(gap_num) if gap_num.isdigit() else 0

                freqs.append(s["frequency"])
                gaps.append(s["last_draw_gap"])

            # 안전한 최대값 보호
            max_freq = max(freqs) if freqs and max(freqs) > 0 else 1
            max_gap = max(gaps) if gaps and max(gaps) > 0 else 1

            # 가중치
            w_freq = 0.7
            w_gap = 0.3

            for s in detailed_stats:
                f = float(s["frequency"])
                g = float(s["last_draw_gap"])

                freq_norm = f / max_freq
                gap_norm = 1 - (g / max_gap)

                score = (w_freq * freq_norm + w_gap * gap_norm) * 100
                s["total_score"] = round(score, 2)

            # 정상 반환
            return history_analysis_results, comments, detailed_stats

        except Exception as e:
            print("CHECK_PICK_ANALYSIS ERROR:", e)
            # 템플릿이 깨지지 않도록 기본값 반환
            return (
                {'total_draws': 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 0: 0},
                ["❌ 분석 중 오류가 발생했습니다. (console 로그 확인)"],
                []
            )
            
            
    # ---------------------------------------------------------
    # 사용자 PICK 저장
    # ---------------------------------------------------------
    @staticmethod
    def save_user_pick(user_id, numbers):
        if not (isinstance(numbers, list) and len(numbers) == 6):
            return False, "❌ 번호는 정확히 6개여야 합니다."

        try:
            numbers = [int(n) for n in numbers]
        except:
            return False, "❌ 모든 번호는 정수여야 합니다."

        if not all(1 <= n <= 45 for n in numbers):
            return False, "❌ 번호는 1~45 사이여야 합니다."

        if len(set(numbers)) != 6:
            return False, "❌ 번호에 중복이 있으면 안 됩니다."

        numbers.sort()
        return UserPickDB.save_user_pick(user_id, *numbers)

    @staticmethod
    def get_user_picks(user_id):
        return UserPickDB.get_user_picks(user_id)

    @staticmethod
    def delete_pick(pick_id, user_id):
        return UserPickDB.delete_pick(pick_id, user_id)

    # ---------------------------------------------------------
    # 분석 코멘트 생성기
    # ---------------------------------------------------------
    @staticmethod
    def _get_analysis_comment(num_sum, odd_count, low_count, consecutive_count, total_freq):
        comments = []

        if num_sum < 80:
            comments.append("총합계가 매우 낮은 편입니다. 일반적 범위는 100~170입니다.")
        elif num_sum > 180:
            comments.append("총합계가 매우 높은 편입니다. 일반적 범위는 100~170입니다.")
        else:
            comments.append("총합계가 일반적인 구간(100~170)에 있습니다.")

        if odd_count in (0, 6):
            comments.append("홀/짝이 한쪽으로 쏠린 조합입니다. 출현 확률이 낮습니다.")
        elif odd_count in (1, 5):
            comments.append("홀짝 비율이 5:1 또는 1:5로 비정상적입니다.")
        else:
            comments.append("홀짝 비율이 3:3 또는 4:2로 이상적입니다.")

        if low_count in (0, 6):
            comments.append("모두 낮은 번호 또는 높은 번호입니다. 극단적 패턴입니다.")
        elif low_count in (1, 5):
            comments.append("저/고 비율이 5:1 또는 1:5로 불균형합니다.")
        else:
            comments.append("저/고 비율이 3:3 또는 4:2로 이상적입니다.")

        if consecutive_count >= 3:
            comments.append("연속 번호가 3쌍 이상입니다. 매우 드문 패턴입니다.")
        elif consecutive_count == 0:
            comments.append("연속 번호가 없어 다소 비정상적 패턴입니다.")
        else:
            comments.append("1~2쌍의 연속 번호가 있어 자연스러운 패턴입니다.")

        avg_freq = total_freq / 6
        if avg_freq < 110:
            comments.append("선택된 번호들의 평균 출현 빈도가 낮은 편입니다.")
        elif avg_freq > 140:
            comments.append("선택된 번호들의 평균 출현 빈도가 높은 편입니다.")
        else:
            comments.append("출현 빈도 평균이 적절한 범위입니다.")

        return comments
