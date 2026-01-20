import requests
s = requests.Session()
login_url = 'http://127.0.0.1:5000/login'
# fetch login page to get session cookie
r = s.get(login_url, timeout=5)
print('GET /login', r.status_code)
resp = s.post(login_url, data={'username':'admin','password':'123456'}, allow_redirects=False, timeout=5)
print('POST /login status', resp.status_code)
if resp.status_code in (302, 303):
    print('Login likely successful, redirected to', resp.headers.get('Location'))
else:
    # print snippet
    print('Response text:\n', resp.text[:800])
