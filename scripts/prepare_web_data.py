"""把门店坐标数据转换为网页可用的 JSON，并用「点在多边形内」算法给每家店归属省份。

输入：
    data/processed/kfc_stores_with_coords.csv   （门店 + 经纬度）
    assets/geo/provinces.geojson                 （34 个省级边界，由 build_geo.py 生成）
输出：
    web/assets/stores.json   { meta, stores[], province_counts[], city_counts[] }

省份归属完全基于坐标几何计算，无需任何外部 API / 密钥。
"""
import os
import csv
import json
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_IN = os.path.join(ROOT, "data", "processed", "kfc_stores_with_coords.csv")
GEO_IN = os.path.join(ROOT, "assets", "geo", "provinces.geojson")
OUT = os.path.join(ROOT, "web", "assets", "stores.json")


# ---------- 点在多边形内（射线法） ----------
def point_in_ring(lng, lat, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (
            lng < (xj - xi) * (lat - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def point_in_polygon(lng, lat, poly):
    # poly: [outer_ring, hole1, hole2, ...]
    if not point_in_ring(lng, lat, poly[0]):
        return False
    for hole in poly[1:]:
        if point_in_ring(lng, lat, hole):
            return False
    return True


def point_in_geometry(lng, lat, geom):
    t = geom.get("type")
    if t == "Polygon":
        return point_in_polygon(lng, lat, geom["coordinates"])
    if t == "MultiPolygon":
        return any(point_in_polygon(lng, lat, p) for p in geom["coordinates"])
    return False


def load_provinces(path):
    with open(path, "r", encoding="utf-8") as f:
        fc = json.load(f)
    provinces = []
    for feat in fc.get("features", []):
        geom = feat.get("geometry") or {}
        name = feat.get("properties", {}).get("name", "")
        # 预计算 bbox 加速判定
        minlng, minlat, maxlng, maxlat = 180, 90, -180, -90
        polys = geom["coordinates"] if geom.get("type") == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for ring in poly:
                for pt in ring:
                    if pt[0] < minlng:
                        minlng = pt[0]
                    if pt[0] > maxlng:
                        maxlng = pt[0]
                    if pt[1] < minlat:
                        minlat = pt[1]
                    if pt[1] > maxlat:
                        maxlat = pt[1]
        provinces.append({"name": name, "geom": geom, "bbox": (minlng, minlat, maxlng, maxlat)})
    return provinces


def province_of(lng, lat, provinces):
    for p in provinces:
        minlng, minlat, maxlng, maxlat = p["bbox"]
        if lng < minlng or lng > maxlng or lat < minlat or lat > maxlat:
            continue
        if point_in_geometry(lng, lat, p["geom"]):
            return p["name"]
    return "未知"


def main():
    if not os.path.exists(GEO_IN):
        raise SystemExit(f"未找到 {GEO_IN}，请先运行：python scripts/build_geo.py")
    provinces = load_provinces(GEO_IN)

    stores = []
    with open(CSV_IN, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row.get("lat") or 0)
                lng = float(row.get("lng") or 0)
            except ValueError:
                continue
            if lat == 0 and lng == 0:
                continue
            city = (row.get("cityName") or "").strip()
            name = (row.get("storename") or "").strip()
            address = (row.get("address") or "").strip()
            province = province_of(lng, lat, provinces)
            stores.append({
                "name": name,
                "city": city,
                "province": province,
                "address": address,
                "lng": round(lng, 6),
                "lat": round(lat, 6),
            })

    province_counter = Counter(s["province"] for s in stores)
    city_counter = Counter(s["city"] for s in stores if s["city"])

    province_counts = [
        {"name": k, "value": v} for k, v in province_counter.most_common()
    ]
    city_counts = [
        {"name": k, "value": v} for k, v in city_counter.most_common(30)
    ]

    result = {
        "meta": {
            "total": len(stores),
            "provinces_covered": len([k for k in province_counter if k != "未知"]),
            "cities_covered": len(city_counter),
            "generated_from": os.path.relpath(CSV_IN, ROOT),
        },
        "stores": stores,
        "province_counts": province_counts,
        "city_counts": city_counts,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    print(f"已写入 {len(stores)} 家门店 -> {OUT}")
    print(f"覆盖省份 {result['meta']['provinces_covered']} 个，城市 {result['meta']['cities_covered']} 个")
    print(f"归属为『未知』的门店：{province_counter.get('未知', 0)} 家")


if __name__ == "__main__":
    main()
