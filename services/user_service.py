import bcrypt
from db.user_account import UserAccountDB

class UserService:
    @staticmethod
    def signup(username, password):
        # 중복 확인
        existing = UserAccountDB.get_user_by_username(username)
        if existing:
            return False, "❌ 이미 존재하는 사용자입니다."

        # 비밀번호 해시 생성
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # DB 삽입
        created = UserAccountDB.create_user(username, password_hash)

        if created:
            return True, "✅ 회원가입 성공!"
        else:
            return False, "❌ 회원가입 실패(DB 오류)"

    @staticmethod
    def login(username, password):
        user_tuple = UserAccountDB.get_user_by_username(username) # (user_id, username, stored_password_hash, status) 튜플 반환

        if not user_tuple:
            return False, "❌ 사용자를 찾을 수 없습니다.", None 

        user_id, uname, stored_password_hash, status = user_tuple # 튜플 언패킹
        
        # 비밀번호 검증
        if bcrypt.checkpw(password.encode(), stored_password_hash.encode()):
            # 로그인 성공 시: 딕셔너리 형태로 반환하여 app.py에서 키 접근 가능하도록 함
            user_data = {
                'user_id': user_id, 
                'username': uname,
                'status': status
            }
            return True, f"✅ 로그인 성공! {uname}님 환영합니다.", user_data
        else:
            return False, "❌ 비밀번호가 일치하지 않습니다.", None