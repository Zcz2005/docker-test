# CTyun OOS/ZOS Python SDK

The OOS client (`oos` / `ooscore`) is not available on PyPI. Install it from the official SDK package:

1. Download the Python 3.x SDK from [天翼云 ZOS 对象存储文档](https://www.ctyun.cn/document/10026735/10110276)
2. Extract the archive into this `sdk/` directory
3. Install dependencies:

```bash
cd sdk
pip install -r requirements.txt
sh install_extension.sh   # Linux/macOS
# or: python install_extension_window.py   # Windows
```

After installation, verify:

```bash
python -c "import oos; import ooscore; print('OOS SDK OK')"
```
