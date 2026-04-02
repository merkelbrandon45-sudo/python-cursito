from app import app
print('Routes:', [r.rule for r in app.url_map.iter_rules()])
with app.test_client() as c:
    r = c.get('/login/bran')
    print('status', r.status_code)
    print('contains forgot link?', 'forgot-password/bran' in r.get_data(as_text=True))
