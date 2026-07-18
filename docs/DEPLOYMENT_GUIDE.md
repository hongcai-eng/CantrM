# 合同管理系统 - 部署指南

## 版本信息
- 版本号：v2.0
- 更新日期：2026-04-09
- Python 版本要求：3.8+

---

## 📦 部署前准备

### 1. 服务器环境要求
- Python 3.8 或更高版本
- pip 包管理器
- 至少 500MB 可用磁盘空间
- 建议内存：2GB+

### 2. 必需的系统包
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

---

## 🚀 部署步骤

### 步骤 1：上传文件到服务器

将以下文件和目录上传到服务器（如 `/var/www/cantrm/`）：

```
cantrm/
├── app.py                    # 主应用文件
├── models.py                 # 数据模型
├── migrate_db.py             # 数据库迁移脚本
├── requirements.txt          # Python 依赖
├── instance/
│   └── contracts.db          # 数据库文件（包含现有数据）
├── static/                   # 静态文件（Logo等）
│   ├── company_logo.jpg
│   ├── tenant_1_logo.jpg
│   ├── tenant_2_logo.jpg
│   └── ...
├── templates/                # HTML 模板
│   ├── base.html
│   ├── login.html
│   ├── index.html
│   └── ...
└── uploads/                  # 上传文件目录
```

### 步骤 2：创建虚拟环境并安装依赖

```bash
cd /var/www/cantrm

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 步骤 3：执行数据库迁移（重要！）

```bash
# 确保在虚拟环境中
python migrate_db.py
```

预期输出：
```
开始数据库迁移...
[OK] 创建 tenant_customer 表
[SKIP] User.customer_id 字段已存在
...
[OK] 创建 organization 表
[OK] user 表添加 organization_id 字段
数据库迁移完成！
```

### 步骤 4：配置应用

编辑 `app.py`，修改以下配置：

```python
# 修改 SECRET_KEY（重要！生产环境必须使用强密钥）
app.config['SECRET_KEY'] = '请替换为随机生成的长字符串'

# 如果需要修改端口
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # debug=False 用于生产环境
```

### 步骤 5：测试运行

```bash
# 测试启动
python app.py
```

访问 `http://服务器IP:5000` 测试是否正常。

---

## 🔒 生产环境部署（推荐）

### 方案 A：使用 Gunicorn + Nginx

#### 1. 安装 Gunicorn
```bash
pip install gunicorn
```

#### 2. 创建 Gunicorn 配置文件 `gunicorn_config.py`
```python
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
timeout = 120
accesslog = "/var/log/cantrm/access.log"
errorlog = "/var/log/cantrm/error.log"
loglevel = "info"
```

#### 3. 创建 systemd 服务文件 `/etc/systemd/system/cantrm.service`
```ini
[Unit]
Description=Contract Management System
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/cantrm
Environment="PATH=/var/www/cantrm/venv/bin"
ExecStart=/var/www/cantrm/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 4. 启动服务
```bash
# 创建日志目录
sudo mkdir -p /var/log/cantrm
sudo chown www-data:www-data /var/log/cantrm

# 启动服务
sudo systemctl daemon-reload
sudo systemctl start cantrm
sudo systemctl enable cantrm

# 查看状态
sudo systemctl status cantrm
```

#### 5. 配置 Nginx `/etc/nginx/sites-available/cantrm`
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名或IP

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/cantrm/static;
        expires 30d;
    }
}
```

#### 6. 启用 Nginx 配置
```bash
sudo ln -s /etc/nginx/sites-available/cantrm /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 方案 B：使用 Docker（可选）

创建 `Dockerfile`：
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python migrate_db.py

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "app:app"]
```

构建并运行：
```bash
docker build -t cantrm:v2.0 .
docker run -d -p 5000:5000 -v $(pwd)/instance:/app/instance cantrm:v2.0
```

---

## 🔐 安全建议

1. **修改默认密码**
   - superadmin 默认密码：654321（请立即修改）
   - 各租户管理员密码也应修改

2. **配置防火墙**
   ```bash
   # 只允许特定IP访问
   sudo ufw allow from 192.168.1.0/24 to any port 5000
   ```

3. **启用 HTTPS**
   - 使用 Let's Encrypt 免费证书
   - 或配置自签名证书

4. **定期备份数据库**
   ```bash
   # 备份脚本
   cp instance/contracts.db backups/contracts_$(date +%Y%m%d_%H%M%S).db
   ```

---

## 👥 默认账号

### 总超级管理员
- 账号：`superadmin`
- 密码：`654321`
- 权限：管理所有租户

### 租户超级管理员（示例）
- 创鑫汇智：`admin1` / `123456`
- 亿海立达：`admin2` / `123456`
- 中科跃达：`admin3` / `123456`

**⚠️ 重要：首次登录后请立即修改所有默认密码！**

---

## 📝 访问地址

部署完成后，同事可通过以下地址访问：

- **本地测试**：http://localhost:5000
- **局域网访问**：http://服务器IP:5000
- **域名访问**：http://your-domain.com（需配置 Nginx）

---

## 🐛 故障排查

### 问题 1：无法访问
```bash
# 检查服务状态
sudo systemctl status cantrm

# 查看日志
sudo journalctl -u cantrm -f
tail -f /var/log/cantrm/error.log
```

### 问题 2：数据库错误
```bash
# 重新执行迁移
python migrate_db.py

# 检查数据库文件权限
ls -l instance/contracts.db
chmod 664 instance/contracts.db
```

### 问题 3：静态文件无法加载
```bash
# 检查 static 目录权限
chmod -R 755 static/
```

---

## 📞 技术支持

如遇问题，请检查：
1. Python 版本是否 3.8+
2. 所有依赖是否正确安装
3. 数据库迁移是否成功执行
4. 防火墙是否开放端口
5. 日志文件中的错误信息

---

## 🎯 测试清单

部署完成后，请测试以下功能：

- [ ] 登录功能（superadmin 和租户管理员）
- [ ] 合同列表筛选和统计
- [ ] 组织管理功能
- [ ] 导出 Excel 功能（勾选导出项）
- [ ] 品牌显示（登录页和系统内页）
- [ ] 数据隔离（不同租户看不到对方数据）

---

## 📊 本次更新内容

### 新增功能
1. ✅ 登录页和系统内页品牌显示
2. ✅ 合同列表筛选统计汇总
3. ✅ 组织结构管理（增删改查、人员调动）
4. ✅ 修复合同类型筛选问题
5. ✅ 修复统计导出勾选问题

### 数据库变更
- 新增 `organization` 表
- `user` 表新增 `organization_id` 字段
- `tenant_customer` 表新增 `company_name` 和 `logo_file` 字段

### 已删除
- 删除了 `admin` 用户（密码为 "1" 的旧账号）

---

**部署完成后，请通知同事使用 Ctrl+F5 强制刷新浏览器清除缓存！**
