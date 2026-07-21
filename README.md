# tiny-second-hand-shopping-platform
[WHS4]_정은아(7624) 

# LOOPICK

> 아직 좋은 물건을 다시 고르는 안전한 중고거래 플랫폼

LOOPICK은 사용자가 상품을 등록하고 검색하며, 다른 사용자와 채팅하고 가상 잔액을 송금할 수 있는 Flask 기반 중고거래 웹 애플리케이션입니다.

신고 누적에 따른 사용자·상품 차단과 관리자 관리 기능을 제공하며, 개발 과정에서 입력 검증과 접근 통제 등 시큐어 코딩 원칙을 적용했습니다.

## 주요 기능

### 회원 기능

- 회원가입
- 로그인 및 로그아웃
- 프로필 조회·수정
- 비밀번호 변경
- 비밀번호 scrypt 해시 저장
- 정상·휴면 계정 상태 관리

### 상품 기능

- 상품 등록
- 상품 이미지 업로드
- 상품 목록 및 상세 조회
- 상품 검색
- 상품 수정 및 삭제
- 판매 중·예약 중·판매 완료 상태 변경
- 사용자별 등록 상품 조회

### 채팅 기능

- 전체 공개 채팅
- 사용자 간 1:1 채팅
- 최근 메시지 조회
- 관리자 메시지 관리

### 신고 기능

- 사용자 신고
- 상품 신고
- 자기 신고 방지
- 동일 대상 중복 신고 방지
- 신고 누적 시 사용자 자동 휴면 처리
- 신고 누적 시 상품 자동 차단
- 관리자 신고 승인 및 기각

### 송금 기능

- 사용자 간 가상 잔액 송금
- 송금 내역 조회
- 자기 송금 방지
- 잔액 부족 송금 방지
- 휴면 사용자 송금 방지
- 트랜잭션 기반 잔액 변경

### 관리자 기능

- 관리자 전용 대시보드
- 사용자 정상·휴면 상태 관리
- 상품 차단 및 복구
- 신고 검토 및 처리
- 채팅 기록 조회·삭제
- 송금 기록 조회
- 일반 사용자의 관리자 페이지 접근 차단

## 기술 스택

- Python 3.12
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login
- Flask-WTF
- Flask-Limiter
- Flask-SocketIO
- SQLite
- Pillow
- pytest
- HTML
- CSS
- Jinja2

## 프로젝트 구조

```text
tiny-second-hand-shopping-platform/
├── app/
│   ├── admin/          # 관리자 기능
│   ├── auth/           # 인증 및 사용자 기능
│   ├── chat/           # 전체 및 1:1 채팅
│   ├── main/           # 메인 화면과 상품 검색
│   ├── products/       # 상품 관리
│   ├── reports/        # 신고 기능
│   ├── transfers/      # 가상 잔액 송금
│   ├── static/         # CSS 및 정적 파일
│   ├── templates/      # Jinja2 템플릿
│   ├── extensions.py   # Flask 확장 객체
│   └── models.py       # 데이터베이스 모델
├── migrations/         # Alembic DB 마이그레이션
├── tests/              # pytest 자동 테스트
├── uploads/            # 업로드 이미지 저장 폴더
├── config.py           # 애플리케이션 설정
├── run.py              # 실행 진입점
├── pytest.ini          # pytest 설정
├── requirements.txt    # Python 의존성
├── .env.example        # 환경변수 예시
└── README.md
```

## 실행 환경

다음 환경에서 개발하고 테스트했습니다.

- Ubuntu on WSL
- Python 3.12.3
- SQLite
- 최신 Chromium 기반 브라우저

## 설치 및 실행

### 1. 저장소 복제

```bash
git clone https://github.com/0xd3funa/tiny-second-hand-shopping-platform.git
cd tiny-second-hand-shopping-platform
```

### 2. 가상환경 생성

```bash
python3 -m venv .venv
```

가상환경 활성화:

```bash
source .venv/bin/activate
```

Windows PowerShell을 사용하는 경우:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. 패키지 설치

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. 환경변수 파일 생성

`.env.example`을 복사하여 `.env` 파일을 생성합니다.

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

안전한 `SECRET_KEY` 생성:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

출력된 값을 `.env`에 설정합니다.

```env
SECRET_KEY=생성한_랜덤_문자열
FLASK_DEBUG=false
COOKIE_SECURE=false
```

로컬 HTTP 개발 환경에서는 `COOKIE_SECURE=false`를 사용합니다.

HTTPS 배포 환경에서는 반드시 다음과 같이 변경해야 합니다.

```env
COOKIE_SECURE=true
```

`.env` 파일에는 비밀 정보가 포함되므로 Git에 커밋하지 않습니다.

### 5. 데이터베이스 생성 및 마이그레이션

```bash
flask --app run.py db upgrade
```

SQLite 데이터베이스는 실행 과정에서 `instance/` 폴더에 생성됩니다.

### 6. 애플리케이션 실행

```bash
python run.py
```

브라우저에서 다음 주소로 접속합니다.

```text
http://127.0.0.1:5000
```

개발 서버는 로컬 개발과 테스트 목적으로만 사용해야 합니다.

## 관리자 계정 설정

일반 회원가입으로는 관리자 권한을 획득할 수 없습니다.

먼저 웹사이트에서 관리자용 계정을 일반 회원으로 생성한 뒤 Flask 셸을 실행합니다.

```bash
flask --app run.py shell
```

셸 안에서 다음 명령을 실행합니다.

```python
from app.extensions import db
from app.models import User

admin_user = db.session.scalar(
    db.select(User).where(
        User.username == "관리자로_지정할_아이디"
    )
)

admin_user.role = "admin"
db.session.commit()

print(admin_user.username, admin_user.role)
exit()
```

관리자 계정으로 다시 로그인하면 상단 메뉴에 `관리자` 버튼이 표시됩니다.

## 테스트 실행

전체 자동 테스트:

```bash
pytest -q
```

또는:

```bash
python -m pytest -q
```

현재 자동 테스트에서는 다음 항목을 검사합니다.

- 비밀번호 해시 저장
- 일반 사용자의 관리자 페이지 접근 차단
- 관리자의 관리자 페이지 접근 허용
- 정상 송금과 양쪽 잔액 변경
- 잔액 부족 송금 차단
- 자기 송금 차단
- 채팅 메시지 XSS 이스케이프

예상 결과:

```text
7 passed
```

## 적용한 주요 보안 대책

### 인증 및 비밀번호

- 비밀번호 원문을 저장하지 않고 scrypt 해시 저장
- 로그인 성공 전 기존 세션 제거
- 세션 유효시간 제한
- HttpOnly 및 SameSite 쿠키 설정
- 휴면 계정의 기존 로그인 세션 강제 종료

### 접근 통제

- 상품 수정·삭제 시 소유자 또는 관리자 권한 검사
- 관리자 경로에 별도 관리자 권한 decorator 적용
- 1:1 채팅 참여 사용자만 대화 조회
- 차단 상품의 비인가 조회 제한
- 관리자 자신의 계정 상태 변경 방지

### 입력값 및 요청 검증

- Flask-WTF를 통한 서버 측 입력 검증
- 모든 상태 변경 요청에 POST 사용
- CSRF 토큰 검증
- SQLAlchemy ORM을 통한 SQL Injection 방어
- Jinja2 자동 이스케이프를 통한 XSS 방어
- 로그인, 회원가입, 신고, 송금 및 채팅 요청 횟수 제한
- 외부 URL 리다이렉트를 차단하여 Open Redirect 방지

### 이미지 업로드

- 업로드 요청 크기 제한
- 허용 이미지 형식 제한
- Pillow를 이용한 실제 이미지 검증
- 이미지 재인코딩을 통한 메타데이터 제거
- UUID 기반 서버 파일명 생성
- 이미지 픽셀 수 제한
- DB 저장 실패 시 고아 이미지 삭제

### 데이터베이스 및 송금

- Foreign Key 활성화
- Check Constraint로 상태 및 금액 범위 제한
- Unique Constraint로 중복 신고 방지
- 송금액 범위 제한
- 조건부 UPDATE를 이용한 잔액 음수 방지
- 잔액 차감·증가·송금 기록을 하나의 트랜잭션으로 처리
- 송금 기록을 감사 목적으로 보존

### HTTP 보안 헤더

다음 보안 헤더를 응답에 적용합니다.

- Content-Security-Policy
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy

## 데이터 및 업로드 파일

다음 파일은 실행 중 생성되는 데이터이므로 Git으로 관리하지 않습니다.

```text
.env
.venv/
instance/
uploads/
__pycache__/
.pytest_cache/
```

실제 개인정보나 비밀키를 저장소에 커밋하지 않도록 주의해야 합니다.

## 유지보수 계획

- 의존성 보안 업데이트 정기 적용
- 업로드 파일과 데이터베이스 정기 백업
- 관리자 작업 로그 기능 추가 검토
- 신고 기준과 자동 차단 임계치 정기 검토
- 운영 환경에서 HTTPS와 Secure Cookie 강제
- 운영용 WSGI 서버와 외부 DB 도입
- 테스트 범위 지속 확대
- 오래된 채팅 및 업로드 파일 보존 정책 수립

## 보고서

개발 과정 보고서는 요구사항 분석, 시스템 설계, 구현 과정, 테스트 체크리스트, 보안 약점 및 개선 사항, 유지보수 계획을 포함하여 별도의 PDF로 제출합니다.

최종 제출 전에 이 위치에 PDF 보고서 링크를 추가할 예정입니다.

## 저장소

- GitHub: https://github.com/0xd3funa/tiny-second-hand-shopping-platform