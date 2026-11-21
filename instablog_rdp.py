import asyncio
import random
import json
import os
from playwright.async_api import async_playwright

TARGET_REDIRECT_URL = "https://l.instagram.com/?u=https%3A%2F%2Ftooliyapooliya.blogspot.com%2F%3Ffbclid%3DPAT01DUAVuHnlleHRuA2FlbQIxMABwZG9mAnNydGMGYXBwX2lkDzU2NzA2NzM0MzM1MjQyNwABp94y9LB2FxI7iYuvqlrLdFsZ_4Gc8Rm_RJ_iRrgXZrOl8lBLSGuV5Q5gDyuU_aem_dk6ur67larzQ_tD7tvPcFw&e=AUAv1NYG3bRqEflm_DkdDRUQhfMPNa6EdVE3bjW0nBE3uztni7DV02X8P1HtjHi9sqa2uLCwf8phYCdLURUj9yVuRO5UDUD-0AHd9jSTMGyAjFW8Dr53gDzc4Q&s=1"
TARGET_DOMAIN = "tooliyapooliya.blogspot.com"
CONCURRENT_TABS = 3

# Proxy Poland credentials (HTTP 8005 aur SOCKS5 5005)
PROXY_LIST = [
    "http://HjmrT6g8:jtuFhS5G@v2.proxyapi.eu:8005",
    "socks5://HjmrT6g8:jtuFhS5G@v2.proxyapi.eu:5005",
]

def get_random_proxy():
    if not PROXY_LIST:
        return None
    proxy_url = random.choice(PROXY_LIST).strip()
    return {"server": proxy_url}

async def run_tab_automation(p, tab_id, target_url, target_domain):
    tab_name = f"Tab-{tab_id}"
    report = {"tab_name": tab_name, "status": "FAIL", "steps_passed": []}

    browser = None
    proxy_cfg = get_random_proxy()
    if proxy_cfg:
        print(f"[{tab_name}] Proxy selected: {proxy_cfg['server']}")
    else:
        print(f"[{tab_name}] Bina proxy ke direct launch ho raha hai...")

    try:
        browser = await p.chromium.launch(
            headless=False,
            proxy=proxy_cfg,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(viewport={"width": 400, "height": 800})
        page = await context.new_page()

        os.makedirs("screenshots", exist_ok=True)

        # 1. Instagram redirect link open
        print(f"[{tab_name}] Instagram redirect link khol raha hoon...")
        await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(2, 4))

        # 2 & 3. Direct blog ya warning page check -> fixed coordinate click
        if target_domain not in page.url:
            print(f"[{tab_name}] Warning page detect hua, fixed coordinate (X: 200, Y: 480) par click kar rahe hain...")
            await page.mouse.click(200, 480)
            await asyncio.sleep(4)

        # 4. Domain verify
        try:
            await page.wait_for_url(f"**/{target_domain}**", timeout=15000)
            print(f"[{tab_name}] Domain verified! Blog open hai: {page.url}")
        except Exception:
            if target_domain not in page.url:
                print(f"[{tab_name}] [!] Blog domain verify nahi hua. Current URL: {page.url}")
                report["error"] = "Domain verification failed"
                return report

        try:
            await page.screenshot(path=f"screenshots/{tab_name}_blog_success.png", timeout=10000)
        except Exception:
            pass

        # 5. Human scrolling & reading wait
        wait_time = random.randint(10, 40)
        print(f"[{tab_name}] Human behaviour shuru ({wait_time}s scrolling)...")
        end_time = asyncio.get_event_loop().time() + wait_time
        while asyncio.get_event_loop().time() < end_time:
            scroll_amount = random.randint(200, 500)
            await page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(2.0, 4.0))

        # 6. Banner / Ad click (main page + iframes)
        print(f"[{tab_name}] Banner ya Ad par click karne ki koshish...")
        banner_clicked = False
        try:
            banner_clicked = await page.evaluate("""() => {
                let selectors = [
                    'img[src*="banner"]', 'div[class*="banner"]', 'div[id*="banner"]',
                    'a[href*="ads"]', 'ins.adsbygoogle', '.ad-container', 'img[alt*="banner"]',
                    'div[class*="ads"]', '.post-body img', 'a img'
                ];
                for (let sel of selectors) {
                    let el = document.querySelector(sel);
                    if (el) {
                        el.click();
                        return true;
                    }
                }
                return false;
            }""")

            if not banner_clicked:
                for frame in page.frames:
                    try:
                        clicked_in_frame = await frame.evaluate("""() => {
                            let adEl = document.querySelector('ins.adsbygoogle, a img, .ad-banner, img[src*="banner"], a');
                            if (adEl) {
                                adEl.click();
                                return true;
                            }
                            return false;
                        }""")
                        if clicked_in_frame:
                            banner_clicked = True
                            break
                    except Exception:
                        pass

            if banner_clicked:
                print(f"[{tab_name}] Banner/Ad par click ho gaya!")
                await asyncio.sleep(3)
            else:
                print(f"[{tab_name}] Koi banner click nahi hua.")
        except Exception as e:
            print(f"[{tab_name}] Banner click error: {e}")

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
        loop_count = 1
        while True:
            print(f"========== RUN NUMBER {loop_count} ==========")
            tasks = [run_tab_automation(p, i + 1, TARGET_REDIRECT_URL, TARGET_DOMAIN) for i in range(CONCURRENT_TABS)]
            all_reports = await asyncio.gather(*tasks)

            with open("test_report.json", "w") as f:
                json.dump(all_reports, f, indent=4)

            print(f"[*] Run {loop_count} pura hua...\n")
            loop_count += 1
            await asyncio.sleep(random.uniform(5, 10))

if __name__ == "__main__":
    asyncio.run(main())
