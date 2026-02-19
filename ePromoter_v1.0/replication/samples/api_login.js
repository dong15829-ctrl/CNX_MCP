/**
 * 로그인 API 호출 샘플 (fetch).
 * Base URL은 환경에 맞게 수정.
 */
var BASE = ''; // 예: 'https://www.globalsess.com/globaldashboard'

function login(userId, userPw) {
  return fetch(BASE + '/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ user_id: userId, user_pw: userPw })
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.ok) {
      if (data.data === 1)
        alert('Data is under processing. You may still access.');
      window.location.href = BASE + '/main';
    } else {
      alert(data.data || 'Login failed');
    }
    return data;
  });
}

// 사용 예:
// login('user@example.com', 'password');
