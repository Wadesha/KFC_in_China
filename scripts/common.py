"""公共工具：极简 .env 加载器（无第三方依赖）。

用于在脚本运行前把项目根目录下的 .env 文件注入环境变量，
避免把密钥（腾讯地图 / 高德 API Key）硬编码进源码。
"""
import os


def load_dotenv(path=".env"):
    """读取 .env 文件并写入 os.environ（仅当变量尚未设置时）。"""
    # 允许从 scripts/ 目录向上查找根目录的 .env
    candidates = [
        path,
        os.path.join(os.path.dirname(__file__), "..", path),
        os.path.join(os.path.dirname(__file__), path),
    ]
    target = next((p for p in candidates if os.path.exists(p)), None)
    if not target:
        return
    with open(target, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
