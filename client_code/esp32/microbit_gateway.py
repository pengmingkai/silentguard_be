# ESP32作为micro:bit网关 - MicroPython版本
# 接收micro:bit的无线电信号并转发到服务器

import network
import urequests
import ujson
import time
import machine
from machine import Pin, UART
import gc

# 配置信息
WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"
SERVER_URL = "http://192.168.1.100:5000"
GATEWAY_ID = "gateway_001"
GATEWAY_NAME = "MicroBit Gateway"

# 串口配置（连接micro:bit）
UART_TX = 17
UART_RX = 16
UART_BAUDRATE = 115200

class MicroBitGateway:
    def __init__(self):
        self.gateway_id = GATEWAY_ID
        self.gateway_name = GATEWAY_NAME
        self.wifi_connected = False
        self.server_connected = False
        self.connected_devices = {}  # 存储连接的micro:bit设备
        self.last_heartbeat = 0
        self.heartbeat_interval = 30000  # 30秒
        
        # 初始化硬件
        self.setup_hardware()
        
        # 连接WiFi
        self.connect_wifi()
        
        # 注册网关
        self.register_gateway()
        
        print(f"MicroBit Gateway initialized: {self.gateway_id}")
    
    def setup_hardware(self):
        """初始化硬件"""
        try:
            # 状态LED
            self.led = Pin(2, Pin.OUT)
            self.led.on()
            
            # 串口通信（与micro:bit通信）
            self.uart = UART(2, baudrate=UART_BAUDRATE, tx=UART_TX, rx=UART_RX)
            
            print("Gateway hardware initialized")
            
        except Exception as e:
            print(f"Hardware setup error: {e}")
    
    def connect_wifi(self):
        """连接WiFi网络"""
        try:
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            
            if not wlan.isconnected():
                print(f"Connecting to WiFi: {WIFI_SSID}")
                wlan.connect(WIFI_SSID, WIFI_PASSWORD)
                
                timeout = 20
                while not wlan.isconnected() and timeout > 0:
                    time.sleep(1)
                    timeout -= 1
                    print(".", end="")
                
                print()
            
            if wlan.isconnected():
                self.wifi_connected = True
                config = wlan.ifconfig()
                print(f"WiFi connected! IP: {config[0]}")
                self.led.on()
                return True
            else:
                print("WiFi connection failed!")
                self.led.off()
                return False
                
        except Exception as e:
            print(f"WiFi connection error: {e}")
            return False
    
    def register_gateway(self):
        """注册网关到服务器"""
        if not self.wifi_connected:
            return False
        
        try:
            wlan = network.WLAN(network.STA_IF)
            config = wlan.ifconfig()
            
            registration_data = {
                "device_id": self.gateway_id,
                "name": self.gateway_name,
                "description": "ESP32 Gateway for micro:bit devices",
                "device_type": "gateway",
                "wifi_ssid": WIFI_SSID,
                "ip_address": config[0],
                "mac_address": ":".join(["{:02x}".format(b) for b in wlan.config('mac')]),
                "capabilities": ["wifi", "uart", "radio_bridge"]
            }
            
            response = self.send_http_request("POST", "/api/devices", registration_data)
            
            if response and response.get("success"):
                self.server_connected = True
                print("Gateway registered successfully")
                return True
            else:
                print("Gateway registration failed")
                return False
                
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    def send_http_request(self, method, endpoint, data=None):
        """发送HTTP请求"""
        try:
            url = SERVER_URL + endpoint
            headers = {"Content-Type": "application/json"}
            
            if method == "POST" and data:
                json_data = ujson.dumps(data)
                response = urequests.post(url, data=json_data, headers=headers)
            elif method == "GET":
                response = urequests.get(url, headers=headers)
            else:
                return None
            
            if response.status_code in [200, 201]:
                result = response.json()
                response.close()
                return result
            else:
                print(f"HTTP {method} failed: {response.status_code}")
                response.close()
                return None
                
        except Exception as e:
            print(f"HTTP request error: {e}")
            return None
    
    def receive_radio_message(self):
        """接收来自micro:bit的串口消息"""
        try:
            if self.uart.any():
                message = self.uart.readline()
                if message:
                    try:
                        # 解析JSON消息
                        data = ujson.loads(message.decode('utf-8').strip())
                        return data
                    except:
                        # 忽略无效消息
                        pass
            return None
            
        except Exception as e:
            print(f"Radio receive error: {e}")
            return None
    
    def send_radio_message(self, message):
        """发送消息到micro:bit"""
        try:
            json_message = ujson.dumps(message)
            self.uart.write(json_message + '\n')
            return True
            
        except Exception as e:
            print(f"Radio send error: {e}")
            return False
    
    def handle_microbit_message(self, message):
        """处理来自micro:bit的消息"""
        try:
            message_type = message.get("type")
            device_id = message.get("device_id")
            
            if not device_id:
                return
            
            if message_type == "register":
                self.handle_device_registration(message)
            
            elif message_type == "sensor_data":
                self.forward_sensor_data(message)
            
            elif message_type == "heartbeat":
                self.handle_device_heartbeat(message)
            
            elif message_type == "command_ack":
                self.handle_command_acknowledgment(message)
            
            elif message_type == "pong":
                self.handle_ping_response(message)
            
        except Exception as e:
            print(f"Message handling error: {e}")
    
    def handle_device_registration(self, message):
        """处理micro:bit设备注册"""
        try:
            device_id = message["device_id"]
            device_name = message["device_name"]
            
            # 检查设备数量限制
            if len(self.connected_devices) >= 2 and device_id not in self.connected_devices:
                # 发送注册失败响应
                response = {
                    "type": "register_nack",
                    "target": device_id,
                    "error": "Maximum devices reached"
                }
                self.send_radio_message(response)
                return
            
            # 向服务器注册micro:bit设备
            registration_data = {
                "device_id": device_id,
                "device_type": "microbit",
                "name": device_name,
                "description": message.get("data", {}).get("description", "micro:bit via gateway"),
                "config": {
                    "gateway_id": self.gateway_id,
                    "connection_type": "radio",
                    "capabilities": message.get("data", {}).get("capabilities", [])
                }
            }
            
            response = self.send_http_request("POST", "/api/microbit/register", registration_data)
            
            if response and response.get("success"):
                # 记录连接的设备
                self.connected_devices[device_id] = {
                    "name": device_name,
                    "last_seen": time.ticks_ms(),
                    "registered": True
                }
                
                # 发送注册成功响应
                ack_response = {
                    "type": "register_ack",
                    "target": device_id,
                    "gateway_id": self.gateway_id,
                    "server_time": response.get("server_time")
                }
                self.send_radio_message(ack_response)
                
                print(f"Device {device_id} registered successfully")
            else:
                # 发送注册失败响应
                nack_response = {
                    "type": "register_nack",
                    "target": device_id,
                    "error": "Server registration failed"
                }
                self.send_radio_message(nack_response)
                
        except Exception as e:
            print(f"Device registration error: {e}")
    
    def forward_sensor_data(self, message):
        """转发传感器数据到服务器"""
        try:
            device_id = message["device_id"]
            sensor_data = message.get("data", {})
            
            if device_id not in self.connected_devices:
                print(f"Unknown device: {device_id}")
                return
            
            # 更新设备最后活跃时间
            self.connected_devices[device_id]["last_seen"] = time.ticks_ms()
            
            # 构建服务器数据格式
            server_data = {
                "device_id": device_id,
                **sensor_data
            }
            
            # 发送到服务器
            response = self.send_http_request("POST", "/api/microbit/data", server_data)
            
            if response and response.get("success"):
                print(f"Data forwarded for device {device_id}")
                
                # 发送确认给micro:bit
                ack_message = {
                    "type": "data_ack",
                    "target": device_id,
                    "timestamp": message.get("timestamp")
                }
                self.send_radio_message(ack_message)
            else:
                print(f"Failed to forward data for device {device_id}")
                
        except Exception as e:
            print(f"Data forwarding error: {e}")
    
    def handle_device_heartbeat(self, message):
        """处理设备心跳"""
        try:
            device_id = message["device_id"]
            
            if device_id in self.connected_devices:
                self.connected_devices[device_id]["last_seen"] = time.ticks_ms()
                
                # 转发心跳到服务器
                heartbeat_data = {"device_id": device_id}
                response = self.send_http_request("POST", "/api/microbit/heartbeat", heartbeat_data)
                
                if response and response.get("success"):
                    # 发送心跳确认
                    ack_message = {
                        "type": "heartbeat_ack",
                        "target": device_id,
                        "server_time": response.get("server_time")
                    }
                    self.send_radio_message(ack_message)
                
        except Exception as e:
            print(f"Heartbeat handling error: {e}")
    
    def handle_command_acknowledgment(self, message):
        """处理命令执行确认"""
        try:
            device_id = message["device_id"]
            command = message.get("data", {}).get("command")
            
            print(f"Command '{command}' executed by device {device_id}")
            
        except Exception as e:
            print(f"Command ack handling error: {e}")
    
    def handle_ping_response(self, message):
        """处理ping响应"""
        try:
            device_id = message["device_id"]
            if device_id in self.connected_devices:
                self.connected_devices[device_id]["last_seen"] = time.ticks_ms()
                print(f"Ping response from {device_id}")
                
        except Exception as e:
            print(f"Ping response handling error: {e}")
    
    def check_device_timeouts(self):
        """检查设备超时"""
        try:
            current_time = time.ticks_ms()
            timeout_threshold = 60000  # 60秒超时
            
            devices_to_remove = []
            for device_id, device_info in self.connected_devices.items():
                if time.ticks_diff(current_time, device_info["last_seen"]) > timeout_threshold:
                    devices_to_remove.append(device_id)
            
            for device_id in devices_to_remove:
                print(f"Device {device_id} timed out")
                del self.connected_devices[device_id]
                
        except Exception as e:
            print(f"Timeout check error: {e}")
    
    def send_gateway_heartbeat(self):
        """发送网关心跳"""
        try:
            heartbeat_data = {
                "device_id": self.gateway_id,
                "connected_devices": list(self.connected_devices.keys()),
                "device_count": len(self.connected_devices),
                "system_info": {
                    "free_heap": gc.mem_free(),
                    "wifi_rssi": network.WLAN(network.STA_IF).status('rssi') if self.wifi_connected else 0,
                    "uptime": time.ticks_ms()
                }
            }
            
            response = self.send_http_request("POST", "/api/data", heartbeat_data)
            
            if response and response.get("success"):
                print("Gateway heartbeat sent")
                return True
            else:
                print("Gateway heartbeat failed")
                return False
                
        except Exception as e:
            print(f"Gateway heartbeat error: {e}")
            return False
    
    def run(self):
        """主运行循环"""
        print("Starting MicroBit Gateway...")
        
        while True:
            try:
                current_time = time.ticks_ms()
                
                # 检查WiFi连接
                if not network.WLAN(network.STA_IF).isconnected():
                    print("WiFi disconnected, reconnecting...")
                    self.wifi_connected = False
                    self.server_connected = False
                    self.connect_wifi()
                    if self.wifi_connected:
                        self.register_gateway()
                
                # 处理来自micro:bit的消息
                message = self.receive_radio_message()
                if message:
                    self.handle_microbit_message(message)
                
                # 发送网关心跳
                if time.ticks_diff(current_time, self.last_heartbeat) >= self.heartbeat_interval:
                    self.send_gateway_heartbeat()
                    self.last_heartbeat = current_time
                
                # 检查设备超时
                self.check_device_timeouts()
                
                # 垃圾回收
                gc.collect()
                
                time.sleep_ms(100)  # 短暂延迟
                
            except Exception as e:
                print(f"Main loop error: {e}")
                time.sleep(5)

# 运行网关
if __name__ == "__main__":
    try:
        gateway = MicroBitGateway()
        gateway.run()
    except KeyboardInterrupt:
        print("Gateway stopped by user")
    except Exception as e:
        print(f"Gateway error: {e}")
        machine.reset()

