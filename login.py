# login.py

import hashlib
import secrets

# 간단한 사용자 데이터베이스 (실제로는 DB 사용)
users = {
    "testuser": {
        "password_hash": hashlib.sha256("testpassword".encode('utf-8')).hexdigest(),
        "salt": "somesalt"  # 간단한 salt. 실제로는 secrets.token_hex() 등으로 생성.
    }
}

sessions = {}  # 세션 저장 (실제로는 Redis, Memcached 등 사용)


def authenticate_user(username, password):
    """사용자 인증"""
    user = users.get(username)
    if user:
        password_hash = hashlib.sha256((password + user["salt"]).encode('utf-8')).hexdigest()
        if password_hash == user["password_hash"]:
            return True
    return False


def create_session(username):
    """세션 생성"""
    session_id = secrets.token_hex(16)  # 안전한 세션 ID 생성
    sessions[session_id] = {"username": username}
    return session_id


def get_user_from_session(session_id):
    """세션 ID로 사용자 정보 가져오기"""
    session = sessions.get(session_id)
    if session:
        return session.get("username")
    return None


def delete_session(session_id):
    """세션 삭제 (로그아웃)"""
    if session_id in sessions:
        del sessions[session_id]