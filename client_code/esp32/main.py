# ESP32 IoT客户端 - MicroPython版本
# 连接到Flask服务器并发送传感器数据

import network
import urequests
import ujson
import time
import machine
from machine import Pin, ADC, PWM, I2C
import dht
import gc

# 配置信息
WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"
SERVER_URL = "http://192.168.1.100:5000"
DEVICE_ID = "esp32_micropython_001"
DEVICE_NAME = "ESP32 MicroPython Sensor"

# 引脚配置
DHT_PIN = 4
MOTION_PIN = 5
LIGHT_PIN = 36  # ADC引脚
TRIG_PIN = 18
ECHO_PIN = 19
LED_PIN = 2
RELAY_PIN = 23

class ESP32IoTClient:
    def __init__(self):
        self.device_id = DEVICE_ID
        self.device_name = DEVICE_NAME
        self.wifi_connected = False
        self.server_connected = False
        self.last_heartbeat = 0
        self.last_data_send = 0
        self.heartbeat_interval = 30000  # 30秒
        self.data_send_interval = 10000  # 10秒
        
        # 初始化硬件
        self.setup_hardware()
        
        # 连接WiFi
        self.connect_wifi()
        
        # 注册设备
        self.register_device()
        
        print(f"ESP32 IoT Client initialized: {self.device_id}")
    
    def setup_hardware(self):
        """初始化硬件引脚和传感器"""
        try:
            # GPIO引脚
            self.led = Pin(LED_PIN, Pin.OUT)
            self.relay = Pin(RELAY_PIN, Pin.OUT)
            self.motion = Pin(MOTION_PIN, Pin.IN)
            self.trig = Pin(TRIG_PIN, Pin.OUT)
            self.echo = Pin(ECHO_PIN, Pin.IN)
            
            # ADC引脚
            self.light_adc = ADC(Pin(LIGHT_PIN))
            self.light_adc.atten(ADC.ATTN_11DB)  # 0-3.3V范围
            
            # DHT传感器
            self.dht_sensor = dht.DHT22(Pin(DHT_PIN))
            
            # 启动指示灯
            self.led.on()
            
            print("Hardware initialized")
            
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
                
                # 等待连接
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
    
    def register_device(self):
        """注册设备到服务器"""
        if not self.wifi_connected:
            return False
        
        try:
            wlan = network.WLAN(network.STA_IF)
            config = wlan.ifconfig()
            
            registration_data = {
                "device_id": self.device_id,
                "name": self.device_name,
                "description": "ESP32 MicroPython IoT device",
                "wifi_ssid": WIFI_SSID,
                "ip_address": config[0],
                "mac_address": ":".join(["{:02x}".format(b) for b in wlan.config('mac')]),
                "firmware_version": "MicroPython 1.0",
                "chip_model": "ESP32",
                "sensors": ["temperature", "humidity", "light", "motion", "distance"],
                "capabilities": ["wifi", "gpio", "pwm", "adc"]
            }
            
            response = self.send_http_request("POST", "/api/esp32/register", registration_data)
            
            if response and response.get("success"):
                self.server_connected = True
                print("Device registered successfully")
                return True
            else:
                print("Device registration failed")
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
            
            if response.status_code == 200:
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
    
    def read_sensors(self):
        """读取所有传感器数据"""
        sensor_data = {}
        
        try:
            # DHT22温湿度传感器
            try:
                self.dht_sensor.measure()
                sensor_data["temperature"] = self.dht_sensor.temperature()
                sensor_data["humidity"] = self.dht_sensor.humidity()
            except Exception as e:
                print(f"DHT sensor error: {e}")
            
            # 光照传感器
            try:
                light_raw = self.light_adc.read()
                sensor_data["light"] = int(light_raw * 1000 / 4095)  # 映射到0-1000
            except Exception as e:
                print(f"Light sensor error: {e}")
            
            # 运动传感器
            try:
                sensor_data["motion"] = bool(self.motion.value())
            except Exception as e:
                print(f"Motion sensor error: {e}")
            
            # 超声波距离传感器
            try:
                distance = self.read_ultrasonic_distance()
                if distance > 0:
                    sensor_data["distance"] = distance
            except Exception as e:
                print(f"Ultrasonic sensor error: {e}")
            
            # 系统状态
            sensor_data["system_status"] = {
                "free_heap": gc.mem_free(),
                "wifi_rssi": network.WLAN(network.STA_IF).status('rssi') if self.wifi_connected else 0
            }
            
        except Exception as e:
            print(f"Sensor reading error: {e}")
        
        return sensor_data
    
    def read_ultrasonic_distance(self):
        """读取超声波距离传感器"""
        try:
            # 发送触发信号
            self.trig.off()
            time.sleep_us(2)
            self.trig.on()
            time.sleep_us(10)
            self.trig.off()
            
            # 测量回波时间
            start_time = time.ticks_us()
            timeout = start_time + 30000  # 30ms超时
            
            # 等待回波开始
            while self.echo.value() == 0 and time.ticks_us() < timeout:
                pass
            
            if time.ticks_us() >= timeout:
                return -1
            
            echo_start = time.ticks_us()
            
            # 等待回波结束
            while self.echo.value() == 1 and time.ticks_us() < timeout:
                pass
            
            if time.ticks_us() >= timeout:
                return -1
            
            echo_end = time.ticks_us()
            
            # 计算距离
            duration = time.ticks_diff(echo_end, echo_start)
            distance = duration * 0.034 / 2  # 声速计算距离(cm)
            
            if distance > 400:
                return -1
            
            return distance
            
        except Exception as e:
            print(f"Ultrasonic reading error: {e}")
            return -1
    
    def send_sensor_data(self):
        """发送传感器数据到服务器"""
        if not self.server_connected:
            return False
        
        try:
            sensor_data = self.read_sensors()
            sensor_data["device_id"] = self.device_id
            
            response = self.send_http_request("POST", "/api/esp32/data", sensor_data)
            
            if response and response.get("success"):
                print("Sensor data sent successfully")
                # 闪烁LED表示成功
                self.led.off()
                time.sleep_ms(100)
                self.led.on()
                return True
            else:
                print("Failed to send sensor data")
                return False
                
        except Exception as e:
            print(f"Data sending error: {e}")
            return False
    
    def send_heartbeat(self):
        """发送心跳信号"""
        if not self.server_connected:
            return False
        
        try:
            heartbeat_data = {
                "device_id": self.device_id,
                "system_info": {
                    "free_heap": gc.mem_free(),
                    "wifi_rssi": network.WLAN(network.STA_IF).status('rssi') if self.wifi_connected else 0,
                    "uptime": time.ticks_ms()
                }
            }
            
            response = self.send_http_request("POST", "/api/esp32/heartbeat", heartbeat_data)
            
            if response and response.get("success"):
                print("Heartbeat sent successfully")
                return True
            else:
                print("Heartbeat failed")
                self.server_connected = False
                return False
                
        except Exception as e:
            print(f"Heartbeat error: {e}")
            return False
    
    def check_server_commands(self):
        """检查服务器命令"""
        if not self.server_connected:
            return
        
        try:
            response = self.send_http_request("GET", f"/api/esp32/config/{self.device_id}")
            
            if response and response.get("success"):
                config = response.get("config", {})
                
                # 处理配置更新
                if "led_brightness" in config:
                    brightness = config["led_brightness"]
                    # 使用PWM控制LED亮度
                    led_pwm = PWM(Pin(LED_PIN))
                    led_pwm.duty(int(brightness * 1023 / 100))  # 转换为0-1023范围
                
                if "relay_state" in config:
                    relay_state = config["relay_state"]
                    self.relay.value(1 if relay_state else 0)
                
                if "data_interval" in config:
                    self.data_send_interval = config["data_interval"] * 1000  # 转换为毫秒
                
        except Exception as e:
            print(f"Command checking error: {e}")
    
    def execute_control_command(self, action, parameters):
        """执行控制命令"""
        try:
            if action == "gpio_write":
                pin_num = parameters["pin"]
                value = parameters["value"]
                pin = Pin(pin_num, Pin.OUT)
                pin.value(value)
                print(f"GPIO {pin_num} set to {value}")
            
            elif action == "pwm_write":
                pin_num = parameters["pin"]
                value = parameters["value"]
                frequency = parameters.get("frequency", 1000)
                pwm = PWM(Pin(pin_num), freq=frequency)
                pwm.duty(value)
                print(f"PWM {pin_num} set to {value} at {frequency}Hz")
            
            elif action == "led_control":
                brightness = parameters["brightness"]
                led_pwm = PWM(Pin(LED_PIN))
                led_pwm.duty(int(brightness * 1023 / 100))
                print(f"LED brightness set to {brightness}%")
            
            elif action == "relay_control":
                state = parameters["state"]
                self.relay.value(1 if state else 0)
                print(f"Relay {'ON' if state else 'OFF'}")
            
            elif action == "restart":
                print("Restarting ESP32...")
                time.sleep(1)
                machine.reset()
            
            elif action == "deep_sleep":
                duration = parameters["duration"]
                print(f"Entering deep sleep for {duration} seconds")
                machine.deepsleep(duration * 1000)
            
            elif action == "wifi_reconnect":
                print("Reconnecting WiFi...")
                self.wifi_connected = False
                self.connect_wifi()
            
        except Exception as e:
            print(f"Command execution error: {e}")
    
    def run(self):
        """主运行循环"""
        print("Starting ESP32 IoT Client...")
        
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
                        self.register_device()
                
                # 发送心跳
                if time.ticks_diff(current_time, self.last_heartbeat) >= self.heartbeat_interval:
                    self.send_heartbeat()
                    self.last_heartbeat = current_time
                
                # 发送传感器数据
                if time.ticks_diff(current_time, self.last_data_send) >= self.data_send_interval:
                    self.send_sensor_data()
                    self.last_data_send = current_time
                
                # 检查服务器命令
                self.check_server_commands()
                
                # 垃圾回收
                gc.collect()
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Main loop error: {e}")
                time.sleep(5)

# 运行客户端
if __name__ == "__main__":
    try:
        client = ESP32IoTClient()
        client.run()
    except KeyboardInterrupt:
        print("Client stopped by user")
    except Exception as e:
        print(f"Client error: {e}")
        machine.reset()

