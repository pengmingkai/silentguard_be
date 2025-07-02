# IoT服务器 - Python Flask RESTful API

一个功能完整的IoT服务器，专为树莓派4B设计，支持micro:bit和ESP32设备的统一管理和数据收集。

## 🌟 项目特性

- **多设备支持**: 同时管理2块micro:bit和1块ESP32设备
- **RESTful API**: 完整的HTTP API接口，支持前端应用集成
- **数据库支持**: MySQL/SQLite双重支持，自动回退机制
- **实时监控**: 设备状态监控和传感器数据实时收集
- **Web控制台**: 内置Web界面，直观管理所有设备
- **高度复用**: 统一的API设计，便于扩展和维护
- **跨平台**: 支持树莓派、Linux、Windows等多种平台

## 📋 系统要求

### 服务器端
- 树莓派4B (推荐) 或其他Linux系统
- Python 3.8+
- 2GB+ RAM
- 8GB+ 存储空间
- 网络连接

### 客户端设备
- **micro:bit**: BBC micro:bit v1/v2 + WiFi模块(可选)
- **ESP32**: ESP32开发板 + 传感器模块

## 🚀 快速开始

### 1. 克隆项目


```bash
git clone <repository-url>
cd iot-server
```

### 2. 自动部署

```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. 手动安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库连接

# 初始化数据库
python src/database_init.py

# 启动服务器
python src/main.py
```

### 4. 访问服务

- **Web控制台**: http://your-pi-ip:5000
- **API文档**: http://your-pi-ip:5000/api
- **健康检查**: http://your-pi-ip:5000/health

## ⚙️ 配置说明

### 环境变量配置 (.env)

```bash
# Flask环境
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# MySQL数据库 (可选)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=iot_server

# 设备限制
MAX_MICROBIT_DEVICES=2
MAX_ESP32_DEVICES=1
```

### MySQL数据库设置 (可选)

如果使用MySQL数据库，请先安装并配置：

```bash
# 安装MySQL
sudo apt update
sudo apt install mysql-server

# 配置MySQL
sudo mysql_secure_installation

# 创建数据库用户
sudo mysql -u root -p
CREATE DATABASE iot_server CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'iot_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON iot_server.* TO 'iot_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 📡 API接口文档

### 基础信息

- **基础URL**: `http://your-server:5000/api`
- **数据格式**: JSON
- **认证方式**: 暂无 (可扩展)

### 通用响应格式

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 设备管理接口

#### 获取所有设备
```http
GET /api/devices
```

**查询参数**:
- `type`: 设备类型 (microbit, esp32)
- `status`: 设备状态 (online, offline, error)

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "device_id": "microbit_001",
      "device_type": "microbit",
      "name": "客厅传感器",
      "status": "online",
      "last_seen": "2024-01-01T12:00:00Z"
    }
  ],
  "count": 1
}
```

#### 获取设备详情
```http
GET /api/devices/{device_id}
```

#### 更新设备状态
```http
PUT /api/devices/{device_id}/status
```

**请求体**:
```json
{
  "status": "online"
}
```

#### 获取设备数据
```http
GET /api/devices/{device_id}/data
```

**查询参数**:
- `sensor_type`: 传感器类型
- `limit`: 数据条数 (默认50)
- `hours`: 最近N小时的数据

#### 获取设备统计
```http
GET /api/devices/stats
```

### 数据管理接口

#### 添加传感器数据
```http
POST /api/data
```

**请求体**:
```json
{
  "device_id": "esp32_001",
  "sensor_type": "temperature",
  "value": 25.6,
  "unit": "°C",
  "metadata": {
    "location": "室内"
  }
}
```

#### 批量添加数据
```http
POST /api/data/batch
```

**请求体**:
```json
{
  "data_list": [
    {
      "device_id": "esp32_001",
      "sensor_type": "temperature",
      "value": 25.6,
      "unit": "°C"
    },
    {
      "device_id": "esp32_001",
      "sensor_type": "humidity",
      "value": 60.2,
      "unit": "%"
    }
  ]
}
```

#### 查询传感器数据
```http
GET /api/data/query
```

**查询参数**:
- `device_id`: 设备ID (必需)
- `sensor_type`: 传感器类型
- `start_time`: 开始时间 (ISO格式)
- `end_time`: 结束时间 (ISO格式)
- `limit`: 数据条数

#### 获取最新数据
```http
GET /api/data/latest
```

#### 获取数据统计
```http
GET /api/data/statistics
```

### micro:bit专用接口

#### 注册设备
```http
POST /api/microbit/register
```

**请求体**:
```json
{
  "device_id": "microbit_001",
  "name": "客厅传感器",
  "description": "BBC micro:bit with sensors"
}
```

#### 心跳检测
```http
POST /api/microbit/heartbeat
GET /api/microbit/heartbeat?device_id=microbit_001
```

#### 上传传感器数据
```http
POST /api/microbit/data
```

**请求体**:
```json
{
  "device_id": "microbit_001",
  "temperature": 25.6,
  "light": 128,
  "accelerometer": {
    "x": 0.1,
    "y": 0.2,
    "z": 9.8
  },
  "compass": 180,
  "button_a": false,
  "button_b": true
}
```

#### 发送命令
```http
POST /api/microbit/command
```

**请求体**:
```json
{
  "device_id": "microbit_001",
  "command": "display_text",
  "text": "Hello World"
}
```

**支持的命令**:
- `display_text`: 显示文本
- `display_icon`: 显示图标
- `clear_display`: 清空显示
- `show_temperature`: 显示温度
- `show_light`: 显示光照
- `set_pixel`: 设置像素点

#### 获取设备状态
```http
GET /api/microbit/status/{device_id}
```

#### 列出所有micro:bit设备
```http
GET /api/microbit/devices
```

### ESP32专用接口

#### 注册设备
```http
POST /api/esp32/register
```

**请求体**:
```json
{
  "device_id": "esp32_001",
  "name": "环境监测站",
  "description": "ESP32 with multiple sensors",
  "wifi_ssid": "MyWiFi",
  "ip_address": "192.168.1.100",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "firmware_version": "1.0.0",
  "sensors": ["temperature", "humidity", "pressure"],
  "capabilities": ["wifi", "gpio", "pwm"]
}
```

#### 心跳检测
```http
POST /api/esp32/heartbeat
```

**请求体**:
```json
{
  "device_id": "esp32_001",
  "system_info": {
    "free_heap": 200000,
    "wifi_rssi": -45,
    "uptime": 3600000
  }
}
```

#### 上传传感器数据
```http
POST /api/esp32/data
```

**请求体**:
```json
{
  "device_id": "esp32_001",
  "temperature": 25.6,
  "humidity": 60.2,
  "pressure": 1013.25,
  "light": 500,
  "motion": false,
  "distance": 150.5,
  "analog_inputs": {
    "A0": 2.5,
    "A1": 1.8
  },
  "digital_inputs": {
    "D2": true,
    "D3": false
  },
  "system_status": {
    "free_heap": 200000,
    "wifi_rssi": -45
  }
}
```

#### 设备控制
```http
POST /api/esp32/control
```

**请求体**:
```json
{
  "device_id": "esp32_001",
  "action": "gpio_write",
  "pin": 2,
  "value": 1
}
```

**支持的控制动作**:
- `gpio_write`: GPIO输出
- `pwm_write`: PWM输出
- `dac_write`: DAC输出
- `servo_write`: 舵机控制
- `led_control`: LED控制
- `relay_control`: 继电器控制
- `restart`: 重启设备
- `deep_sleep`: 深度睡眠
- `wifi_reconnect`: WiFi重连

#### 配置管理
```http
GET /api/esp32/config/{device_id}
PUT /api/esp32/config/{device_id}
```

#### 固件更新
```http
POST /api/esp32/firmware
```

#### 获取设备状态
```http
GET /api/esp32/status/{device_id}
```

#### 列出所有ESP32设备
```http
GET /api/esp32/devices
```

## 🔧 客户端代码使用指南

### micro:bit客户端

项目提供了三种micro:bit客户端实现：

#### 1. 基础版本 (main.py)
适用于有WiFi模块或无线电通信的micro:bit：

```python
# 配置设备信息
DEVICE_ID = "microbit_001"
DEVICE_NAME = "MicroBit Living Room"
SERVER_URL = "http://192.168.1.100:5000"

# 创建并运行客户端
client = MicroBitIoTClient(DEVICE_ID, DEVICE_NAME)
client.run()
```

#### 2. WiFi版本 (wifi_client.py)
适用于配备ESP8266/ESP32 WiFi模块的micro:bit：

```python
# WiFi配置
WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"
SERVER_IP = "192.168.1.100"

# 运行WiFi客户端
client = WiFiMicroBitClient()
client.run()
```

#### 3. 无线电版本 (radio_client.py)
适用于通过无线电与网关通信的micro:bit：

```python
# 无线电配置
DEVICE_ID = "microbit_radio_001"
RADIO_CHANNEL = 7
GATEWAY_ID = "gateway_001"

# 运行无线电客户端
client = RadioMicroBitClient()
client.run()
```

### ESP32客户端

项目提供了两种ESP32客户端实现：

#### 1. Arduino IDE版本 (esp32_iot_client.ino)

```cpp
// WiFi配置
const char* ssid = "YourWiFiName";
const char* password = "YourWiFiPassword";

// 服务器配置
const char* serverURL = "http://192.168.1.100:5000";
const String deviceID = "esp32_001";

// 传感器引脚配置
#define DHT_PIN 4
#define MOTION_PIN 5
#define LIGHT_PIN A0
```

**所需库**:
- WiFi
- HTTPClient
- ArduinoJson
- DHT sensor library
- BMP280 library

#### 2. MicroPython版本 (main.py)

```python
# 配置信息
WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"
SERVER_URL = "http://192.168.1.100:5000"
DEVICE_ID = "esp32_micropython_001"

# 运行客户端
client = ESP32IoTClient()
client.run()
```

#### 3. 网关版本 (microbit_gateway.py)
用于接收micro:bit无线电信号并转发到服务器：

```python
# 网关配置
GATEWAY_ID = "gateway_001"
UART_TX = 17
UART_RX = 16

# 运行网关
gateway = MicroBitGateway()
gateway.run()
```

## 🔌 硬件连接指南

### micro:bit连接

#### 基础传感器 (内置)
- 温度传感器: 内置
- 光照传感器: 内置
- 加速度计: 内置
- 指南针: 内置
- 按钮: A, B

#### WiFi模块连接 (可选)
```
micro:bit -> ESP8266/ESP32
GND      -> GND
3V       -> 3.3V
Pin 0    -> TX
Pin 1    -> RX
```

### ESP32连接

#### DHT22温湿度传感器
```
ESP32 -> DHT22
3.3V  -> VCC
GND   -> GND
GPIO4 -> DATA
```

#### BMP280气压传感器
```
ESP32 -> BMP280
3.3V  -> VCC
GND   -> GND
GPIO21-> SDA
GPIO22-> SCL
```

#### 超声波距离传感器
```
ESP32 -> HC-SR04
5V    -> VCC
GND   -> GND
GPIO18-> Trig
GPIO19-> Echo
```

#### 其他传感器
```
ESP32 -> 传感器
GPIO5 -> PIR运动传感器
GPIO36-> 光敏电阻 (ADC)
GPIO2 -> LED指示灯
GPIO23-> 继电器控制
```

## 🚀 部署到生产环境

### 使用systemd服务

1. 复制服务文件：
```bash
sudo cp iot-server.service /etc/systemd/system/
sudo systemctl daemon-reload
```

2. 启用并启动服务：
```bash
sudo systemctl enable iot-server
sudo systemctl start iot-server
```

3. 查看服务状态：
```bash
sudo systemctl status iot-server
sudo journalctl -u iot-server -f
```

### 使用Nginx反向代理

1. 安装Nginx：
```bash
sudo apt install nginx
```

2. 配置Nginx：
```bash
sudo nano /etc/nginx/sites-available/iot-server
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. 启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/iot-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 防火墙配置

```bash
# 开放HTTP端口
sudo ufw allow 80/tcp
sudo ufw allow 5000/tcp

# 开放SSH端口 (如果需要)
sudo ufw allow 22/tcp

# 启用防火墙
sudo ufw enable
```

## 📊 监控和日志

### 日志文件位置
- 应用日志: `server.log`
- 系统服务日志: `journalctl -u iot-server`
- Nginx日志: `/var/log/nginx/`

### 健康检查
```bash
# 检查服务状态
curl http://localhost:5000/health

# 检查API状态
curl http://localhost:5000/api

# 检查设备统计
curl http://localhost:5000/api/devices/stats
```

### 性能监控

可以使用以下工具监控系统性能：
- `htop`: 系统资源监控
- `iotop`: 磁盘I/O监控
- `nethogs`: 网络流量监控

## 🔧 故障排除

### 常见问题

#### 1. 数据库连接失败
```
错误: MySQL连接失败
解决: 检查MySQL服务状态，确认用户名密码正确
```

#### 2. 设备无法连接
```
错误: 设备注册失败
解决: 检查网络连接，确认服务器IP地址正确
```

#### 3. 传感器数据异常
```
错误: 传感器读取失败
解决: 检查硬件连接，确认传感器工作正常
```

#### 4. 内存不足
```
错误: 系统内存不足
解决: 增加swap空间，优化代码内存使用
```

### 调试模式

启用调试模式获取详细日志：

```bash
export FLASK_ENV=development
python src/main.py
```

### 日志级别配置

在代码中添加日志配置：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置

1. Fork项目
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 提交Pull Request

### 代码规范

- 使用Python PEP 8代码风格
- 添加适当的注释和文档
- 编写单元测试
- 确保所有测试通过

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如有问题或建议，请：

1. 查看文档和FAQ
2. 搜索已有的Issue
3. 创建新的Issue
4. 联系项目维护者

## 🙏 致谢

感谢以下开源项目：

- [Flask](https://flask.palletsprojects.com/) - Web框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - 数据库ORM
- [micro:bit](https://microbit.org/) - 教育开发板
- [ESP32](https://www.espressif.com/) - IoT开发平台

---

**Happy Coding! 🚀**

