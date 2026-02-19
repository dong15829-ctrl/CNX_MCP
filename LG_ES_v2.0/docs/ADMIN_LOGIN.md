# 관리자 로그인 설정

관리자 계정을 만드는 방법은 **두 가지**입니다.

---

## 1) 서버 최초 실행 시 자동 생성 (권장)

`.env`에 관리자 이메일·비밀번호를 넣어 두면, **admin이 한 명도 없을 때만** 서버 시작 시 자동으로 생성됩니다.

```env
# .env 파일에 추가 (선택)
ADMIN_EMAIL=admin@회사도메인.com
ADMIN_PASSWORD=안전한비밀번호
```

- 이 값을 넣지 않으면 기본값 `admin@example.com` / `admin` 으로 한 번만 생성됩니다.
- **서버를 재시작**한 뒤, 로그인 화면에서 위 이메일과 비밀번호로 로그인하면 됩니다.

---

## 2) 스크립트로 관리자 생성/역할 변경

이미 서버가 돌고 있거나, 나중에 관리자를 추가·변경하고 싶을 때 사용합니다.

**프로젝트 루트**에서:

```bash
# 가상환경 활성화 후
.venv/bin/python scripts/create_admin.py 이메일 비밀번호
```

예:

```bash
.venv/bin/python scripts/create_admin.py admin@company.com MySecurePass123
```

- 해당 이메일 계정이 **없으면** → 새로 만들고 **admin** 역할 부여  
- 해당 이메일 계정이 **이미 있으면** → 역할만 **admin**으로 변경  

인자 없이 실행하면 `.env`의 `ADMIN_EMAIL`, `ADMIN_PASSWORD`를 사용합니다:

```bash
.venv/bin/python scripts/create_admin.py
```

---

## 로그인 방법

1. 브라우저에서 대시보드 로그인 페이지(`/login`)로 이동
2. **아이디**에 **이메일** 입력 (예: `admin@example.com`)
3. **비밀번호** 입력
4. 로그인 후 관리자면 관리자 메뉴(사용자 관리 등)가 보입니다
