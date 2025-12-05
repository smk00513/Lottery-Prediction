# app.py
from flask import Flask, render_template, request, redirect, session, url_for, flash
from dotenv import load_dotenv
import os
from functools import wraps 

# 환경 변수 로드 (.env 파일에 SECRET_KEY, DB 정보 등이 있어야 합니다)
load_dotenv() 

# 서비스 레이어에서 비즈니스 로직과 DB 접근을 처리합니다.
from services.user_service import UserService 
from services.lotto_service import LottoService
from services.stat_service import StatService
from services.recommend_service import RecommendService

app = Flask(__name__)
# 세션 관리를 위한 SECRET_KEY 설정
secret_key = os.getenv("SECRET_KEY")

if not secret_key or len(secret_key) < 16:
    print("🚨 FATAL ERROR: SECRET_KEY 환경 변수가 정의되지 않았거나 너무 짧습니다. .env 파일을 확인해 주세요.")
    app.secret_key = "a_temporary_fallback_secret_key_1234567890_long_enough"
else:
    app.secret_key = secret_key

# =========================
# 0. 유틸리티 및 데코레이터
# =========================
def login_required(f):
    """로그인 상태를 확인하는 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("❌ 로그인이 필요한 서비스입니다.", 'warning')
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def get_ball_color_class(number):
    """
    로또 번호에 따라 색상 클래스를 반환하는 파이썬 함수.
    (1-10: ball-1, 11-20: ball-2, 21-30: ball-3, 31-40: ball-4, 41-45: ball-5)
    """
    try:
        num = int(number)
    except ValueError:
        return '' 

    if 1 <= num <= 10:
        return 'ball-1'
    elif 11 <= num <= 20:
        return 'ball-2'
    elif 21 <= num <= 30:
        return 'ball-3'
    elif 31 <= num <= 40:
        return 'ball-4'
    elif 41 <= num <= 45:
        return 'ball-5'
    return '' 

@app.context_processor
def utility_processor():
    # 'getBallColorClass' 이름으로 위 함수를 Jinja 템플릿에 등록
    return dict(getBallColorClass=get_ball_color_class)

# =========================
# 1. 메인페이지
# =========================
@app.route("/")
def index():
    # index.html에서 session 정보를 사용하여 환영 메시지를 표시합니다.
    return render_template("index.html", title="홈")


# =========================
# 2. 회원가입 (UserService 호출)
# =========================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # UserService에 구현된 로직 호출 (중복 확인, bcrypt 해싱, DB 저장 모두 처리)
        success, message = UserService.signup(username, password)
        
        if success:
            flash(message, 'success')
            return redirect(url_for("login"))
        else:
            flash(message, 'error')
            return redirect(url_for("signup"))
    
    return render_template("signup.html", title="회원가입")


# =========================
# 3. 로그인 (UserService 호출 및 Authorization 기반 마련)
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        success, message, user_data = UserService.login(username, password)
        
        if success:
            # ⭐ 로그인 성공: 세션에 사용자 정보 저장 ⭐
            session['user_id'] = user_data['user_id']
            session['username'] = user_data['username']
            
            # 💡 status 필드를 공백 제거 및 소문자 변환 후 'admin'과 비교하여 안정성을 높입니다.
            sanitized_status = user_data['status'].strip().lower()
            # [FIX 1] 'status' 정보도 세션에 저장하여 mypage 등에서 사용할 수 있게 합니다.
            session['status'] = sanitized_status
            session['is_admin'] = sanitized_status == 'admin' # 저장된 status로 isAdmin 설정
            flash(f"✅ {user_data['username']}님 환영합니다!", 'success')
            return redirect(url_for("index"))
        else:
            flash(message, 'error')
            return redirect(url_for("login"))
            
    return render_template("login.html", title="로그인")

# =========================
# 4. 로그아웃
# =========================
@app.route("/logout")
def logout():
    session.clear()
    flash("👋 로그아웃되었습니다.", 'info')
    return redirect(url_for("index"))


# =========================
# 5. 마이페이지 (권한 보호 예시)
# =========================
@app.route("/mypage")
@login_required 
def mypage():
    # 세션에서 가져온 username과 status 정보를 템플릿에 전달합니다.
    return render_template("mypage.html", 
                           title="마이페이지", 
                           username=session["username"], 
                           status=session.get("status", "active"))


# =========================
# 6. Lotto Data (당첨 데이터 조회 - LOTTO_DRAW)
# =========================
@app.route("/lotto")
def lotto_data():
    # 당첨 데이터 조회는 로그인 없이도 가능하도록 처리
    
    page = request.args.get('page', 1, type=int)
    per_page = 20 # 한 페이지에 표시할 데이터 수

    # LottoService를 통해 페이징된 데이터 가져오기 (SFW, ORDER BY, LIMIT 적용)
    data = LottoService.get_paginated_draws(page, per_page)
    
    # lotto_data.html 템플릿은 별도로 생성해야 합니다.
    return render_template("lotto_data.html", 
                           title="당첨 번호 조회",
                           data=data)


# =========================
# 7. 내 번호 목록 조회 (My Picks)
# =========================
@app.route("/my-picks")
@login_required 
def my_picks():
    user_id = session.get("user_id")
    
    # DB에서 해당 user_id의 모든 선택 번호를 조회합니다.
    picks = LottoService.get_user_picks(user_id) 
    
    # 템플릿에 조회된 picks 데이터를 전달합니다.
    return render_template("my_picks.html", title="내 번호 목록", picks=picks)


# =========================
# 7-A. 번호 분석 (Check Pick) ⭐ 추가된 라우트 ⭐
# =========================
@app.route('/check-pick', methods=['GET', 'POST'])
@login_required 
def check_pick():
    analysis_result = None
    form_data = {} # 폼 데이터 유지를 위한 딕셔너리

    if request.method == 'POST':
        # 1. 폼 데이터 수집 및 정제
        try:
            numbers = []
            for i in range(1, 7):
                key = f'number_{i}'
                num_str = request.form.get(key)
                
                # 입력 값이 없으면 에러
                if not num_str:
                    flash(f"❌ {i}번째 번호를 입력해주세요.", 'error')
                    return redirect(url_for("check_pick"))
                
                num = int(num_str)
                numbers.append(num)
                form_data[key] = num_str # 폼 데이터 유지
                
        except ValueError:
            flash("❌ 번호는 정수(숫자)만 입력해야 합니다.", 'error')
            return redirect(url_for("check_pick"))

        # 2. 유효성 검사 (1~45 범위, 6개, 중복 없음)
        is_valid = True
        if not all(1 <= n <= 45 for n in numbers):
            flash("❌ 로또 번호는 1부터 45 사이여야 합니다.", 'error')
            is_valid = False
        elif len(set(numbers)) != 6:
            # 중복된 번호는 서버 측에서 제거하지 않고 오류 메시지만 표시
            flash("❌ 로또 번호는 중복될 수 없습니다. 중복된 번호가 입력되었습니다.", 'error')
            is_valid = False
        
        if is_valid:
            # 3. 분석 서비스 호출
            analysis_result = LottoService.analyze_pick(numbers)
            
            if "error" in analysis_result:
                # 서비스에서 통계 데이터 없음 등의 오류가 발생한 경우
                print(f"LottoService Analysis Error: {analysis_result['error']}")
                flash(f"❌ 분석 오류: {analysis_result['error']}", 'error')
                analysis_result = None
            else:
                flash("✅ 로또 번호 분석이 완료되었습니다.", 'success')
                # 분석 성공 시 폼 데이터 초기화
                form_data = {} 
        
    # GET 요청이거나 POST 요청 후 결과를 렌더링할 때
    return render_template(
        "check_pick.html", 
        title="번호 분석", 
        analysis_result=analysis_result,
        form_data=form_data # 폼 유지를 위해 전달
    )


# =========================
# 8. 통계 조회 (Statistics) 
# =========================
@app.route('/statistics')
def statistics_page():
    # 1. 정렬 기준 및 순서 파라미터 읽기 (기본값: frequency 내림차순)
    sort_by = request.args.get('sort', 'frequency')
    sort_order = request.args.get('order', 'desc')
    reverse_flag = sort_order == 'desc'

    # 2. StatService를 통해 LOTTO_STAT 테이블의 모든 통계 데이터를 조회합니다.
    stats = StatService.get_all_stats() 
    
    # 3. Python 로직을 사용하여 데이터 정렬
    try:
        # last_draw_gap에 None이 있을 경우, -1로 처리하여 가장 낮은 값으로 둡니다.
        if sort_by == 'last_draw_gap':
            stats.sort(key=lambda x: x.get(sort_by) if x.get(sort_by) is not None else -1, reverse=reverse_flag)
        else:
            # frequency나 number는 None이 없으므로 단순 키 정렬
            stats.sort(key=lambda x: x[sort_by], reverse=reverse_flag)
            
    except KeyError:
        # 잘못된 정렬 기준이 들어왔을 경우 기본값(frequency 내림차순)으로 재정렬
        stats.sort(key=lambda x: x['frequency'], reverse=True)
        flash("유효하지 않은 정렬 기준입니다. 기본 정렬(출현 횟수 내림차순)으로 표시됩니다.", 'warning')

    # 정렬된 데이터를 템플릿에 전달합니다.
    return render_template('statistics.html', title="번호 통계", stats=stats)


# =========================
# 9. 통계 갱신 (Admin Authorization 적용)
# =========================
@app.route('/admin/update_stats', methods=['POST'])
# @login_required # 필요하다면 추가
def update_statistics_route():
    # 1. 로그인 및 관리자 권한 확인 (중요: POST 요청에도 반드시 권한 체크 필요)
    if not session.get('is_admin'):
        flash("❌ 접근 거부: 관리자 권한이 필요합니다.", 'error')
        return redirect(url_for('mypage')) 

    # 통계 갱신 실행 
    success, msg = StatService.update_statistics()

    if success:
        # ⭐ 신규 기능: 통계 갱신 성공 시, 추천 시스템을 위한 VIEW도 갱신합니다. ⭐
        # RecommendService를 import했는지 확인 (app.py 상단에 from services.recommend_service import RecommendService)
        from services.recommend_service import RecommendService
        RecommendService.create_recommend_view_only()
        
        flash(f"✅ 통계 데이터 갱신 성공 및 추천 VIEW 갱신 완료: {msg}", 'success')
    else:
        flash(f"❌ 통계 데이터 갱신 실패: {msg}", 'error')

    # 사용자가 원래 사용하던 라우트로 리다이렉트
    return redirect(url_for('admin_stats_management'))    
    
# =========================
# 9-A. 관리자 통계 관리 페이지 (Admin Stats Management)
# =========================
@app.route('/admin/stats_management')
# @login_required # 필요하다면 추가
def admin_stats_management():
    # [Authorization 체크]: 관리자(admin)가 아니면 접근 거부 
    if not session.get('is_admin'): 
        flash("❌ 접근 거부: 관리자 권한이 필요합니다.", 'error')
        return redirect(url_for('index'))
    
    # ⭐ 통계 개수를 조회하여 템플릿에 전달하는 로직 추가 ⭐
    # StatService를 import했는지 확인 (app.py 상단에 from services.stat_service import StatService)
    stats = StatService.get_all_stats()
    stats_count = len(stats)

    # 관리자 페이지 템플릿을 렌더링합니다.
    return render_template(
        'admin_stats.html', 
        title="관리자 - 통계 관리",
        stats_count=stats_count # 템플릿에 통계 개수 전달
    )
    

# =========================
# 10. 번호 삭제 (DELETE)
# =========================
@app.route("/my-picks/delete/<int:id>", methods=["POST"])
@login_required
def delete_pick(id):
    user_id = session["user_id"]
    
    # LottoService.delete_pick 호출
    success, message = LottoService.delete_pick(id, user_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
        
    return redirect(url_for("my_picks"))


# =========================
# 11. 번호 추천 (Recommendation)
# =========================
@app.route('/recommend', methods=['GET'])
@login_required 
def recommend_page():
    user_id = session.get('user_id') 
    
    # 추천 로직 실행 (개인화 추천을 위해 user_id 전달)
    success, recommended_numbers, detailed_stats = RecommendService.generate_recommendation(user_id) 
    
    # 디버깅 정보 추가: 추천 실패 시 서버 로그 출력
    if not success:
        print(f"Recommend Service Error: {recommended_numbers}")
        flash(f"❌ 번호 추천에 실패했습니다: {recommended_numbers}", 'error')
    
    # 템플릿 렌더링
    return render_template(
        'recommend.html', 
        title="번호 추천",
        is_success=success,
        recommended_numbers=recommended_numbers, 
        detailed_stats=detailed_stats
    )


# =========================
# 12. 추천 번호 저장 (INSERT)
# =========================
@app.route('/save_pick', methods=['POST'])
@login_required 
def save_recommended_pick():
    user_id = session.get('user_id')
    
    # POST 요청에서 번호 6개를 추출
    try:
        numbers = []
        for i in range(1, 7):
            num_str = request.form.get(f'number_{i}')
            if not num_str:
                raise ValueError("필수 번호가 누락되었습니다.")
            numbers.append(int(num_str))
        
    except (ValueError, TypeError) as e:
        # 번호가 없거나 유효한 정수가 아닌 경우
        print(f"Save Pick Error: {e}")
        flash("❌ 번호 저장 실패: 유효하지 않은 번호 형식입니다. 다시 시도해 주세요.", 'error')
        return redirect(url_for('recommend_page'))

    # 서비스 레이어 호출 및 유효성 검사/DB 저장
    success, message = LottoService.save_user_pick(user_id, numbers)

    if success:
        flash("✅ 로또 번호가 나의 목록에 성공적으로 저장되었습니다.", 'success')
        return redirect(url_for('my_picks'))
    else:
        # message는 실패 이유를 담고 있습니다.
        flash(f"❌ 번호 저장 실패: {message}", 'error')
        return redirect(url_for('recommend_page'))
    
    
    
# =========================
# 13. 직접 선택 번호 분석 (GET/POST)
# =========================
@app.route('/check_pick', methods=['GET', 'POST'])
@login_required 
def check_pick_analysis_route():
    # 1. GET: 세션에서 이전 분석 결과를 안전하게 가져옵니다.
    comments = session.pop('analysis_comments', None)
    detailed_stats = session.pop('analysis_detailed_stats', None)
    input_numbers = session.pop('analysis_input_numbers', None)
    history_analysis_results = session.pop('analysis_history_analysis_results', None)
    
    # total_score 처리 로직 (이전 TypeError 방지 로직)
    total_score = session.pop('analysis_total_score', None)
    if total_score is not None:
        try:
            total_score = float(total_score)
        except (ValueError, TypeError):
            total_score = 0.0

    # 2. POST 요청: 분석 실행
    if request.method == 'POST':
        try:
            numbers = []
            
            # 번호 유효성 검사 및 파싱
            for i in range(1, 7):
                num_str = request.form.get(f'number_{i}')
                if not num_str or num_str.strip() == '':
                    raise ValueError("6개의 로또 번호를 모두 입력해야 합니다.")
                num = int(num_str.strip())
                
                if not 1 <= num <= 45:
                    raise ValueError("로또 번호는 1부터 45 사이여야 합니다.")
                numbers.append(num)

            if len(set(numbers)) != 6:
                raise ValueError("중복된 번호가 있습니다. 6개의 고유한 번호를 입력하세요.")

            input_numbers = sorted(numbers) 
            
            # 2. 서비스 레이어 호출하여 분석 수행
            # LottoService.check_pick_analysis는 comments(list)와 detailed_stats(list of tuples)를 반환해야 합니다.
            history_analysis_results, comments, detailed_stats = LottoService.check_pick_analysis(input_numbers) #

            # 3. total_score 계산 (템플릿에 전달할 전체 점수 합계)
            current_total_score = None
            if detailed_stats:
                # detailed_stats의 두 번째 요소(인덱스 1)가 total_score라고 가정하고 합산합니다.
                # (detailed_stats 구조: [(number, total_score, frequency, last_draw_gap), ...])
                current_total_score = sum(stat[1] for stat in detailed_stats if isinstance(stat, (list, tuple)) and len(stat) > 1 and isinstance(stat[1], (int, float)))

            
            # 4. 분석 결과를 세션에 저장 ⭐이 부분이 누락되었을 가능성이 높습니다.⭐
            session['analysis_comments'] = comments
            session['analysis_detailed_stats'] = detailed_stats
            session['analysis_input_numbers'] = input_numbers
            session['analysis_total_score'] = current_total_score # float 또는 None

            flash("✅ 입력하신 번호의 통계 분석이 완료되었습니다.", 'success') #
            
            # 5. GET 요청으로 리다이렉트 (PRG 패턴)
            return redirect(url_for('check_pick_analysis_route'))

        except ValueError as e:
            flash(f"❌ 번호 입력 오류: {e}", 'error')
            return redirect(url_for('check_pick_analysis_route'))
        except Exception as e:
            print(f"Analysis Error: {e}")
            flash("❌ 분석 중 예상치 못한 오류가 발생했습니다. (서버 콘솔 확인)", 'error')
            return redirect(url_for('check_pick_analysis_route'))

    # 3. GET: 템플릿 렌더링
    # 세션에서 가져온 결과를 템플릿에 전달합니다.
    return render_template(
        'check_pick.html', 
        title="내 번호 통계 분석",
        input_numbers=input_numbers, 
        comments=comments,           
        detailed_stats=detailed_stats,
        history_analysis_results=history_analysis_results,       
        total_score=total_score # float 또는 None
    )
        
    
if __name__ == "__main__":
    app.run(debug=True)