import csv
import os
import matplotlib.pyplot as plt
from collections import defaultdict
import json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 读取CSV文件
def read_kfc_stores(csv_file):
    stores = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            print(f'CSV文件字段: {reader.fieldnames}')
            
            for i, row in enumerate(reader):
                if i < 5:  # 打印前5行数据
                    print(f'第{i+1}行数据: {row}')
                
                try:
                    # 尝试不同的字段名
                    city_key = 'cityName' if 'cityName' in row else 'cityname' if 'cityname' in row else 'city'
                    lat_key = 'lat' if 'lat' in row else 'latitude'
                    lng_key = 'lng' if 'lng' in row else 'longitude'
                    
                    store = {
                        'storecode': row.get('storecode', ''),
                        'storename': row.get('storename', ''),
                        'cityName': row.get(city_key, ''),
                        'districtName': row.get('districtName', '') or row.get('districtname', ''),
                        'address': row.get('address', ''),
                        'lat': float(row.get(lat_key, 0)),
                        'lng': float(row.get(lng_key, 0))
                    }
                    
                    if store['cityName'] and store['lat'] != 0 and store['lng'] != 0:
                        stores.append(store)
                    else:
                        print(f'跳过无效数据: {row}')
                        
                except (ValueError, KeyError) as e:
                    print(f'处理第{i+1}行时出错: {e}, 数据: {row}')
                    continue
        
        print(f'成功读取 {len(stores)} 条有效数据')
        return stores
    except Exception as e:
        print(f'读取CSV文件时出错: {e}')
        return []

# 按城市分组
def group_by_city(stores):
    city_stores = defaultdict(list)
    for store in stores:
        city_stores[store['cityName']].append(store)
    return city_stores

# 生成散点图
def generate_scatter_plot(city, stores, output_dir):
    if not stores:
        return
    
    # 按区县分组
    district_stores = defaultdict(list)
    for store in stores:
        district = store.get('districtName', '未知')
        district_stores[district].append(store)
    
    # 按KFC数量降序排列区县
    sorted_districts = sorted(district_stores.items(), key=lambda x: len(x[1]), reverse=True)
    
    plt.figure(figsize=(14, 10))
    
    # 绘制区县边界
    geojson_dir = os.path.join(ROOT, 'china_geojson', 'ChinaGeoJson-master', 'county')
    if os.path.exists(geojson_dir):
        # 绘制每个区县的边界
        for district, _ in sorted_districts:
            if district != '未知':
                geojson_file = os.path.join(geojson_dir, f'{district}.json')
                if os.path.exists(geojson_file):
                    try:
                        with open(geojson_file, 'r', encoding='utf-8') as f:
                            geojson_data = json.load(f)
                        
                        # 绘制多边形
                        if geojson_data.get('type') == 'FeatureCollection':
                            for feature in geojson_data.get('features', []):
                                geometry = feature.get('geometry', {})
                                if geometry.get('type') == 'MultiPolygon':
                                    for polygon in geometry.get('coordinates', []):
                                        for ring in polygon:
                                            if ring:
                                                lngs_ring = [point[0] for point in ring]
                                                lats_ring = [point[1] for point in ring]
                                                plt.plot(lngs_ring, lats_ring, color='lightgray', linewidth=1, alpha=0.7)
                                elif geometry.get('type') == 'Polygon':
                                    for ring in geometry.get('coordinates', []):
                                        if ring:
                                            lngs_ring = [point[0] for point in ring]
                                            lats_ring = [point[1] for point in ring]
                                            plt.plot(lngs_ring, lats_ring, color='lightgray', linewidth=1, alpha=0.7)
                        elif geojson_data.get('type') == 'Feature':
                            geometry = geojson_data.get('geometry', {})
                            if geometry.get('type') == 'MultiPolygon':
                                for polygon in geometry.get('coordinates', []):
                                    for ring in polygon:
                                        if ring:
                                            lngs_ring = [point[0] for point in ring]
                                            lats_ring = [point[1] for point in ring]
                                            plt.plot(lngs_ring, lats_ring, color='lightgray', linewidth=1, alpha=0.7)
                            elif geometry.get('type') == 'Polygon':
                                for ring in geometry.get('coordinates', []):
                                    if ring:
                                        lngs_ring = [point[0] for point in ring]
                                        lats_ring = [point[1] for point in ring]
                                        plt.plot(lngs_ring, lats_ring, color='lightgray', linewidth=1, alpha=0.7)
                    except Exception as e:
                        print(f'绘制 {district} 边界时出错: {e}')
    
    # 生成颜色映射
    colors = plt.cm.tab20(np.linspace(0, 1, len(sorted_districts)))
    color_map = {district: colors[i] for i, (district, _) in enumerate(sorted_districts)}
    
    # 绘制散点图，按区县着色
    for district, district_store_list in sorted_districts:
        lats = [store['lat'] for store in district_store_list]
        lngs = [store['lng'] for store in district_store_list]
        count = len(district_store_list)
        plt.scatter(lngs, lats, c=[color_map[district]], s=30, alpha=0.7, label=f'{district} ({count}家)')
    
    # 添加图例（按KFC数量降序排列）
    plt.legend(title='区县 (KFC数量)', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.title(f'KFC门店分布 - {city} (共{len(stores)}家)', fontsize=14)
    plt.xlabel('经度', fontsize=12)
    plt.ylabel('纬度', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # 调整图表范围
    all_lats = [store['lat'] for store in stores]
    all_lngs = [store['lng'] for store in stores]
    padding = 0.05
    min_lng, max_lng = min(all_lngs), max(all_lngs)
    min_lat, max_lat = min(all_lats), max(all_lats)
    plt.xlim(min_lng - padding, max_lng + padding)
    plt.ylim(min_lat - padding, max_lat + padding)
    
    # 保存为PNG文件
    output_file = os.path.join(output_dir, f'{city}_kfc_stores.png')
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f'已生成 {city} 的散点图: {output_file}')

# 主函数
def main():
    csv_file = os.path.join(ROOT, 'data', 'processed', 'kfc_stores_with_coords.csv')
    output_dir = os.path.join(ROOT, 'scatter_plots_extended')
    
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 读取数据
    stores = read_kfc_stores(csv_file)
    print(f'共读取 {len(stores)} 家KFC门店数据')
    
    # 按城市分组
    city_stores = group_by_city(stores)
    print(f'共包含 {len(city_stores)} 个城市')
    
    # 为每个城市生成散点图
    for city, city_store_list in city_stores.items():
        generate_scatter_plot(city, city_store_list, output_dir)
    
    print('\n所有城市的散点图已生成完成!')

if __name__ == '__main__':
    main()