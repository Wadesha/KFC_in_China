# KFC_in_China · 肯德基中国门店分布（数据工程化示例）

采集 KFC 全国门店信息 → 地理编码得到经纬度 → 工程化整理 → **网页看板展示门店分布**。
本项目重点演示一套**结构化、可复现、密钥安全**的数据工程目录组织方式。

> ⚠️ 数据仅用于技术演示与学习，门店信息来自公开渠道，底图 GeoJSON 版权归第三方原作者（见文末声明）。请勿用于商业用途。

---

## 目录结构

```
KFC_in_China/
├── README.md
├── .gitignore            # 忽略 .env / 第三方缓存 / 生成物
├── .env.example          # 环境变量模板（复制为 .env 后填写自己的 Key）
├── requirements.txt      # Python 依赖
├── LICENSE
├── assets/
│   └── geo/
│       └── provinces.geojson   # 34 个省级行政区边界（由第三方数据合并，已提交）
├── data/
│   ├── raw/              # 原始采集：kfc_stores.json、test_*、kfc_stores_amap.csv
│   └── processed/        # 成品：kfc_stores_with_coords.csv（完整 11885 家含坐标）、kfc_stores_sample.csv
├── scripts/              # 全部脚本（已重命名、脱敏）
│   ├── common.py         # 极简 .env 加载器（无第三方依赖）
│   ├── collect_stores.py       # 采集 KFC 门店（原 fetch_kfc.py）
│   ├── collect_stores_amap.py  # 高德方式采集（原 fetch_kfc_locations.py）
│   ├── geocode.py              # 地理编码（原 geocode_kfc.py，Key 取自环境变量）
│   ├── fetch_districts.py      # 拉取区县边界（原 download_geojson.py）
│   ├── fetch_geojson.py        # 下载 ChinaGeoJson（原 download_china_geojson.py）
│   ├── generate_plots.py       # 生成分城市散点 PNG（原 generate_scatter_plots.py）
│   ├── build_geo.py            # 合并 34 个省级 GeoJSON -> assets/geo/provinces.geojson
│   └── prepare_web_data.py     # 门店 CSV -> web 数据，并用点在多边形内算法归属省份
├── web/                  # 网页展示（纯前端，无需后端 / 密钥）
│   ├── index.html
│   ├── app.js
│   └── assets/
│       └── stores.json        # 前端数据（11885 家门店坐标 + 省份/城市统计）
└── archive/
    └── legacy_web/       # 旧网页（参考，非入口）
```

---

## 环境准备

```bash
# 1. 安装依赖（建议在虚拟环境中）
pip install -r requirements.txt

# 2. 配置密钥：复制模板并填入你自己的 Key
cp .env.example .env
#   然后编辑 .env：
#   TENCENT_MAP_API_KEYS=你的腾讯地图key1,你的key2
#   AMAP_API_KEY=你的高德key
```

> `.env` 已被 `.gitignore` 忽略，**绝不会提交**。所有脚本统一从环境变量读取 Key，
> 源码中不再出现任何硬编码密钥。

---

## 数据流程（Pipeline）

```bash
# ① 采集门店（写入 data/raw/kfc_stores.json）
python scripts/collect_stores.py

# ② 地理编码：地址 -> 经纬度（写入 data/processed/kfc_stores_with_coords.csv）
python scripts/geocode.py            # 全量；--test 仅跑前 5 家验证
python scripts/geocode.py --test

# ③ 生成分城市散点图（可选，输出到 scatter_plots_extended/，已 gitignore）
python scripts/generate_plots.py

# ④ 合并省级 GeoJSON（首次需先：python scripts/fetch_geojson.py 下载源数据）
python scripts/build_geo.py

# ⑤ 生成网页数据（省份归属、统计），输出 web/assets/stores.json
python scripts/prepare_web_data.py
```

> 仓库已自带 `assets/geo/provinces.geojson` 与 `web/assets/stores.json`，
> 因此**克隆后无需重跑脚本即可直接查看网页**。

---

## 网页展示

网页为纯前端（ECharts + 本地 GeoJSON/JSON），展示：
- **门店分布地图**：省份按门店密度着色 + 单店坐标散点（可缩放/拖拽）
- **统计卡片**：门店总数、覆盖省级行政区、覆盖城市、门店最多省份
- **条形图**：省份 TOP15、城市 TOP15

### 本地预览
因浏览器安全策略，`file://` 直接打开无法 `fetch` 本地 JSON，请起一个本地服务器：

```bash
# 在项目根目录执行（保持运行），浏览器访问 http://localhost:8000/web/index.html
python -m http.server 8000
```

### GitHub Pages
将本仓库开启 Pages（Source 选 `main` 分支根目录）后，访问
`https://Wadesha.github.io/KFC_in_China/web/index.html` 即可。

---

## 当前数据概览（已提交快照）

| 指标 | 数值 |
|---|---|
| 门店总数 | 11,885 |
| 覆盖省级行政区 | 33（台湾省无 KFC，故 0 家） |
| 覆盖城市 | 230 |
| 门店最多省份 | 广东省（1,822 家） |
| 门店最多城市 | 见网页「城市 TOP15」 |

省份归属通过**坐标点在省级多边形内的几何判定**得到，不依赖任何在线 API。

---

## 隐私与安全

- 所有 API Key（腾讯地图 / 高德）一律通过 `.env` + 环境变量注入，**源码零硬编码**。
- `.gitignore` 已忽略 `.env`、`china_geojson/`（第三方数据缓存）、`scatter_plots*/`（生成物）、`*.log`。
- 提交前已全量扫描，确认仓库内不含任何密钥或 Token。
- 密钥仅存在于你本地的 `.env` 与运行环境变量中。

---

## 第三方数据声明

- 底图 `assets/geo/provinces.geojson` 由 [zhChuXiao/ChinaGeoJson](https://github.com/zhChuXiao/ChinaGeoJson)
  的中国行政区划 GeoJSON 合并而来，数据版权归原作者所有，本项目仅作展示用途。
- 本项目代码以 MIT 协议开源（见 `LICENSE`）。
