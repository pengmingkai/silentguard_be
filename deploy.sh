#!/bin/bash

# IoT服务器部署脚本
# 适用于树莓派4B和其他Linux系统

set -e

echo "=========================================="
echo "IoT服务器部署脚本"
echo "=========================================="

# 检查Python版本
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python版本: $PYTHON_VERSION"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "安装pip3..."
    sudo apt update
    sudo apt install -y python3-pip
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装Python依赖包..."
pip install -r requirements.txt

# 检查MySQL（可选）
echo "检查MySQL服务..."
if command -v mysql &> /dev/null; then
    echo "✓ MySQL已安装"
    
    # 检查MySQL服务状态
    if systemctl is-active --quiet mysql; then
        echo "✓ MySQL服务正在运行"
    else
        echo "⚠ MySQL服务未运行，尝试启动..."
        sudo systemctl start mysql || echo "⚠ 无法启动MySQL服务，将使用SQLite"
    fi
else
    echo "⚠ MySQL未安装，将使用SQLite数据库"
    echo "如需安装MySQL，请运行: sudo apt install mysql-server"
fi

# 创建环境配置文件
if [ ! -f ".env" ]; then
    echo "创建环境配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置数据库连接信息"
fi

# 初始化数据库
echo "初始化数据库..."
python src/database_init.py

# 检查防火墙设置
echo "检查防火墙设置..."
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        echo "检测到UFW防火墙，确保端口5000已开放..."
        sudo ufw allow 5000/tcp || echo "⚠ 无法配置防火墙规则"
    fi
fi

# 创建systemd服务文件（可选）
echo "创建系统服务文件..."
cat > iot-server.service << EOF
[Unit]
Description=IoT Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "系统服务文件已创建: iot-server.service"
echo "要安装为系统服务，请运行:"
echo "  sudo cp iot-server.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable iot-server"
echo "  sudo systemctl start iot-server"

# 测试服务器
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo "启动服务器:"
echo "  source venv/bin/activate"
echo "  python src/main.py"
echo ""
echo "或者在后台运行:"
echo "  nohup python src/main.py > server.log 2>&1 &"
echo ""
echo "访问地址:"
echo "  本地: http://localhost:5000"
echo "  网络: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "API文档:"
echo "  /api - API信息"
echo "  /health - 健康检查"
echo "  /api/devices - 设备管理"
echo "  /api/microbit - micro:bit接口"
echo "  /api/esp32 - ESP32接口"
echo "=========================================="

