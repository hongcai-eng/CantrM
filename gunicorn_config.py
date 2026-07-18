# Gunicorn 配置文件 - 生产环境

# 绑定地址和端口
bind = "127.0.0.1:5000"

# 工作进程数（建议：CPU核心数 * 2 + 1）
workers = 4

# 工作模式
worker_class = "sync"

# 超时时间（秒）
timeout = 120

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 日志配置
accesslog = "/var/log/cantrm/access.log"
errorlog = "/var/log/cantrm/error.log"
loglevel = "info"

# 进程名称
proc_name = "cantrm"

# 守护进程（设为 False，由 systemd 管理）
daemon = False

# 预加载应用（提高性能）
preload_app = True

# 优雅重启超时
graceful_timeout = 30

# 保持连接时间
keepalive = 5
