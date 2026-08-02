import os
import requests
import zipfile
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# GitHub仓库URL（第三方中国行政区划 GeoJSON，数据版权归原作者所有）
GITHUB_REPO_URL = 'https://github.com/zhChuXiao/ChinaGeoJson/archive/refs/heads/master.zip'

# 保存目录
GEOJSON_DIR = os.path.join(ROOT, 'china_geojson')

def download_and_extract_geojson():
    """下载并解压ChinaGeoJson仓库"""
    # 创建保存目录
    if not os.path.exists(GEOJSON_DIR):
        os.makedirs(GEOJSON_DIR)
    
    # 下载zip文件
    zip_file = os.path.join(GEOJSON_DIR, 'ChinaGeoJson.zip')
    print(f'正在下载ChinaGeoJson仓库...')
    
    response = requests.get(GITHUB_REPO_URL)
    with open(zip_file, 'wb') as f:
        f.write(response.content)
    
    print(f'下载完成，正在解压...')
    
    # 解压zip文件
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(GEOJSON_DIR)
    
    print(f'解压完成！')
    
    # 清理zip文件
    os.remove(zip_file)
    
    # 查看解压后的文件结构
    extracted_dir = os.path.join(GEOJSON_DIR, 'ChinaGeoJson-master')
    if os.path.exists(extracted_dir):
        print(f'\n解压后的文件结构:')
        for root, dirs, files in os.walk(extracted_dir):
            level = root.replace(extracted_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                if file.endswith('.json'):
                    print(f'{subindent}{file}')
    
    return extracted_dir

def main():
    """主函数"""
    download_and_extract_geojson()

if __name__ == '__main__':
    main()