# micro:bit IoT客户端主程序
# 适用于BBC micro:bit v2 (支持WiFi模块)
# 需要配合ESP8266/ESP32 WiFi模块使用

from microbit import *
import radio
import json
import time

# 配置信息
SERVER_URL = "http://192.168.1.100:5000"  # 替换为您的服务器IP
DEVICE_ID = "microbit_001"  # 设备唯一标识符
DEVICE_NAME = "MicroBit Living Room"

# WiFi模块通信配置（通过串口）
WIFI_ENABLED = False  # 如果有WiFi模块则设为True

class MicroBitIoTClient:
    def __init__(self, device_id, device_name):
        self.device_id = device_id
        self.device_name = device_name
        self.registered = False
        self.last_heartbeat = 0
        self.heartbeat_interval = 30000  # 30秒心跳间隔
        
        # 初始化显示
        display.show(Image.HEART)
        sleep(1000)
        display.clear()
        
        # 初始化无线电（用于本地通信）
        radio.on()
        radio.config(channel=7, power=7)
        
        print(f"MicroBit IoT Client initialized: {device_id}")
    
    def register_device(self):
        """注册设备到服务器"""
        try:
            if WIFI_ENABLED:
                # 通过WiFi模块注册
                registration_data = {
                    "device_id": self.device_id,
                    "name": self.device_name,
                    "description": "BBC micro:bit with sensors"
                }
                
                # 发送注册请求（需要WiFi模块支持）
                response = self.send_http_request("POST", "/api/microbit/register", registration_data)
                if response and response.get("success"):
                    self.registered = True
                    display.show(Image.YES)
                    print("Device registered successfully")
                else:
                    display.show(Image.NO)
                    print("Registration failed")
            else:
                # 无WiFi模块时，通过无线电广播设备信息
                radio_data = {
                    "type": "register",
                    "device_id": self.device_id,
                    "name": self.device_name
                }
                radio.send(json.dumps(radio_data))
                self.registered = True
                display.show("R")  # 显示R表示已广播注册信息
                
        except Exception as e:
            print(f"Registration error: {e}")
            display.show(Image.SAD)
    
    def read_sensors(self):
        """读取所有传感器数据"""
        sensor_data = {}
        
        try:
            # 温度传感器
            sensor_data["temperature"] = temperature()
            
            # 光照传感器
            sensor_data["light"] = display.read_light_level()
            
            # 加速度计
            sensor_data["accelerometer"] = {
                "x": accelerometer.get_x(),
                "y": accelerometer.get_y(),
                "z": accelerometer.get_z()
            }
            
            # 指南针
            try:
                sensor_data["compass"] = compass.heading()
            except:
                # 指南针可能需要校准
                pass
            
            # 按钮状态
            sensor_data["button_a"] = button_a.is_pressed()
            sensor_data["button_b"] = button_b.is_pressed()
            
        except Exception as e:
            print(f"Sensor reading error: {e}")
        
        return sensor_data
    
    def send_sensor_data(self, sensor_data):
        """发送传感器数据到服务器"""
        try:
            if WIFI_ENABLED:
                # 通过WiFi发送到服务器
                data_payload = {
                    "device_id": self.device_id,
                    **sensor_data
                }
                
                response = self.send_http_request("POST", "/api/microbit/data", data_payload)
                if response and response.get("success"):
                    display.set_pixel(4, 0, 9)  # 右上角点亮表示发送成功
                    return True
                else:
                    display.set_pixel(4, 0, 0)  # 右上角熄灭表示发送失败
                    return False
            else:
                # 通过无线电发送
                radio_data = {
                    "type": "sensor_data",
                    "device_id": self.device_id,
                    "data": sensor_data,
                    "timestamp": time.ticks_ms()
                }
                radio.send(json.dumps(radio_data))
                display.set_pixel(4, 0, 5)  # 中等亮度表示无线电发送
                return True
                
        except Exception as e:
            print(f"Data sending error: {e}")
            return False
    
    def send_heartbeat(self):
        """发送心跳信号"""
        try:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, self.last_heartbeat) >= self.heartbeat_interval:
                if WIFI_ENABLED:
                    # WiFi心跳
                    response = self.send_http_request("POST", "/api/microbit/heartbeat", 
                                                    {"device_id": self.device_id})
                    if response and response.get("success"):
                        display.set_pixel(0, 0, 9)  # 左上角点亮表示在线
                    else:
                        display.set_pixel(0, 0, 0)  # 左上角熄灭表示离线
                else:
                    # 无线电心跳
                    radio_data = {
                        "type": "heartbeat",
                        "device_id": self.device_id,
                        "timestamp": current_time
                    }
                    radio.send(json.dumps(radio_data))
                    display.set_pixel(0, 0, 5)  # 中等亮度表示无线电心跳
                
                self.last_heartbeat = current_time
                
        except Exception as e:
            print(f"Heartbeat error: {e}")
    
    def send_http_request(self, method, endpoint, data=None):
        """发送HTTP请求（需要WiFi模块支持）"""
        # 这里需要实现与WiFi模块的串口通信
        # 具体实现取决于使用的WiFi模块类型
        # 示例代码框架：
        try:
            if data:
                # 构建HTTP请求
                url = f"{SERVER_URL}{endpoint}"
                # 通过串口发送AT命令到WiFi模块
                # 返回解析后的响应
                pass
            return None
        except Exception as e:
            print(f"HTTP request error: {e}")
            return None
    
    def handle_commands(self):
        """处理来自服务器的命令"""
        try:
            # 检查无线电消息
            message = radio.receive()
            if message:
                try:
                    command_data = json.loads(message)
                    if command_data.get("target") == self.device_id:
                        self.execute_command(command_data)
                except:
                    pass  # 忽略无效消息
                    
        except Exception as e:
            print(f"Command handling error: {e}")
    
    def execute_command(self, command_data):
        """执行收到的命令"""
        try:
            command = command_data.get("command")
            
            if command == "display_text":
                text = command_data.get("text", "Hello")
                display.scroll(text)
            
            elif command == "display_icon":
                icon_name = command_data.get("icon", "HEART")
                if hasattr(Image, icon_name):
                    display.show(getattr(Image, icon_name))
            
            elif command == "clear_display":
                display.clear()
            
            elif command == "show_temperature":
                temp = temperature()
                display.scroll(f"T:{temp}C")
            
            elif command == "show_light":
                light = display.read_light_level()
                display.scroll(f"L:{light}")
            
            elif command == "set_pixel":
                pixel_data = command_data.get("pixel_data", {})
                x = pixel_data.get("x", 0)
                y = pixel_data.get("y", 0)
                brightness = pixel_data.get("brightness", 9)
                display.set_pixel(x, y, brightness)
            
            print(f"Executed command: {command}")
            
        except Exception as e:
            print(f"Command execution error: {e}")
    
    def run(self):
        """主运行循环"""
        print("Starting MicroBit IoT Client...")
        
        # 注册设备
        self.register_device()
        sleep(2000)
        
        # 主循环
        while True:
            try:
                # 读取传感器数据
                sensor_data = self.read_sensors()
                
                # 发送数据
                self.send_sensor_data(sensor_data)
                
                # 发送心跳
                self.send_heartbeat()
                
                # 处理命令
                self.handle_commands()
                
                # 显示状态
                if button_a.is_pressed() and button_b.is_pressed():
                    # 同时按下A+B显示设备ID
                    display.scroll(self.device_id)
                elif button_a.is_pressed():
                    # 按下A显示温度
                    temp = temperature()
                    display.scroll(f"{temp}C")
                elif button_b.is_pressed():
                    # 按下B显示光照
                    light = display.read_light_level()
                    display.scroll(f"L{light}")
                
                # 等待一段时间
                sleep(5000)  # 5秒间隔
                
            except Exception as e:
                print(f"Main loop error: {e}")
                display.show(Image.SAD)
                sleep(1000)
                display.clear()

# 创建客户端实例并运行
if __name__ == "__main__":
    client = MicroBitIoTClient(DEVICE_ID, DEVICE_NAME)
    client.run()

