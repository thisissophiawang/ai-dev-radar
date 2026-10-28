from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page()
    page.goto('http://127.0.0.1:8000')
    page.locator('.card').first.wait_for()
    page.locator('[data-tab=repo]').click()
    page.locator('#sort').select_option('stars')
    with page.expect_response(lambda r: '/api/items?' in r.url and 'kind=article' in r.url) as info:
        page.locator('[data-tab=article]').click()
    assert 'sort=recent' in info.value.url, info.value.url
    page.route('**/api/items?*',lambda route: route.fulfill(status=500,body='failure'))
    page.locator('[data-tab=saved]').click()
    page.wait_for_timeout(4500)
    assert '请求失败' in page.locator('#notice').inner_text()
    assert page.locator('.card').count()==0
    browser.close()
    print('PASS: tab sort and persistent list failure state')
