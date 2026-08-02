import requests
import json
import re
import time
import os
from urllib.parse import urlencode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_JSON = os.path.join(ROOT, "data", "raw", "kfc_stores.json")

# Common keywords in KFC store names and addresses to maximize coverage
KEYWORDS = [
    '路', '街', '道', '号', '弄', '巷', '里', '村', '镇', '区',
    '市', '广场', '中心', '商场', '百货', '万达', '大润发', '宝龙',
    '吾悦', '印象汇', '印象城', '银泰', '汇', '城', '店', '站',
    '大学', '学院', '校区', '医院', '大厦', '小区', '大酒店', '市场',
    '新', '老', '大', '小', '上', '下', '东', '南', '西', '北', '中',
    '金', '百', '星', '天', '地', '人', '和', '光', '明', '美', '好'
]

# Additional fallback letters and numbers
KEYWORDS += [chr(i) for i in range(ord('A'), ord('Z')+1)]
KEYWORDS += [str(i) for i in range(10)]

def extract_cities():
    print("Fetching cities data...")
    url = "https://xd.foodyh.cn/static/js/cities20240424.js"
    response = requests.get(url)
    if response.status_code == 200:
        # Extract the JSON variable from the javascript file
        match = re.search(r'var\s+cities\s*=\s*(\{.*\})', response.text, re.DOTALL)
        if match:
            try:
                cities_data = json.loads(match.group(1))
                all_cities = cities_data.get('data', {}).get('allCities', [])
                city_codes = [city.get('gbCityCode') for city in all_cities if city.get('gbCityCode')]
                print(f"Found {len(city_codes)} city codes.")
                return city_codes, all_cities
            except json.JSONDecodeError as e:
                print("Failed to parse cities JSON.", e)
    else:
        print("Failed to fetch cities JS.", response.status_code)
    return [], []

def fetch_stores_for_city(city_code, keyword):
    url = "https://xd.foodyh.cn/index/index/keywordgetstores.html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://xd.foodyh.cn',
        'Referer': 'https://xd.foodyh.cn/'
    }
    data = {"gbCityCode": city_code, "keyword": keyword}
    
    try:
        response = requests.post(url, data=urlencode(data), headers=headers, timeout=10)
        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get('code') == 200:
                data_node = resp_json.get('data', {}).get('data', {})
                # The response structure might have stores directly or wrapped in 'data'
                stores = data_node.get('stores', [])
                return stores
            elif resp_json.get('code') == 1022:  # 店铺信息异常
                # Often happens if keyword has no matches
                return []
            else:
                pass
    except Exception as e:
        pass
    return []

def main():
    city_codes, all_cities = extract_cities()
    if not city_codes:
        print("No cities configured, exiting.")
        return

    # To test locally without hitting all cities forever, let's limit testing phase
    # if required. But script aims to get all. We will save progress after each city.
    
    # Pre-populate map of gbCityCode to CityName for better logging
    city_map = {city['gbCityCode']: city['cityNameZh'] for city in all_cities}

    all_stores = {}
    total_cities = len(city_codes)

    try:
        # Load existing progress if any
        with open(RAW_JSON, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            for s in existing:
                all_stores[s['storecode']] = s
        print(f"Loaded {len(all_stores)} existing stores.")
    except Exception:
        pass

    try:
        for i, city_code in enumerate(city_codes):
            city_name = city_map.get(city_code, city_code)
            print(f"[{i+1}/{total_cities}] Processing city {city_name} ({city_code})")
            
            city_store_count_before = len(all_stores)
            
            for keyword in KEYWORDS:
                stores = fetch_stores_for_city(city_code, keyword)
                for store in stores:
                    # use string concatenation to extract minimal subset or keep entire dict
                    storecode = store.get('storecode')
                    if storecode:
                        all_stores[storecode] = {
                            'storecode': storecode,
                            'storename': store.get('storename'),
                            'address': store.get('address'),
                            'cityName': store.get('cityName'),
                            'districtName': store.get('districtName'),
                            'starttime': store.get('starttime'),
                            'endtime': store.get('endtime'),
                            'citycode': store.get('citycode'),
                            'marketcode': store.get('marketcode')
                        }
                # To be gentle on API
                time.sleep(0.1)
            
            city_store_count_after = len(all_stores)
            new_this_city = city_store_count_after - city_store_count_before
            print(f"  -> Found {new_this_city} new stores in {city_name}. Total so far: {city_store_count_after}")

            # Save progress periodically
            if (i + 1) % 10 == 0:
                with open(RAW_JSON, 'w', encoding='utf-8') as f:
                    json.dump(list(all_stores.values()), f, ensure_ascii=False, indent=2)

    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving current progress...")
    finally:
        with open(RAW_JSON, 'w', encoding='utf-8') as f:
            json.dump(list(all_stores.values()), f, ensure_ascii=False, indent=2)
        print(f"Saved {len(all_stores)} total stores.")

if __name__ == "__main__":
    main()
