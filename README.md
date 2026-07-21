# LOOPICK

안전한 중고거래 플랫폼

## 환경 설정

- Python 3.12 이상
- SQLite
- Git

## 설치 방법

### 1. 저장소 복제

```bash
git clone https://github.com/0xd3funa/tiny-second-hand-shopping-platform.git
cd tiny-second-hand-shopping-platform
```

### 2. 가상환경 생성 및 활성화

Linux 또는 WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. 패키지 설치

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. 환경변수 설정

`.env.example`을 복사하여 `.env` 파일을 만든다.

Linux 또는 WSL:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

안전한 `SECRET_KEY`를 생성한다.

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

출력된 값을 `.env`에 입력한다.

```env
SECRET_KEY=생성한_비밀키
FLASK_DEBUG=false
COOKIE_SECURE=false
```

> 로컬 HTTP 개발 환경에서는 `COOKIE_SECURE=false`를 사용한다.  
> HTTPS로 배포할 때는 `COOKIE_SECURE=true`로 변경한다.

### 5. 데이터베이스 생성

```bash
flask --app run.py db upgrade
```

## 실행 방법

```bash
python run.py
```

브라우저에서 다음 주소로 접속한다.

```text
http://127.0.0.1:5000
```

## 테스트 방법

```bash
pytest -q
```