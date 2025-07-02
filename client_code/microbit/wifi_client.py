# micro:bit WiFi客户端（配合ESP8266/ESP32 WiFi模块）
# 通过串口与WiFi模块通信

from microbit import *
import json
import time

# 配置
SERVER_IP = "192.168.1.100"  # 服务器IP地址
SERVER_PORT = 5000
DEVICE_ID = "microbit_wifi_001"
WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"

class WiFiMicroBitClient:
    def __init__(self):
        self.device_id = DEVICE_ID
        self.wifi_connected = False
        self.server_connected = False
        
        # 初始化串口通信
        uart.init(baudrate=115200)
        
        # 显示启动状态
        display.show(Image.ARROW_E)
        
    def send_at_command(self, command, timeout=5000):
        """发送AT命令到WiFi模块"""
        uart.write(command + '\r\n')
        start_time = time.ticks_ms()
        response = ""
        
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout:
            if uart.any():
                response += uart.read().decode('utf-8', 'ignore')
                if "OK" in response or "ERROR" in response:
                    break
            sleep(10)
        
        return response
    
    def connect_wifi(self):
        """连接WiFi网络"""
        try:
            display.show("W")
            
            # 重置WiFi模块
            self.send_at_command("AT+RST")
            sleep(2000)
            
            # 设置WiFi模式
            self.send_at_command("AT+CWMODE=1")
            
            # 连接WiFi
            connect_cmd = f'AT+CWJAP="{WIFI_SSID}","{WIFI_PASSWORD}"'
            response = self.send_at_command(connect_cmd, 10000)
            
            if "OK" in response:
                self.wifi_connected = True
                display.show(Image.YES)
                print("WiFi connected")
                return True
            else:
                display.show(Image.NO)
                print("WiFi connection failed")
                return False
                
        except Exception as e:
            print(f"WiFi connection error: {e}")
            display.show(Image.SAD)
            return False
    
    def register_device(self):
        """注册设备到服务器"""
        try:
            if not self.wifi_connected:
                return False
            
            # 准备注册数据
            data = {
                "device_id": self.device_id,
                "name": "MicroBit WiFi Device",
                "description": "BBC micro:bit with WiFi module"
            }
            
            # 发送HTTP POST请求
            success = self.send_http_post("/api/microbit/register", data)
            
            if success:
                self.server_connected = True
                display.show("R")
                print("Device registered")
                return True
            else:
                display.show(Image.NO)
                print("Registration failed")
                return False
                
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    def send_http_post(self, endpoint, data):
        """发送HTTP POST请求"""
        try:
            # 建立TCP连接
            connect_cmd = f'AT+CIPSTART="TCP","{SERVER_IP}",{SERVER_PORT}'
            response = self.send_at_command(connect_cmd, 5000)
            
            if "OK" not in response:
                return False
            
            # 构建HTTP请求
            json_data = json.dumps(data)
            http_request = (
                f"POST {endpoint} HTTP/1.1\r\n"
                f"Host: {SERVER_IP}:{SERVER_PORT}\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(json_data)}\r\n"
                "\r\n"
                f"{json_data}"
            )
            
            # 发送数据
            send_cmd = f"AT+CIPSEND={len(http_request)}"
            self.send_at_command(send_cmd)
            sleep(100)
            
            uart.write(http_request)
            sleep(1000)
            
            # 读取响应
            response = ""
            start_time = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
                if uart.any():
                    response += uart.read().decode('utf-8', 'ignore')
                sleep(10)
            
            # 关闭连接
            self.send_at_command("AT+CIPCLOSE")
            
            # 检查响应
            return "success" in response and "true" in response
            
        except Exception as e:
            print(f"HTTP POST error: {e}")
            return False
    
    def send_sensor_data(self):
        """发送传感器数据"""
        try:
            if not self.server_connected:
                return False
            
            # 读取传感器数据
            sensor_data = {
                "device_id": self.device_id,
                "temperature": temperature(),
                "light": display.read_light_level(),
                "accelerometer": {
                    "x": accelerometer.get_x(),
                    "y": accelerometer.get_y(),
                    "z": accelerometer.get_z()
                },
                "button_a": button_a.is_pressed(),
                "button_b": button_b.is_pressed()
            }
            
            # 添加指南针数据（如果已校准）
            try:
                sensor_data["compass"] = compass.heading()
            except:
                pass
            
            # 发送数据
            success = self.send_http_post("/api/microbit/data", sensor_data)
            
            if success:
                display.set_pixel(4, 0, 9)  # 右上角亮起表示发送成功
            else:
                display.set_pixel(4, 0, 0)  # 右上角熄灭表示发送失败
            
            return success
            
        except Exception as e:
            print(f"Sensor data sending error: {e}")
            return False
    
    def send_heartbeat(self):
        """发送心跳信号"""
        try:
            if not self.server_connected:
                return False
            
            heartbeat_data = {"device_id": self.device_id}
            success = self.send_http_post("/api/microbit/heartbeat", heartbeat_data)
            
            if success:
                display.set_pixel(0, 0, 9)  # 左上角亮起表示在线
            else:
                display.set_pixel(0, 0, 0)  # 左上角熄灭表示离线
            
            return success
            
        except Exception as e:
            print(f"Heartbeat error: {e}")
            return False
    
    def run(self):
        """主运行循环"""
        print("Starting WiFi MicroBit Client...")
        
        # 连接WiFi
        if not self.connect_wifi():
            print("Failed to connect WiFi")
            return
        
        sleep(2000)
        
        # 注册设备
        if not self.register_device():
            print("Failed to register device")
            return
        
        sleep(2000)
        
        # 主循环
        last_heartbeat = 0
        last_data_send = 0
        
        while True:
            try:
                current_time = time.ticks_ms()
                
                # 每30秒发送心跳
                if time.ticks_diff(current_time, last_heartbeat) >= 30000:
                    self.send_heartbeat()
                    last_heartbeat = current_time
                
                # 每10秒发送传感器数据
                if time.ticks_diff(current_time, last_data_send) >= 10000:
                    self.send_sensor_data()
                    last_data_send = current_time
                
                # 按钮交互
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
                
                sleep(1000)
                
            except Exception as e:
                print(f"Main loop error: {e}")
                display.show(Image.SAD)
                sleep(2000)
                display.clear()

# 运行客户端
if __name__ == "__main__":
    client = WiFiMicroBitClient()
    client.run()

