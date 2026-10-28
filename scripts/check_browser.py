"""Explicit local browser smoke check; run with the dashboard already started."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.goto('http://127.0.0.1:8000')
    page.locator('.card').first.wait_for()
    page.get_by_role('button',name='＋ 收藏').first.click()
    page.locator('#note').fill('Browser verification: persistent bookmark')
    page.get_by_role('button',name='保存收藏',exact=True).click()
    page.locator('#note-dialog').wait_for(state='hidden')
    page.reload()
    page.locator('[data-tab=saved]').click()
    page.get_by_text('Browser verification: persistent bookmark',exact=True).first.wait_for()
    page.get_by_role('button',name='取消收藏',exact=True).first.click()
    page.get_by_text('还没有收藏。从资讯或项目中留下第一条参考。',exact=True).wait_for()
    page.locator('[data-tab=repo]').click()
    page.locator('.card').first.wait_for()
    query=page.locator('.card h2').first.inner_text()
    page.locator('#search').fill(query)
    page.wait_for_timeout(500)
    assert page.locator('.card').count()>=1
    page.locator('#search').fill('')
    page.wait_for_timeout(500)
    page.locator('[data-tab=article]').click()
    page.locator('.card').first.wait_for()
    Path('data').mkdir(exist_ok=True)
    page.screenshot(path='data/dashboard-desktop.png',full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path='data/dashboard-mobile.png',full_page=True)
    assert not errors,errors
    browser.close()
    print(json.dumps({'bookmark_persistence':True,'search':True,'mobile_no_overflow':True,'page_errors':errors}))
