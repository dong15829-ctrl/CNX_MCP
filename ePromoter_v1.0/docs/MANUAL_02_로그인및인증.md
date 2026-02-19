# 매뉴얼 02: 로그인 및 인증

## 1. 로그인 플로우

```
1. 사용자가 로그인 페이지 접속 (GET /globaldashboard/ 또는 /globaldashboard)
2. 로그인 폼 표시 (ID: #user_id, Password: #user_pw)
3. 사용자가 [Log-in] 클릭 → javascript:login() 호출
4. login() 내부: ajax.post("/login", { user_id, user_pw }, ...)
5. 성공 시: respon.ok === true
   - respon.data === 1 이면 "데이터 처리 중" 안내 alert 후 진행
   - location.href = '/globaldashboard/main'
6. 실패 시: alert(respon.data)
```

## 2. 로그인 API 스펙

### 2.1 요청

| 항목 | 값 |
|------|-----|
| **Method** | POST |
| **URL** | `/globaldashboard/login` 또는 `//login` (상대 경로 시 현재 도메인 기준) |
| **Content-Type** | application/json |
| **Body** | `{ "user_id": "이메일", "user_pw": "비밀번호" }` |

### 2.2 요청 예시 (JSON)

```json
{
  "user_id": "user@example.com",
  "user_pw": "plain_password"
}
```

### 2.3 응답 (가정)

- **성공**: `{ "ok": true, "data": 1 }` 또는 `{ "ok": true }`. `data === 1`이면 데이터 처리 중 안내 문구 표시 후 main으로 이동.
- **실패**: `{ "ok": false, "data": "에러 메시지" }`. `respon.data`를 alert.

## 3. 로그인 폼 HTML (원본 구조)

```html
<form class="login_frm" id="loginForm" name="loginForm" method="post" action="javascript:login()">
    <div class="login_form">
        <div class="ipt_wrap">
            <label for="user_id">아이디</label>
            <input type="email" id="user_id" name="id" placeholder="ID">
        </div>
        <div class="ipt_wrap">
            <label for="user_pw">비밀번호</label>
            <input type="password" id="user_pw" name="user_pw" placeholder="Password">
        </div>
        <span class="warn_msg"></span>
    </div>
    <a href="javascript:login()" class="login_btn_img">
        <img src="img/login_02.png" alt="Log-in">
    </a>
</form>
```

- **ID 필드**: `#user_id`, `name="id"`, `type="email"`
- **비밀번호 필드**: `#user_pw`, `name="user_pw"`, `type="password"`
- **제출**: `login()` 함수에서 `$('#user_id').val()`, `$('#user_pw').val()`로 읽어 ajax.post 호출.

## 4. 인증 유지

- 로그인 성공 후 서버에서 **세션 쿠키**를 설정하고, 이후 모든 API 요청 시 해당 쿠키가 자동으로 전송되는 구조로 추정됩니다.
- 재현 시: 백엔드에서 세션 쿠키 또는 JWT 등 동일한 방식으로 인증을 유지하고, fetch/axios 사용 시 `credentials: 'include'` 등으로 쿠키를 포함해야 합니다.

## 5. 샘플 코드 위치

- `replication/samples/api_login.js` — fetch 기반 로그인 예시
- `replication/schemas/request_login.json` — 요청 body 예시
