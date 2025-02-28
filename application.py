import logging.handlers
import os
from urllib.parse import parse_qs

import login  # login.py 모듈 import

# 로깅 설정 (로그 파일 경로 수정)
LOG_FILE = os.path.join(os.path.dirname(__file__), 'sample-app.log')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1048576, backupCount=5)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


login_form = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
</head>
<body>
    <h2>Login</h2>
    <form method="POST" action="/login">
        Username: <input type="text" name="username"><br>
        Password: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
</body>
</html>
"""

welcome_page = """
<!DOCTYPE html>
<html>
<head>
    <title>Welcome</title>
    <style>
    body { font-family: Arial, sans-serif; }
    .logout { float: right; }
    </style>
</head>
<body>
    <h2>Welcome, {username}!</h2>
    <div class="logout"><a href="/logout">Logout</a></div>
    <p>Your first AWS Elastic Beanstalk Python Application is now running...</p>
      <ul>
      <li><a href="http://docs.amazonwebservices.com/elasticbeanstalk/latest/dg/">AWS Elastic Beanstalk overview</a></li>
      <li><a href="http://docs.amazonwebservices.com/elasticbeanstalk/latest/dg/index.html?concepts.html">AWS Elastic Beanstalk concepts</a></li>
      <li><a href="http://docs.amazonwebservices.com/elasticbeanstalk/latest/dg/create_deploy_Python_django.html">Deploy a Django Application to AWS Elastic Beanstalk</a></li>
      <li><a href="http://docs.amazonwebservices.com/elasticbeanstalk/latest/dg/create_deploy_Python_flask.html">Deploy a Flask Application to AWS Elastic Beanstalk</a></li>
      <li><a href="http://docs.amazonwebservices.com/elasticbeanstalk/latest/dg/create_deploy_Python_custom_container.html">Customizing and Configuring a Python Container</a></li>
      <li><a href="http://docs.amazonwebservices.com/elasticbeanstalk/latest/dg/using-features.loggingS3.title.html">Working with Logs</a></li>
      </ul>
</body>
</html>
"""
def application(environ, start_response):
    path = environ['PATH_INFO']
    method = environ['REQUEST_METHOD']
    
    # 세션 쿠키 가져오기
    cookie_string = environ.get('HTTP_COOKIE', '')
    cookies = dict(item.split("=") for item in cookie_string.split("; ") if "=" in item)
    session_id = cookies.get('session_id')
    username = login.get_user_from_session(session_id)

    if path == '/login' and method == 'POST':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size).decode('utf-8')
            form_data = parse_qs(request_body)
            username_form = form_data.get('username', [''])[0]
            password_form = form_data.get('password', [''])[0]
            
            if login.authenticate_user(username_form, password_form):
                session_id = login.create_session(username_form)
                headers = [
                    ("Content-Type", "text/html"),
                    ("Set-Cookie", f"session_id={session_id}; HttpOnly; Path=/") # HttpOnly 설정
                ]
                start_response("302 Found", headers) # 로그인 성공 후 리다이렉션
                return [b""] #리다이렉션은 헤더로 충분
            else:
                response = "Login failed."
                start_response("401 Unauthorized", [("Content-Type", "text/html")])
                return [response.encode('utf-8')]

        except (TypeError, ValueError) as e:
            logger.warning(f'Error during login: {e}')
            start_response("400 Bad Request", [("Content-Type", "text/html")])
            return [b"Invalid request."]

    elif path == '/login':
        start_response("200 OK", [("Content-Type", "text/html")])
        return [login_form.encode('utf-8')]

    elif path == '/logout':
        login.delete_session(session_id)  # 세션 삭제
        headers = [
            ("Content-Type", "text/html"),
            ("Set-Cookie", "session_id=; HttpOnly; Path=/; Max-Age=0")  # 쿠키 삭제
        ]
        start_response("302 Found", headers)
        return [b""]


    elif path == '/scheduled':
        # 스케줄된 작업 처리 (이 예제에서는 로깅만)
        logger.info("Received task %s scheduled at %s", environ['HTTP_X_AWS_SQSD_TASKNAME'],
                    environ['HTTP_X_AWS_SQSD_SCHEDULED_AT'])
        start_response("200 OK", [("Content-Type", "text/html")])
        return [b""]


    else:  # 기본 페이지 (로그인 상태 확인)
        if username:
            response = welcome_page.format(username=username)  # 사용자 이름 표시
            start_response("200 OK", [("Content-Type", "text/html")])
            return [response.encode('utf-8')]
        else:
            start_response("302 Found", [("Location", "/login")]) # 로그인 페이지로 리다이렉션
            return [b""]