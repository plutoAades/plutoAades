# -*- coding: utf-8 -*-
"""
dangdang_proxy_crawl_multi_parallel.py

功能：
- 多分类、多窗口并行抓取商品列表页（Selenium）
- requests + 免费代理池下载详情页与图片（多线程）
- 支持翻页抓取（pg2-cidXXXX.html 等）
- 随机延时，降低被风控风险
"""

import requests
from bs4 import BeautifulSoup
import time, random, os, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ----------------- 配置 -----------------
CHROME_DRIVER = r"D:\Tools\chromedriver\chromedriver.exe"   # 指定chromedriver 路径
CATEGORIES = {
    "食品": ("https://category.dangdang.com/cid4002145.html", 20),
    "家电": ("https://category.dangdang.com/cid4001001.html", 20),
    "家具": ("https://category.dangdang.com/cid4010897.html", 20),
}
OUTPUT_JSON = "dangdang_goods.json"
IMAGE_DIR = "dangdang_images"
MAX_PROXY_TEST = 30
KEEP_PROXIES = 10
TEST_URL = "https://httpbin.org/ip"
REQUEST_TIMEOUT = 12
ENTER_DETAIL_PROB = 0.5
# ----------------------------------------

os.makedirs(IMAGE_DIR, exist_ok=True)

# ---------- 1) 抓取 sslproxies.org 列表 ----------
def fetch_proxies_from_sslproxies(max_items=30):
    url = "https://www.sslproxies.org/"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("❌ 无法访问 sslproxies.org:", e)
        return []
    soup = BeautifulSoup(r.text, "lxml")
    table = soup.find("table", id="proxylisttable")
    if not table:
        print("❌ 未在 sslproxies.org 找到代理表格")
        return []
    proxies = []
    for row in table.tbody.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 2:
            ip = cols[0].text.strip()
            port = cols[1].text.strip()
            proxies.append(f"{ip}:{port}")
            if len(proxies) >= max_items:
                break
    print(f"🔍 抓取到 {len(proxies)} 个代理候选")
    return proxies

# ---------- 2) 测试代理 ----------
def test_proxy_http(proxy):
    proxy_url = proxy if proxy.startswith("http") else f"http://{proxy}"
    proxies = {"http": proxy_url, "https": proxy_url}
    try:
        r = requests.get(TEST_URL, proxies=proxies, timeout=6)
        if r.status_code == 200:
            return proxy_url
    except Exception:
        return None
    return None

def build_working_proxy_pool(candidates, keep_n=10, max_workers=12):
    working = []
    random.shuffle(candidates)
    with ThreadPoolExecutor(max_workers=min(max_workers, len(candidates))) as ex:
        futures = {ex.submit(test_proxy_http, p): p for p in candidates}
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                working.append(res)
                print("✅ 可用代理:", res)
            if len(working) >= keep_n:
                break
    print(f"🔧 可用代理池大小: {len(working)}")
    return working

# ---------- 3) Session / 下载 ----------
def make_session_with_proxy(proxy_url=None, referer=None):
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/141 Safari/537.36",
        "Referer": referer or "https://category.dangdang.com/"
    })
    if proxy_url:
        s.proxies.update({"http": proxy_url, "https": proxy_url})
    return s

def download_binary_with_retries(url, save_path, proxy_pool, tries=3):
    if not url:
        print("❌ 无效的 URL")
        return False
    if url.startswith("//"):
        url = "https:" + url
    for attempt in range(tries):
        proxy = random.choice(proxy_pool) if proxy_pool else None
        sess = make_session_with_proxy(proxy)
        try:
            print(f"尝试下载图片 {url} 第 {attempt + 1} 次")
            r = sess.get(url, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200 and r.content:
                with open(save_path, "wb") as f:
                    f.write(r.content)
                print(f"✅ 图片下载成功: {save_path}")
                return True
        except Exception as e:
            print(f"❌ 下载失败: {e}")
        time.sleep(random.uniform(0.8, 2.0))
    print(f"❌ 下载失败: {url}")
    return False

# ---------- 4) 单商品解析 ----------
# ---------- 4) 单商品解析 ----------
def parse_single_item(li, driver, proxy_pool, default_sess):
    item_id = li.get_attribute("id") or f"item_{random.randint(1000,9999)}"
    title = link = name = price = ""
    img_url = ""
    
    detail_info = {}  # 初始化 detail_info 为空字典

    try:
        a_el = li.find_element(By.XPATH, ".//a[1]")
        title = a_el.get_attribute("title") or a_el.text.strip()
        link = a_el.get_attribute("href") or ""
        try:
            img_el = a_el.find_element(By.XPATH, ".//img")
            img_url = (img_el.get_attribute("data-original")
                       or img_el.get_attribute("data-lazy")
                       or img_el.get_attribute("src") or "")
        except Exception:
            pass
    except Exception:
        return None

    try:
        price = li.find_element(By.XPATH, ".//p[contains(@class,'price')]//span[contains(@class,'price_n')]").text.strip()
    except Exception:
        price = ""

    try:
        name = li.find_element(By.XPATH, ".//p[2]").text.strip()
    except:
        name = ""

    # 下载主图
    local_main = ""
    if img_url:
        ext = os.path.splitext(img_url)[1].split("?")[0] or ".jpg"
        local_main = os.path.join(IMAGE_DIR, f"{item_id}_main{ext}")
        if not os.path.exists(local_main):
            ok = download_binary_with_retries(img_url, local_main, proxy_pool)
            if not ok:
                try:
                    r = default_sess.get(img_url, timeout=REQUEST_TIMEOUT)
                    if r.status_code == 200:
                        with open(local_main, "wb") as f:
                            f.write(r.content)
                except:
                    local_main = ""  # 如果下载失败，路径保持为空

    # 随机决定是否抓详情页（可选）
    detail_images = []  # 初始化为空列表
    if link and random.random() < ENTER_DETAIL_PROB:
        html = None
        for attempt in range(3):
            proxy = random.choice(proxy_pool) if proxy_pool else None
            sess = make_session_with_proxy(proxy, referer=link)
            try:
                r = sess.get(link, timeout=REQUEST_TIMEOUT)
                if r.status_code == 200 and r.text:
                    html = r.text
                    break
            except Exception:
                time.sleep(random.uniform(0.8, 1.8))
                continue
        if html:
            soup = BeautifulSoup(html, "lxml")
            ul = soup.select_one("#detail_describe ul")
            if ul:
                for li_d in ul.select("li"):
                    text = li_d.get_text(strip=True)
                    if "：" in text:
                        k, v = text.split("：", 1)
                        detail_info[k.strip()] = v.strip()  # 添加到 detail_info 字典
            detail_div = soup.select_one("#detail")
            if detail_div:
                imgs = detail_div.select("img")
                for i_img, im in enumerate(imgs, start=1):
                    iurl = im.get("src") or ""
                    if iurl.startswith("//"):
                        iurl = "https:" + iurl
                    if not iurl:
                        continue
                    ext = os.path.splitext(iurl)[1].split("?")[0] or ".jpg"
                    save_path = os.path.join(IMAGE_DIR, f"{item_id}_detail_{i_img}{ext}")
                    if not os.path.exists(save_path):
                        ok = download_binary_with_retries(iurl, save_path, proxy_pool)
                        if ok:
                            detail_images.append(save_path)
                    else:
                        detail_images.append(save_path)

    return {
        "id": item_id,
        "name": title,
        "description": name,
        "price": price,
        "image_main": local_main, 
        "detail_info": detail_info,  
        "detail_images": detail_images
    }

# ---------- 5) 单分类分页抓取 ----------
def crawl_category(driver, category_name, base_url, max_page, proxy_pool, default_sess):
    all_results = []

    def crawl_single_page(page):
        if page == 1:
            url = base_url
        else:
            cid_part = base_url.split("cid")[-1]  # e.g. '4002145.html'
            url = f"https://category.dangdang.com/pg{page}-cid{cid_part}"
        print(f"\n📄 [{category_name}] 抓取第 {page} 页: {url}")

        try:
            driver.get(url)
            time.sleep(random.uniform(3, 5))

            scroll_height = driver.execute_script("return document.body.scrollHeight")
            for y in range(0, scroll_height + 1, 800):
                driver.execute_script(f"window.scrollTo(0, {y});")
                time.sleep(random.uniform(0.6, 1.2))

            goods = driver.find_elements(By.XPATH, '//*[@id="component_47"]/li')
            print(f"  ↳ 找到 {len(goods)} 个商品节点")

            page_results = []
            # 多线程抓详情与图片
            with ThreadPoolExecutor(max_workers=8) as ex:
                futures = [ex.submit(parse_single_item, li, driver, proxy_pool, default_sess) for li in goods]
                for fut in as_completed(futures):
                    record = fut.result()
                    if record:
                        record["category"] = category_name
                        record["page"] = page
                        page_results.append(record)

            return page_results
        except Exception as e:
            print(f"⚠️ {category_name} 第 {page} 页异常: {e}")
            return []

    # 分类内分页并行
    with ThreadPoolExecutor(max_workers=min(max_page, 4)) as page_ex:
        futures = [page_ex.submit(crawl_single_page, p) for p in range(1, max_page + 1)]
        for fut in as_completed(futures):
            all_results.extend(fut.result())

    return all_results

# ---------- 6) 每分类线程抓取 ----------
def crawl_category_thread(cat_name, base_url, max_page, proxy_pool, output_list):
    """每个线程启动独立浏览器抓取一个分类"""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(CHROME_DRIVER)
    driver = webdriver.Chrome(service=service, options=options)

    # 避免被检测
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN','zh']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        window.navigator.chrome = { runtime: {} };
        """
    })

    default_sess = make_session_with_proxy(None)
    try:
        cat_results = crawl_category(driver, cat_name, base_url, max_page, proxy_pool, default_sess)
        output_list.extend(cat_results)
    finally:
        driver.quit()

# ---------- 7) 主流程 ----------
def main():
    candidates = fetch_proxies_from_sslproxies(MAX_PROXY_TEST)
    proxy_pool = build_working_proxy_pool(candidates, keep_n=KEEP_PROXIES) if candidates else []
    if not proxy_pool:
        print("⚠️ 未构建到可用代理，将不使用代理（风险较高）")

    all_data = []

    # 分类间并行抓取
    with ThreadPoolExecutor(max_workers=len(CATEGORIES)) as executor:
        futures = []
        for cat_name, (url, max_page) in CATEGORIES.items():
            futures.append(executor.submit(crawl_category_thread, cat_name, url, max_page, proxy_pool, all_data))

        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception as e:
                print("线程异常:", e)

    # 写入 JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 全部完成，共导出 {len(all_data)} 条商品数据 -> {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
