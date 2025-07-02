# micro:bit 无线电客户端
# 通过无线电与网关设备通信，适用于没有WiFi模块的micro:bit

from microbit import *
import radio
import json
import time

# 配置
DEVICE_ID = "microbit_radio_001"
DEVICE_NAME = "MicroBit Radio Sensor"
RADIO_CHANNEL = 7
GATEWAY_ID = "gateway_001"  # 网关设备ID

class RadioMicroBitClient:
    def __init__(self):
        self.device_id = DEVICE_ID
        self.device_name = DEVICE_NAME
        self.gateway_connected = False
        self.last_heartbeat = 0
        
        # 初始化无线电
        radio.on()
        radio.config(channel=RADIO_CHANNEL, power=7, length=251)
        
        # 显示启动状态
        display.show(Image.DIAMOND)
        sleep(1000)
        display.clear()
        
        print(f"Radio MicroBit Client: {self.device_id}")
    
    def send_radio_message(self, message_type, data=None):
        """发送无线电消息"""
        try:
            message = {
                "type": message_type,
                "device_id": self.device_id,
                "device_name": self.device_name,
                "timestamp": time.ticks_ms(),
                "target": GATEWAY_ID
            }
            
            if data:
                message["data"] = data
            
            # 发送消息
            radio.send(json.dumps(message))
            return True
            
        except Exception as e:
            print(f"Radio send error: {e}")
            return False
    
    def register_device(self):
        """向网关注册设备"""
        try:
            registration_data = {
                "description": "BBC micro:bit radio sensor",
                "capabilities": ["temperature", "light", "accelerometer", "compass", "buttons"]
            }
            
            success = self.send_radio_message("register", registration_data)
            
            if success:
                display.show("R")
                print("Registration message sent")
                
                # 等待确认
                start_time = time.ticks_ms()
                while time.ticks_diff(time.ticks_ms(), start_time) < 5000:
                    response = self.receive_radio_message()
                    if response and response.get("type") == "register_ack":
                        if response.get("target") == self.device_id:
                            self.gateway_connected = True
                            display.show(Image.YES)
                            print("Registration confirmed")
                            return True
                    sleep(100)
                
                # 超时未收到确认
                display.show(Image.NO)
                print("Registration timeout")
                return False
            else:
                display.show(Image.SAD)
                return False
                
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    def receive_radio_message(self):
        """接收无线电消息"""
        try:
            message = radio.receive()
            if message:
                return json.loads(message)
            return None
        except:
            return None
    
    def read_sensors(self):
        """读取传感器数据"""
        try:
            sensor_data = {
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
            
            # 尝试读取指南针（可能需要校准）
            try:
                sensor_data["compass"] = compass.heading()
            except:
                pass
            
            return sensor_data
            
        except Exception as e:
            print(f"Sensor reading error: {e}")
            return {}
    
    def send_sensor_data(self):
        """发送传感器数据"""
        try:
            sensor_data = self.read_sensors()
            success = self.send_radio_message("sensor_data", sensor_data)
            
            if success:
                display.set_pixel(4, 0, 5)  # 右上角中等亮度表示数据发送
            else:
                display.set_pixel(4, 0, 0)  # 右上角熄灭表示发送失败
            
            return success
            
        except Exception as e:
            print(f"Data sending error: {e}")
            return False
    
    def send_heartbeat(self):
        """发送心跳信号"""
        try:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, self.last_heartbeat) >= 30000:  # 30秒间隔
                success = self.send_radio_message("heartbeat")
                
                if success:
                    display.set_pixel(0, 0, 5)  # 左上角中等亮度表示心跳
                    self.last_heartbeat = current_time
                else:
                    display.set_pixel(0, 0, 0)  # 左上角熄灭表示心跳失败
                
                return success
            
            return True
            
        except Exception as e:
            print(f"Heartbeat error: {e}")
            return False
    
    def handle_commands(self):
        """处理来自网关的命令"""
        try:
            message = self.receive_radio_message()
            if message and message.get("target") == self.device_id:
                command_type = message.get("type")
                
                if command_type == "command":
                    self.execute_command(message.get("data", {}))
                elif command_type == "ping":
                    # 响应ping命令
                    self.send_radio_message("pong")
                
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
            
            elif command == "blink":
                # 闪烁显示
                for _ in range(3):
                    display.show(Image.DIAMOND)
                    sleep(200)
                    display.clear()
                    sleep(200)
            
            # 发送命令执行确认
            self.send_radio_message("command_ack", {"command": command})
            print(f"Executed command: {command}")
            
        except Exception as e:
            print(f"Command execution error: {e}")
    
    def show_status(self):
        """显示设备状态"""
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
    
    def run(self):
        """主运行循环"""
        print("Starting Radio MicroBit Client...")
        
        # 尝试注册设备
        registration_attempts = 0
        while not self.gateway_connected and registration_attempts < 3:
            self.register_device()
            if not self.gateway_connected:
                registration_attempts += 1
                sleep(5000)  # 等待5秒后重试
        
        if not self.gateway_connected:
            print("Failed to connect to gateway")
            display.show(Image.SAD)
            return
        
        # 主循环
        last_data_send = 0
        
        while True:
            try:
                current_time = time.ticks_ms()
                
                # 发送心跳
                self.send_heartbeat()
                
                # 每10秒发送传感器数据
                if time.ticks_diff(current_time, last_data_send) >= 10000:
                    self.send_sensor_data()
                    last_data_send = current_time
                
                # 处理命令
                self.handle_commands()
                
                # 显示状态
                self.show_status()
                
                # 检查网关连接状态
                if not self.gateway_connected:
                    display.show(Image.NO)
                    sleep(1000)
                    # 尝试重新连接
                    self.register_device()
                
                sleep(1000)
                
            except Exception as e:
                print(f"Main loop error: {e}")
                display.show(Image.SAD)
                sleep(2000)
                display.clear()

# 运行客户端
if __name__ == "__main__":
    client = RadioMicroBitClient()
    client.run()

