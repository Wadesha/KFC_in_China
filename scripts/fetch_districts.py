import requests
import os
import json
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import load_dotenv

load_dotenv()

# 腾讯地图 API Key：从环境变量 / .env 读取（不再硬编码）
TENCENT_API_KEY = os.environ.get("TENCENT_MAP_API_KEY") or os.environ.get(
    "TENCENT_MAP_API_KEYS", ""
).split(",")[0].strip()

if not TENCENT_API_KEY:
    sys.stderr.write(
        "缺少腾讯地图 API Key：请在 .env 中设置 "
        "TENCENT_MAP_API_KEY=your_key 或 TENCENT_MAP_API_KEYS=key1,key2\n"
    )
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 城市列表（与之前获取KFC数据的城市一致）
cities = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆']

def get_district_boundaries(city_name):
    """使用腾讯地图API获取指定城市的区县边界"""
    # 首先搜索城市，获取城市ID
    search_url = 'https://apis.map.qq.com/ws/place/v1/search'
    search_params = {
        'key': TENCENT_API_KEY,
        'keyword': city_name,
        'boundary': 'region(' + city_name + ',0)',
        'page_size': 1
    }
    
    response = requests.get(search_url, params=search_params)
    search_data = response.json()
    
    if search_data['status'] != 0 or not search_data['data']:
        print(f'无法搜索到城市 {city_name}')
        return None
    
    # 获取城市的adcode
    city_adcode = search_data['data'][0].get('adcode', '')
    if not city_adcode:
        print(f'无法获取城市 {city_name} 的adcode')
        return None
    
    # 使用腾讯地图的行政区划API获取区县边界
    district_url = 'https://apis.map.qq.com/ws/district/v1/list'
    district_params = {
        'key': TENCENT_API_KEY,
        'id': city_adcode
    }
    
    response = requests.get(district_url, params=district_params)
    district_data = response.json()
    
    if district_data['status'] != 0 or not district_data['result']:
        print(f'无法获取城市 {city_name} 的区县数据')
        return None
    
    return district_data['result']

def download_district_geojson(city_name):
    """下载指定城市的区县边界GeoJSON数据"""
    districts = get_district_boundaries(city_name)
    if not districts:
        return False
    
    # 保存GeoJSON数据
    output_dir = os.path.join(ROOT, 'assets', 'geo', 'districts')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = os.path.join(output_dir, f'{city_name}_districts.geojson')
    
    # 构建GeoJSON结构
    geojson = {
        'type': 'FeatureCollection',
        'features': []
    }
    
    print(f'城市 {city_name} 的区县数量: {len(districts)}')
    
    # 处理区县数据
    for district in districts:
        print(f'处理区县: {district.get("fullname")}')
        
        # 腾讯地图API返回的边界数据结构不同，需要根据实际返回格式调整
        if 'location' in district and 'lat' in district['location'] and 'lng' in district['location']:
            # 简化处理，使用中心点作为示例
            # 实际项目中需要根据腾讯地图API的具体返回格式来解析边界
            feature = {
                'type': 'Feature',
                'properties': {
                    'name': district.get('fullname', ''),
                    'adcode': district.get('id', '')
                },
                'geometry': {
                    'type': 'Point',
                    'coordinates': [district['location']['lng'], district['location']['lat']]
                }
            }
            geojson['features'].append(feature)
            print(f'添加区县到GeoJSON: {district.get("fullname")}')
    
    # 保存文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    
    print(f'已下载 {city_name} 的区县边界数据到 {output_file}')
    return True

def main():
    """主函数，下载所有城市的区县边界数据"""
    for city in cities:
        print(f'正在下载 {city} 的区县边界数据...')
        download_district_geojson(city)
    print('\n所有城市的区县边界数据下载完成!')

if __name__ == '__main__':
    main()