import requests
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import load_dotenv

load_dotenv()

# 高德地图 API Key：从环境变量 / .env 读取（不再硬编码）
AMAP_API_KEY = os.environ.get("AMAP_API_KEY", "")
if not AMAP_API_KEY:
    sys.stderr.write(
        "缺少高德地图 API Key：请在 .env 中设置 AMAP_API_KEY=your_key\n"
    )
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 城市列表（添加更多城市）
cities = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆',
          '天津', '苏州', '郑州', '长沙', '沈阳', '青岛', '宁波', '东莞', '无锡', '福州',
          '厦门', '大连', '济南', '哈尔滨', '昆明', '合肥', '南宁', '南昌', '贵阳', '太原',
          '石家庄', '乌鲁木齐', '拉萨', '西宁', '银川', '兰州', '呼和浩特', '海口', '三亚', '珠海',
          '佛山', '中山', '惠州', '江门', '肇庆', '汕头', '湛江', '茂名', '阳江', '潮州',
          '揭阳', '清远', '韶关', '梅州', '邯郸', '唐山', '保定', '廊坊', '沧州', '秦皇岛',
          '张家口', '承德', '衡水', '邢台', '淄博', '烟台', '潍坊', '济宁', '泰安', '威海',
          '日照', '莱芜', '临沂', '德州', '聊城', '滨州', '菏泽', '徐州', '连云港', '宿迁',
          '淮安', '盐城', '扬州', '泰州', '南通', '镇江', '常州', '温州', '嘉兴', '湖州',
          '绍兴', '金华', '衢州', '舟山', '台州', '丽水', '湖州', '马鞍山', '芜湖', '铜陵',
          '安庆', '黄山', '滁州', '阜阳', '宿州', '巢湖', '六安', '亳州', '池州', '宣城',
          '九江', '景德镇', '萍乡', '新余', '鹰潭', '赣州', '宜春', '上饶', '吉安', '抚州',
          '株洲', '湘潭', '衡阳', '邵阳', '岳阳', '常德', '张家界', '益阳', '郴州', '永州',
          '怀化', '娄底', '湘西', '柳州', '桂林', '梧州', '北海', '防城港', '钦州', '贵港',
          '玉林', '百色', '贺州', '河池', '来宾', '崇左', '绵阳', '自贡', '攀枝花', '泸州',
          '德阳', '广元', '遂宁', '内江', '乐山', '南充', '眉山', '宜宾', '广安', '达州',
          '雅安', '巴中', '资阳', '阿坝', '甘孜', '凉山', '遵义', '六盘水', '安顺', '毕节',
          '铜仁', '黔西南', '黔东南', '黔南', '曲靖', '玉溪', '保山', '昭通', '丽江', '普洱',
          '临沧', '楚雄', '红河', '文山', '西双版纳', '大理', '德宏', '怒江', '迪庆', '宝鸡',
          '咸阳', '铜川', '渭南', '延安', '汉中', '榆林', '安康', '商洛', '鞍山', '抚顺',
          '本溪', '丹东', '锦州', '营口', '阜新', '辽阳', '盘锦', '铁岭', '朝阳', '葫芦岛',
          '通化', '白城', '松原', '四平', '辽源', '吉林', '延边', '大庆', '齐齐哈尔', '牡丹江',
          '佳木斯', '绥化', '黑河', '伊春', '鸡西', '鹤岗', '双鸭山', '七台河', '大兴安岭', '香港', '澳门']

def fetch_kfc_locations(city):
    """使用高德地图API获取指定城市的KFC门店位置"""
    url = 'https://restapi.amap.com/v3/place/text'
    params = {
        'key': AMAP_API_KEY,
        'keywords': '肯德基',
        'city': city,
        'extensions': 'base',
        'children': 1,
        'page': 1,
        'offset': 25
    }
    
    locations = []
    page = 1
    
    while True:
        params['page'] = page
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] == '1' and data['pois']:
            for poi in data['pois']:
                location = {
                    'storecode': '',  # 高德API没有提供门店编码
                    'storename': poi.get('name', ''),
                    'cityName': city,
                    'districtName': poi.get('adname', ''),
                    'address': poi.get('address', ''),
                    'starttime': '',  # 高德API没有提供营业时间
                    'endtime': '',  # 高德API没有提供营业时间
                    'lat': float(poi.get('location', '0,0').split(',')[1]),
                    'lng': float(poi.get('location', '0,0').split(',')[0])
                }
                locations.append(location)
            
            # 检查是否还有更多数据
            if len(data['pois']) < 25:
                break
            page += 1
        else:
            break
    
    return locations

def main():
    """主函数，获取所有城市的KFC位置并保存到CSV文件"""
    all_locations = []
    
    for city in cities:
        print(f'正在获取 {city} 的KFC门店位置...')
        locations = fetch_kfc_locations(city)
        all_locations.extend(locations)
        print(f'已获取 {len(locations)} 家KFC门店')
    
    # 保存到CSV文件
    output_file = os.path.join(ROOT, 'data', 'raw', 'kfc_stores_amap.csv')
    fieldnames = ['storecode', 'storename', 'cityName', 'districtName', 'address', 'starttime', 'endtime', 'lat', 'lng']
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for location in all_locations:
            writer.writerow(location)
    
    print(f'\n所有城市的KFC门店位置已保存到 {output_file}')
    print(f'共获取 {len(all_locations)} 家KFC门店')

if __name__ == '__main__':
    main()