from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8000')
    page.locator('[data-tab=repo]').click()
    with page.expect_response(lambda r:'/api/items?' in r.url and 'stage=docs_checked' in r.url):
        page.locator('#stage-filter').select_option('docs_checked')
    page.wait_for_function("document.querySelectorAll('.verification-badge').length===3")
    assert page.locator('.card').count()==3
    assert '最近采集' in page.locator('.card').first.inner_text()
    assert '核查时间' in page.locator('.card').first.inner_text()
    page.get_by_role('button',name='查看 / 更新验证').first.click()
    page.locator('.history-entry').first.wait_for()
    assert 'https://github.com/' in page.locator('#verify-history').inner_text()
    assert page.locator('#verify-version').input_value()
    page.locator('#verify-cancel').click()
    page.screenshot(path='data/verification-desktop.png')
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors,errors
    browser.close()
    print('PASS: 3 reviewed projects, timestamp labels, evidence history, mobile layout, no page errors')
