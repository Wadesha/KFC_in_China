"""合并 34 个省级 GeoJSON 为单个 provinces.geojson（供网页地图与省份归属使用）。

重要：province/ 目录下每个文件（如 广东省.json）内部包含的是该省下辖的
市/区县级要素，其 feature 名并非省名。因此这里按「文件名=省名」把每个文件内
的所有几何合并为「一个省 = 一个 MultiPolygon 要素」，最终输出 34 个省级要素。

数据源（本地缓存，已被 .gitignore 忽略）：
    china_geojson/ChinaGeoJson-master/province/*.json
如需重新获取，运行：python scripts/fetch_geojson.py
"""
import os
import json
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "china_geojson", "ChinaGeoJson-master", "province")
OUT = os.path.join(ROOT, "assets", "geo", "provinces.geojson")


def collect_polygons(geom):
    """把 Polygon / MultiPolygon 的几何展开为一组多边形（每项为 rings 列表）。"""
    t = geom.get("type")
    if t == "Polygon":
        return [geom["coordinates"]]
    if t == "MultiPolygon":
        return list(geom["coordinates"])
    return []


def main():
    if not os.path.isdir(SRC_DIR):
        raise SystemExit(
            f"未找到省级 GeoJSON 目录：{SRC_DIR}\n"
            "请先运行：python scripts/fetch_geojson.py 下载 ChinaGeoJson 数据。"
        )
    features = []
    for path in sorted(glob.glob(os.path.join(SRC_DIR, "*.json"))):
        province_name = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        src_features = d.get("features", []) if d.get("type") == "FeatureCollection" else [d]
        polygons = []
        for feat in src_features:
            geom = (feat or {}).get("geometry") or {}
            if geom.get("type") in ("Polygon", "MultiPolygon"):
                polygons.extend(collect_polygons(geom))
        if not polygons:
            continue
        merged = {
            "type": "Feature",
            "properties": {"name": province_name},
            "geometry": {"type": "MultiPolygon", "coordinates": polygons},
        }
        features.append(merged)
    fc = {"type": "FeatureCollection", "features": features}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    print(f"已合并 {len(features)} 个省级要素 -> {OUT}")


if __name__ == "__main__":
    main()
