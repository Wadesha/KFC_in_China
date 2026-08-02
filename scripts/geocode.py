import json
import csv
import time
import requests
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import load_dotenv

load_dotenv()

# 腾讯地图 API Key：从环境变量 / .env 读取（不再硬编码）
# 支持多个 key，用逗号分隔，脚本会自动轮换以规避配额限制。
TENCENT_KEYS_RAW = os.environ.get("TENCENT_MAP_API_KEYS", "")
API_KEYS = [k.strip() for k in TENCENT_KEYS_RAW.split(",") if k.strip()]

if not API_KEYS:
    sys.stderr.write(
        "缺少腾讯地图 API Key：请在 .env 中设置 "
        "TENCENT_MAP_API_KEYS=key1,key2,...\n"
    )
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_INPUT = os.path.join(ROOT, "data", "raw", "kfc_stores.json")
CSV_OUTPUT = os.path.join(ROOT, "data", "processed", "kfc_stores_with_coords.csv")

def get_coordinates(address, key):
    """
    Call Tencent Map WebService API for geocoding.
    Returns (lat, lng) or (None, None) if failed/quota exceeded.
    """
    url = "https://apis.map.qq.com/ws/geocoder/v1/"
    params = {
        "address": address,
        "key": key
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 0:
                location = data.get("result", {}).get("location", {})
                return location.get("lat"), location.get("lng")
            else:
                # E.g., status == 121 (quota exhausted) or status == 311 (key error)
                return None, data.get("message")
    except Exception as e:
        return None, str(e)
    return None, "HTTP Error"

def main(test_mode=False):
    if not os.path.exists(JSON_INPUT):
        print(f"Error: {JSON_INPUT} not found. Ensure scraping is running/finished.")
        return

    # 1. Read existing data
    with open(JSON_INPUT, 'r', encoding='utf-8') as f:
        stores = json.load(f)

    print(f"Loaded {len(stores)} stores from {JSON_INPUT}.")
    
    if test_mode:
        print("--- RUNNING IN TEST MODE (Only processing 5 stores) ---")
        stores = stores[:5]

    # 2. Check existing CSV progress to allow resuming
    processed_storecodes = set()
    file_exists = os.path.exists(CSV_OUTPUT)
    
    if file_exists:
        with open(CSV_OUTPUT, 'r', encoding='utf-8') as cf:
            reader = csv.DictReader(cf)
            for row in reader:
                processed_storecodes.add(row.get('storecode', ''))
        print(f"Found {len(processed_storecodes)} already processed stores in CSV.")

    # Define CSV columns
    fieldnames = [
        "storecode", "storename", "cityName", "districtName", 
        "address", "starttime", "endtime", "lat", "lng"
    ]

    current_key_idx = 0
    
    # 3. Process remaining stores
    with open(CSV_OUTPUT, 'a' if file_exists else 'w', newline='', encoding='utf-8-sig') as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        
        # Write header if new file
        if not file_exists:
            writer.writeheader()

        for i, store in enumerate(stores):
            storecode = store.get("storecode")
            if storecode in processed_storecodes:
                continue
            
            # Combine cityName and address for better geocoding accuracy
            city = store.get("cityName", "")
            address_text = store.get("address", "")
            full_address = f"{city}市{address_text}"
            
            lat, lng = None, None
            
            # Key rotation loop
            while current_key_idx < len(API_KEYS):
                key = API_KEYS[current_key_idx]
                lat, lng_or_err = get_coordinates(full_address, key)
                
                if lat is not None:
                    lng = lng_or_err
                    break
                else:
                    err_msg = lng_or_err
                    print(f"  [API Key {current_key_idx} failed]: {err_msg}")
                    # If quota exhausted or rate limited, move to next key
                    current_key_idx += 1
            
            if current_key_idx >= len(API_KEYS):
                print("All API keys exhausted. Stopping execution.")
                break

            # Write row to CSV
            row = {
                "storecode": storecode,
                "storename": store.get("storename", ""),
                "cityName": city,
                "districtName": store.get("districtName", ""),
                "address": address_text,
                "starttime": store.get("starttime", ""),
                "endtime": store.get("endtime", ""),
                "lat": lat,
                "lng": lng
            }
            writer.writerow(row)
            # Flush immediately to save progress instantly
            cf.flush()
            
            print(f"[{i+1}/{len(stores)}] Geocoded: {store.get('storename')} -> ({lat}, {lng})")
            
            # Sleep to respect QPS limits (Tencent free tier is usually 5 QPS per key)
            time.sleep(0.25)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Geocode KFC stores JSON to CSV')
    parser.add_argument('--test', action='store_true', help='Run on first 5 stores only')
    args = parser.parse_args()
    
    main(test_mode=args.test)
