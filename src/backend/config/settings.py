# 数据质量评估平台配置

# Flask 应用配置
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True

# 目录配置（相对于项目根目录）
UPLOAD_FOLDER = "output/data"
REPORTS_FOLDER = "output/reports"
TEMP_FOLDER = "temp"

# Great Expectations 配置
GE_VERSION = "1.16.0"

# 支持的文件格式
ALLOWED_EXTENSIONS = ["csv", "xlsx", "xls"]

# 报告配置
REPORT_TEMPLATE = "report_template.html"
