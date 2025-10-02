# --- Selenium 相關匯入 ---
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# 📌 優化：webdriver_manager 將只在主程式啟動時呼叫一次。
from selenium.common.exceptions import WebDriverException
from concurrent.futures import ThreadPoolExecutor, as_completed
import tomli
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
from bs4 import BeautifulSoup

# --- 讀取設定檔 ---
# 注意：配置檔案在運行期間不會自動熱更新，如需修改請重啟程式。
with open("config.toml", "rb") as f:
    config = tomli.load(f)

# 讀取區塊內的設定
general_config = config['general']
COUNTRY_CODE = general_config['country_code']
CACHE_DURATION_SECONDS = general_config['cache_duration_seconds']
CACHE_DURATION_MINUTES = int(CACHE_DURATION_SECONDS / 60) 
MAX_WORKERS = general_config['max_workers']
PAGE_INDEX = general_config['page_index']
PORT = general_config['port']

# 讀取關鍵字設定
KEYWORDS_CONFIG = config['keywords']

# 偽裝成瀏覽器的 Headers
HEADERS = config['headers']

def is_within_last_hour(time_text):
    """
    檢查時間文字 (例如 '5分钟前', '2小时前') 是否在最近一小時內。
    """
    time_text = time_text.strip()
    if any(s in time_text for s in ['分钟前', '分鐘前', 'minutes ago']):
        try:
            minutes = int(re.findall(r'\d+', time_text)[0])
            if minutes <= 60:
                return True
        except (IndexError, ValueError):
            return False
    if any(s in time_text for s in ['秒前', 'seconds ago']):
        return True
    return False

def apply_keyword_filter(numbers, include_keywords, exclude_keywords):
    """
    根據關鍵字清單篩選爬蟲結果。
    """
    if not include_keywords and not exclude_keywords:
        return numbers

    filtered_numbers = []
    inc_lower = [k.lower() for k in include_keywords if k]
    exc_lower = [k.lower() for k in exclude_keywords if k]

    for item in numbers:
        all_sms_content = " ".join(item.get('smss', [])).lower()
        if exc_lower and any(ex_k in all_sms_content for ex_k in exc_lower):
            continue
        if inc_lower and not any(in_k in all_sms_content for in_k in inc_lower):
            continue
        filtered_numbers.append(item)
    return filtered_numbers


def freereceivesms_check_single_number(number_info, user_agent, service, base_url):
    """
    檢查單一號碼的函數，使用傳入的 Selenium Service 實例。
    """
    number_url = number_info['url']
    phone_number_text = number_info['number']
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f'user-agent={user_agent}')
    
    driver = None
    result = None
    for i in range(2):
        try:
            print(f"    [THREAD] 檢查號碼: {phone_number_text} ...", end="", flush=True)
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)
            driver.get(number_url)
            message_row_selector = '.container .row.border-bottom'
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, message_row_selector)))
            time.sleep(4)
            num_soup = BeautifulSoup(driver.page_source, 'html.parser')
            message_rows = num_soup.select(message_row_selector)
            message_rows_contents=[]
            if message_rows:
                latest_row = message_rows[0]
                time_element_lg = latest_row.select_one('.d-none.d-lg-block.col-lg-2 span')
                time_element_sm = latest_row.select_one('.d-block.d-lg-none.ml-2')
                for item in message_rows:
                     item_element = item.select_one('.col-lg-8 div')
                     message_rows_contents.append(item_element.get_text(strip=True) if item_element else "無法讀取簡訊內容。")
                time_text = ''
                if time_element_lg:
                    time_text = time_element_lg.get_text(strip=True)
                elif time_element_sm:
                    time_text = time_element_sm.get_text(strip=True)
                sms_content_element = latest_row.select_one('.col-lg-8 div')
                sms_content = sms_content_element.get_text(strip=True) if sms_content_element else "無法讀取簡訊內容。"
                if time_text and is_within_last_hour(time_text):
                    if len(sms_content) > 80 and (sms_content.endswith('==') or sms_content.endswith('=')):
                        sms_content = " 【注意：內容可能被網站加密，請在瀏覽器中確認】"+sms_content
                    print(f"  -> \033[92m找到活躍號碼 (最新訊息: {time_text})\033[0m")
                    result = {'number': phone_number_text, 'url': number_url, 'last_sms': sms_content, 'smss': message_rows_contents}
                else:
                    print(f"  -> 不活躍 (最新訊息: {time_text})")
            else:
                print("  -> 找不到訊息列。")
        except WebDriverException as e:
            print(f"  -> \033[91mSelenium 讀取失敗: {e}\033[0m")
        except Exception as e:
            print(f"  -> 檢查 {phone_number_text} 失敗: {e}")
        finally:
            if driver:
                driver.quit()
        time.sleep(5)
    return result

def freereceivesms_find_active_numbers(CHROME_SERVICE, base_url, country_code=COUNTRY_CODE, page=PAGE_INDEX):
    """
    取得所有號碼列表，然後使用執行緒池併發檢查號碼。
    """
    print(f"[*] 正在使用 Selenium 搜尋 {country_code.upper()} 國碼的號碼...")
    numbers_to_check = []
    country_page_url = f"{base_url}/{country_code}/{page}/"
    print(f"[*] 目標國家頁面: {country_page_url}")
    driver = None
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
        print("[*] 正在載入國家頁面以取得號碼清單...")
        driver = webdriver.Chrome(service=CHROME_SERVICE, options=options)
        driver.set_page_load_timeout(30)
        driver.get(country_page_url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        number_boxes = soup.select('.number-boxes-item')
        if not number_boxes:
            print("[!] 在國家頁面上找不到任何號碼。網站結構可能已更改或載入失敗。 ")
            return []
        for box in number_boxes:
            link_tag = box.find('a', class_='btn-outline-info')
            if not link_tag or 'href' not in link_tag.attrs:
                continue
            number_path = link_tag['href']
            number_url = f"{base_url}{number_path}"
            phone_number_text = box.find('h4').get_text(strip=True) if box.find('h4') else "N/A"
            numbers_to_check.append({'number': phone_number_text, 'url': number_url})
        print(f"[*] 成功找到 {len(numbers_to_check)} 個號碼，開始併發檢查...")
    except WebDriverException as e:
        print(f"\n[!] 載入國家頁面失敗: {e}")
        return None
    except Exception as e:
        print(f"\n[!] 載入國家頁面發生一般錯誤: {e}")
        return None
    finally:
        if driver:
            driver.quit()
    raw_active_numbers = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_number = {executor.submit(freereceivesms_check_single_number, num_info, HEADERS['User-Agent'], CHROME_SERVICE, base_url): num_info for num_info in numbers_to_check}
        for future in as_completed(future_to_number):
            result = future.result()
            if result:
                raw_active_numbers.append(result)
    print(f"\n[*] 搜尋完畢。總共找到 {len(raw_active_numbers)} 個活躍號碼。")
    return raw_active_numbers

def receivesmss_check_single_number(number_info, user_agent, service, base_url):
    """
    使用 Selenium 檢查 receive-smss.com 的單一號碼。
    """
    number_url = number_info['url']
    phone_number_text = number_info['number']
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f'user-agent={user_agent}')
    
    driver = None
    result = None
    try:
        print(f"    [THREAD] 檢查號碼: {phone_number_text} ...", end="", flush=True)
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        driver.get(number_url)
        
        message_row_selector = 'div.row.border-bottom.py-2'
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, message_row_selector)))
        time.sleep(2) # 等待頁面可能存在的JS渲染

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        message_rows = soup.select(message_row_selector)
        
        if not message_rows:
            print("  -> 找不到訊息列。")
            return None

        latest_row = message_rows[0]
        time_element = latest_row.select_one('div.col-md-2.text-right span.text-muted')
        time_text = time_element.get_text(strip=True) if time_element else ""

        if time_text and is_within_last_hour(time_text):
            sms_content_element = latest_row.select_one('div.col-md-8')
            sms_content = sms_content_element.get_text(strip=True) if sms_content_element else "無法讀取簡訊內容。"
            all_smss = [row.select_one('div.col-md-8').get_text(strip=True) for row in message_rows if row.select_one('div.col-md-8')]

            print(f"  -> \033[92m找到活躍號碼 (最新訊息: {time_text})\033[0m")
            result = {'number': phone_number_text, 'url': number_url, 'last_sms': sms_content, 'smss': all_smss}
        else:
            print(f"  -> 不活躍 (最新訊息: {time_text})")
    except WebDriverException as e:
        print(f"  -> \033[91mSelenium 讀取失敗: {e}\033[0m")
    except Exception as e:
        print(f"  -> 檢查 {phone_number_text} 失敗: {e}")
    finally:
        if driver:
            driver.quit()
    return result

def receivesmss_find_active_numbers(CHROME_SERVICE, base_url, user_agent):
    """
    使用 Selenium 從 receive-smss.com 取得號碼列表。
    """
    print(f"[*] 正在使用 Selenium 搜尋 {base_url} 的號碼...")
    numbers_to_check = []
    driver = None
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={user_agent}')
        
        print("[*] 正在載入主頁面以取得號碼清單...")
        driver = webdriver.Chrome(service=CHROME_SERVICE, options=options)
        driver.set_page_load_timeout(40)

        for attempt in range(3):
            try:
                driver.get(base_url)
                
                # 改用 WebDriverWait 來等待 Cloudflare 挑戰完成
                # 等待 .number-boxes > a 元素出現，最多等 60 秒
                print("[*] 正在等待 Cloudflare 驗證...")
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".number-boxes > a"))
                )
                print("[*] Cloudflare 驗證通過，頁面已載入。")

                # 將頁面源碼寫入文件以供調試
                with open(f"receivesmss_page_source_attempt_{attempt + 1}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"[*] 第 {attempt + 1} 次嘗試的頁面源碼已保存到 receivesmss_page_source_attempt_{attempt + 1}.html")

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                number_links = soup.select('.number-boxes > a')

                if number_links:
                    print(f"[*] 第 {attempt + 1} 次嘗試成功找到號碼連結。")
                    for link in number_links:
                        number_path = link.get('href')
                        if number_path:
                            number_url = f"{base_url.rstrip('/')}{number_path}"
                            phone_number_tag = link.select_one('.number-boxes-itemm-number')
                            phone_number_text = phone_number_tag.get_text(strip=True) if phone_number_tag else "N/A"
                            numbers_to_check.append({'number': phone_number_text, 'url': number_url})
                    break  # 成功找到連結，跳出循環
                else:
                    # 如果 WebDriverWait 成功但仍然找不到連結，這表示網站結構可能真的改變了
                    print(f"[!] 第 {attempt + 1} 次嘗試在主頁上找不到任何號碼，即使已等待頁面載入。網站結構可能已更改。")
                    # 在這種情況下，重新整理可能沒有幫助，但還是保留以防萬一
                    driver.refresh()
            except WebDriverException as e:
                print(f"\n[!] 第 {attempt + 1} 次嘗試載入主頁面或等待元素時發生錯誤: {e}")
                driver.refresh()

        if not numbers_to_check:
            print("[!] 在 3 次嘗試後，仍然無法在主頁上找到任何號碼。網站結構可能已更改或載入失敗。 ")
            return []

        print(f"[*] 成功找到 {len(numbers_to_check)} 個號碼，開始併發檢查...")

    except Exception as e:
        print(f"\n[!] 載入主頁面發生一般錯誤: {e}")
        return []
    finally:
        if driver:
            driver.quit()

    raw_active_numbers = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_number = {executor.submit(receivesmss_check_single_number, num_info, user_agent, CHROME_SERVICE, base_url): num_info for num_info in numbers_to_check}
        for future in as_completed(future_to_number):
            result = future.result()
            if result:
                raw_active_numbers.append(result)
    
    print(f"\n[*] 搜尋完畢。總共找到 {len(raw_active_numbers)} 個活躍號碼。")
    return raw_active_numbers

def scrape_all_sites(CHROME_SERVICE):
    """
    遍歷 config.toml 中的所有 base_urls，並為每個 URL 呼叫對應的爬蟲函式。
    """
    with open("config.toml", "rb") as f:
        config = tomli.load(f)
    
    base_urls = config.get('general', {}).get('base_urls', [])
    country_code = config.get('general', {}).get('country_code', 'us')
    page_index = config.get('general', {}).get('page_index', 1)
    user_agent = config.get('headers', {}).get('User-Agent', 'Mozilla/5.0')

    all_results = []
    print(f"[*] 開始遍歷 {len(base_urls)} 個網站...")

    for url in base_urls:
        print(f"\n--- 正在處理網站: {url} ---")
        if "freereceivesms.com" in url:
            try:
                numbers = freereceivesms_find_active_numbers(CHROME_SERVICE, base_url=url, country_code=country_code, page=page_index)
                if numbers:
                    all_results.extend(numbers)
            except Exception as e:
                print(f"[!] 處理 {url} 時發生錯誤: {e}")
        elif "receive-smss.com" in url:
            try:
                # 使用 Selenium 進行初始頁面加載
                print(f"[*] 正在使用 Selenium 搜尋 {url} 的號碼...")
                numbers = receivesmss_find_active_numbers(CHROME_SERVICE, base_url=url, user_agent=user_agent)
                if numbers:
                    all_results.extend(numbers)
            except Exception as e:
                print(f"[!] 處理 {url} 時發生錯誤: {e}")
        else:
            print(f"[!] 警告：找不到為 {url} 設定的解析器。 ")

    print(f"\n[*] 所有網站處理完畢，總共從 {len(base_urls)} 個網站中收集到 {len(all_results)} 個活躍號碼。 ")
    return all_results