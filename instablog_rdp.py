import asyncio
import random
import json
import os
from playwright.async_api import async_playwright

DIRECT_URL = "https://tooliyapooliya.blogspot.com/"
TARGET_DOMAIN = "tooliyapooliya.blogspot.com"
CONCURRENT_TABS = 3

# Host, Port, Username, Password ke saath proxies
PROXIES = [
    {
        "server": "http://v2.proxyapi.eu:8005",
        "username": "HjmrT6g8",
        "password": "jtuFhS5G",
    },
]

def get_random_proxy():
    if not PROXIES:
        return None
    return random.choice(PROXIES)

async def run_tab_automation(p, tab_id, target_url, target_domain):
    tab_name = f"Tab-{tab_id}"
    report = {"tab_name": tab_name, "status": "FAIL"}
    browser = None
    proxy_cfg = get_random_proxy()
    print(f"[{tab_name}] Proxy: {proxy_cfg['server'] if proxy_cfg else 'NONE'}")

    try:
        browser = await p.chromium.launch(
            headless=False,
            proxy=proxy_cfg,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(viewport={"width": 400, "height": 800})
        page = await context.new_page()
        os.makedirs("screenshots", exist_ok=True)

        print(f"[{tab_name}] Direct URL khol raha hoon: {target_url}")
        await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(2, 4))

        try:
            await page.wait_for_url(f"**/{target_domain}**", timeout=15000)
        except Exception:
            if target_domain not in page.url:
                print(f"[{tab_name}] [!] Domain verify nahi hua: {page.url}")
                return report

        print(f"[{tab_name}] Domain verified: {page.url}")
        try:
            await page.screenshot(path=f"screenshots/{tab_name}_blog_success.png", timeout=10000)
        except Exception:
            pass

        wait_time = random.randint(10, 40)
        print(f"[{tab_name}] Scrolling shuru ({wait_time}s)...")
        end_time = asyncio.get_event_loop().time() + wait_time
        while asyncio.get_event_loop().time() < end_time:
            await page.mouse.wheel(0, random.randint(200, 500))
            await asyncio.sleep(random.uniform(2.0, 4.0))

        print(f"[{tab_name}] Banner/Ad click try kar rahe hain...")
        banner_clicked = await page.evaluate("""() => {
            let sels = ['img[src*="banner"]','div[class*="banner"]','div[id*="banner"]','a[href*="ads"]','ins.adsbygoogle','.ad-container','img[alt*="banner"]','div[class*="ads"]','.post-body img','a img'];
            for (let s of sels) { let el = document.querySelector(s); if (el) { el.click(); return true; } }
            return false;
        }""")
        if not banner_clicked:
            for fr in page.frames:
                try:
                    if await fr.evaluate("""() => { let el = document.querySelector('ins.adsbygoogle,a img,.ad-banner,img[src*="banner"],a'); if (el) { el.click(); return true; } return false; }"""):
                        banner_clicked = True
                        break
                except Exception:
                    pass
        print(f"[{tab_name}] Banner clicked: {banner_clicked}")
        report["status"] = "SUCCESS"

    except Exception as e:
        print(f"[{tab_name}] [!] Error: {e}")
        report["error"] = str(e)
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
            print(f"[{tab_name}] Browser closed.\n")

    return report

async def main():
    async with async_playwright() as p:
        run_no = 1
        while True:
            print(f"========== RUN NUMBER {run_no} ==========")
            reports = await asyncio.gather(*[run_tab_automation(p, i+1, DIRECT_URL, TARGET_DOMAIN) for i in range(CONCURRENT_TABS)])
            with open("test_report.json", "w") as f:
                json.dump(reports, f, indent=4)
            run_no += 1
            await asyncio.sleep(random.uniform(5, 10))

if __name__ == "__main__":
    asyncio.run(main())
    
