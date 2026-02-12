from camoufox.sync_api import Camoufox

with Camoufox(headless=False) as browser:
    page = browser.new_page()
    page.goto("https://www.grok.com")
    input("按回车关闭浏览器...")

