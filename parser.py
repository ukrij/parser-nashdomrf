from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "habarovsk_newbuildings.json")

URL = "https://наш.дом.рф/новостройки/строящиеся/хабаровск/"
SHOW_MORE_SELECTOR = '[class*="LoadMoreContainer"] button'
CARD_SELECTOR = '[class*="NewBuildingItem__Row"]'

driver = webdriver.Chrome()
results = []

try:
    driver.get(URL)
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CARD_SELECTOR)))
    time.sleep(2)

    # Нажимаем "Показать ещё"
    click_count = 0
    while click_count < 100:
        try:
            button = driver.find_element(By.CSS_SELECTOR, SHOW_MORE_SELECTOR)
            if not button.is_displayed() or not button.is_enabled():
                break
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1)
            cards_before = len(driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR))
            driver.execute_script("arguments[0].click();", button)
            click_count += 1
            print(f"Клик №{click_count}")
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)) > cards_before
                )
            except Exception:
                break
        except NoSuchElementException:
            break

    time.sleep(2)
    cards = driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)
    print(f"Найдено карточек (включая пустышки): {len(cards)}")

    for card in cards:
        item = {"name": None, "address": None, "url": None}

        try:
            link_el = card.find_element(
                By.CSS_SELECTOR, '[class*="NewBuildingItem__MainTitleWrapper"] a'
            )
            item["name"] = link_el.text.strip()
            item["url"] = link_el.get_attribute("href")
        except NoSuchElementException:
            pass

        try:
            addr_el = card.find_element(
                By.CSS_SELECTOR, '[class*="NewBuildingItem__MainTitleWrapper"] p'
            )
            item["address"] = addr_el.text.strip()
        except NoSuchElementException:
            pass

        # Пропускаем пустышки
        if not (item["name"] or item["url"]):
            continue

        results.append(item)

    # Дедупликация по URL
    seen = set()
    unique_results = []
    for r in results:
        if r["url"] and r["url"] not in seen:
            seen.add(r["url"])
            unique_results.append(r)
    results = unique_results

    print(f"Уникальных карточек: {len(results)}")

finally:
    driver.quit()

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"✅ Сохранено {len(results)} записей в {OUTPUT_FILE}")