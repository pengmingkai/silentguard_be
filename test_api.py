#!/usr/bin/env python3
"""
IoT服务器API测试脚本
用于测试所有API接口的功能
"""

import requests
import json
import time
import random
from datetime import datetime

# 服务器配置
SERVER_URL = "http://localhost:5000"
API_BASE = f"{SERVER_URL}/api"

class IoTAPITester:
    def __init__(self, server_url=SERVER_URL):
        self.server_url = server_url
        self.api_base = f"{server_url}/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'IoT-API-Tester/1.0'
        })
    
    def test_connection(self):
        """测试服务器连接"""
        print("🔗 测试服务器连接...")
        try:
            response = self.session.get(f"{self.server_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 服务器连接成功")
                print(f"   状态: {data.get('status')}")
                print(f"   数据库: {data.get('database')}")
                return True
            else:
                print(f"❌ 服务器连接失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 连接错误: {e}")
            return False
    
    def test_api_info(self):
        """测试API信息接口"""
        print("\n📋 测试API信息...")
        try:
            response = self.session.get(f"{self.api_base}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API信息获取成功")
                print(f"   名称: {data.get('name')}")
                print(f"   版本: {data.get('version')}")
                return True
            else:
                print(f"❌ API信息获取失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 请求错误: {e}")
            return False
    
    def test_microbit_register(self, device_id="test_microbit_001"):
        """测试micro:bit设备注册"""
        print(f"\n🤖 测试micro:bit设备注册 ({device_id})...")
        try:
            data = {
                "device_id": device_id,
                "name": f"测试micro:bit设备 {device_id}",
                "description": "API测试用micro:bit设备"
            }
            
            response = self.session.post(f"{self.api_base}/microbit/register", 
                                       json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('success'):
                    print(f"✅ micro:bit设备注册成功")
                    print(f"   设备ID: {result['device']['device_id']}")
                    print(f"   设备名称: {result['device']['name']}")
                    return True
                else:
                    print(f"❌ 注册失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ 注册请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 注册错误: {e}")
            return False
    
    def test_esp32_register(self, device_id="test_esp32_001"):
        """测试ESP32设备注册"""
        print(f"\n🔧 测试ESP32设备注册 ({device_id})...")
        try:
            data = {
                "device_id": device_id,
                "name": f"测试ESP32设备 {device_id}",
                "description": "API测试用ESP32设备",
                "wifi_ssid": "TestWiFi",
                "ip_address": "192.168.1.100",
                "mac_address": "AA:BB:CC:DD:EE:FF",
                "firmware_version": "1.0.0",
                "sensors": ["temperature", "humidity", "pressure"],
                "capabilities": ["wifi", "gpio", "pwm"]
            }
            
            response = self.session.post(f"{self.api_base}/esp32/register", 
                                       json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('success'):
                    print(f"✅ ESP32设备注册成功")
                    print(f"   设备ID: {result['device']['device_id']}")
                    print(f"   设备名称: {result['device']['name']}")
                    return True
                else:
                    print(f"❌ 注册失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ 注册请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 注册错误: {e}")
            return False
    
    def test_send_microbit_data(self, device_id="test_microbit_001"):
        """测试发送micro:bit传感器数据"""
        print(f"\n📊 测试micro:bit数据上传 ({device_id})...")
        try:
            data = {
                "device_id": device_id,
                "temperature": round(random.uniform(20, 30), 1),
                "light": random.randint(0, 255),
                "accelerometer": {
                    "x": round(random.uniform(-2, 2), 2),
                    "y": round(random.uniform(-2, 2), 2),
                    "z": round(random.uniform(8, 12), 2)
                },
                "compass": random.randint(0, 360),
                "button_a": random.choice([True, False]),
                "button_b": random.choice([True, False])
            }
            
            response = self.session.post(f"{self.api_base}/microbit/data", 
                                       json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('success'):
                    print(f"✅ micro:bit数据上传成功")
                    print(f"   数据条数: {result.get('data_count', 0)}")
                    return True
                else:
                    print(f"❌ 数据上传失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ 数据上传请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 数据上传错误: {e}")
            return False
    
    def test_send_esp32_data(self, device_id="test_esp32_001"):
        """测试发送ESP32传感器数据"""
        print(f"\n📈 测试ESP32数据上传 ({device_id})...")
        try:
            data = {
                "device_id": device_id,
                "temperature": round(random.uniform(20, 35), 1),
                "humidity": round(random.uniform(40, 80), 1),
                "pressure": round(random.uniform(1000, 1020), 2),
                "light": random.randint(0, 1000),
                "motion": random.choice([True, False]),
                "distance": round(random.uniform(10, 200), 1),
                "analog_inputs": {
                    "A0": round(random.uniform(0, 3.3), 2),
                    "A1": round(random.uniform(0, 3.3), 2)
                },
                "system_status": {
                    "free_heap": random.randint(150000, 250000),
                    "wifi_rssi": random.randint(-80, -30)
                }
            }
            
            response = self.session.post(f"{self.api_base}/esp32/data", 
                                       json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('success'):
                    print(f"✅ ESP32数据上传成功")
                    print(f"   数据条数: {result.get('data_count', 0)}")
                    return True
                else:
                    print(f"❌ 数据上传失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ 数据上传请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 数据上传错误: {e}")
            return False
    
    def test_get_devices(self):
        """测试获取设备列表"""
        print("\n📱 测试获取设备列表...")
        try:
            response = self.session.get(f"{self.api_base}/devices")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    devices = result.get('data', [])
                    print(f"✅ 设备列表获取成功")
                    print(f"   设备总数: {len(devices)}")
                    for device in devices:
                        print(f"   - {device['name']} ({device['device_type']}) - {device['status']}")
                    return True
                else:
                    print(f"❌ 获取失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 请求错误: {e}")
            return False
    
    def test_get_device_data(self, device_id="test_microbit_001"):
        """测试获取设备数据"""
        print(f"\n📊 测试获取设备数据 ({device_id})...")
        try:
            response = self.session.get(f"{self.api_base}/devices/{device_id}/data?limit=5")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data_list = result.get('data', [])
                    print(f"✅ 设备数据获取成功")
                    print(f"   数据条数: {len(data_list)}")
                    for data in data_list[:3]:  # 显示前3条
                        print(f"   - {data['sensor_type']}: {data['value']}{data.get('unit', '')}")
                    return True
                else:
                    print(f"❌ 获取失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 请求错误: {e}")
            return False
    
    def test_device_stats(self):
        """测试设备统计"""
        print("\n📈 测试设备统计...")
        try:
            response = self.session.get(f"{self.api_base}/devices/stats")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    stats = result.get('stats', {})
                    print(f"✅ 设备统计获取成功")
                    print(f"   总设备数: {stats.get('total_devices', 0)}")
                    print(f"   在线设备: {stats.get('online_devices', 0)}")
                    print(f"   micro:bit设备: {stats.get('microbit_devices', 0)}")
                    print(f"   ESP32设备: {stats.get('esp32_devices', 0)}")
                    return True
                else:
                    print(f"❌ 获取失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 请求错误: {e}")
            return False
    
    def test_heartbeat(self, device_id="test_microbit_001", device_type="microbit"):
        """测试心跳接口"""
        print(f"\n💓 测试{device_type}心跳 ({device_id})...")
        try:
            endpoint = f"{self.api_base}/{device_type}/heartbeat"
            data = {"device_id": device_id}
            
            response = self.session.post(endpoint, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ 心跳发送成功")
                    print(f"   设备状态: {result.get('status', 'unknown')}")
                    return True
                else:
                    print(f"❌ 心跳失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ 心跳请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 心跳错误: {e}")
            return False
    
    def test_microbit_command(self, device_id="test_microbit_001"):
        """测试micro:bit命令发送"""
        print(f"\n🎮 测试micro:bit命令发送 ({device_id})...")
        try:
            data = {
                "device_id": device_id,
                "command": "display_text",
                "text": "Hello API!"
            }
            
            response = self.session.post(f"{self.api_base}/microbit/command", 
                                       json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ 命令发送成功")
                    print(f"   命令: {data['command']}")
                    return True
                else:
                    print(f"❌ 命令发送失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ 命令请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 命令错误: {e}")
            return False
    
    def test_esp32_control(self, device_id="test_esp32_001"):
        """测试ESP32控制接口"""
        print(f"\n🎛️ 测试ESP32控制 ({device_id})...")
        try:
            data = {
                "device_id": device_id,
                "action": "led_control",
                "pin": 2,
                "brightness": 50
            }
            
            response = self.session.post(f"{self.api_base}/esp32/control", 
                                       json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ 控制命令发送成功")
                    print(f"   动作: {data['action']}")
                    return True
                else:
                    print(f"❌ 控制失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ 控制请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 控制错误: {e}")
            return False
    
    def run_full_test(self):
        """运行完整测试套件"""
        print("🚀 开始IoT服务器API完整测试")
        print("=" * 50)
        
        test_results = []
        
        # 基础连接测试
        test_results.append(("服务器连接", self.test_connection()))
        test_results.append(("API信息", self.test_api_info()))
        
        # 设备注册测试
        microbit_id = "test_microbit_001"
        esp32_id = "test_esp32_001"
        
        test_results.append(("micro:bit注册", self.test_microbit_register(microbit_id)))
        test_results.append(("ESP32注册", self.test_esp32_register(esp32_id)))
        
        # 数据上传测试
        test_results.append(("micro:bit数据", self.test_send_microbit_data(microbit_id)))
        test_results.append(("ESP32数据", self.test_send_esp32_data(esp32_id)))
        
        # 数据查询测试
        test_results.append(("设备列表", self.test_get_devices()))
        test_results.append(("设备数据", self.test_get_device_data(microbit_id)))
        test_results.append(("设备统计", self.test_device_stats()))
        
        # 心跳测试
        test_results.append(("micro:bit心跳", self.test_heartbeat(microbit_id, "microbit")))
        test_results.append(("ESP32心跳", self.test_heartbeat(esp32_id, "esp32")))
        
        # 控制命令测试
        test_results.append(("micro:bit命令", self.test_microbit_command(microbit_id)))
        test_results.append(("ESP32控制", self.test_esp32_control(esp32_id)))
        
        # 测试结果汇总
        print("\n" + "=" * 50)
        print("📋 测试结果汇总")
        print("=" * 50)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:<20} {status}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print("=" * 50)
        print(f"总测试数: {len(test_results)}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"成功率: {passed/len(test_results)*100:.1f}%")
        
        if failed == 0:
            print("\n🎉 所有测试通过！API服务器工作正常。")
        else:
            print(f"\n⚠️ 有 {failed} 个测试失败，请检查服务器配置。")
        
        return failed == 0

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IoT服务器API测试工具')
    parser.add_argument('--server', default='http://localhost:5000', 
                       help='服务器URL (默认: http://localhost:5000)')
    parser.add_argument('--test', choices=['all', 'connection', 'register', 'data', 'control'],
                       default='all', help='测试类型')
    
    args = parser.parse_args()
    
    tester = IoTAPITester(args.server)
    
    if args.test == 'all':
        success = tester.run_full_test()
        exit(0 if success else 1)
    elif args.test == 'connection':
        tester.test_connection()
        tester.test_api_info()
    elif args.test == 'register':
        tester.test_microbit_register()
        tester.test_esp32_register()
    elif args.test == 'data':
        tester.test_send_microbit_data()
        tester.test_send_esp32_data()
        tester.test_get_devices()
    elif args.test == 'control':
        tester.test_microbit_command()
        tester.test_esp32_control()

if __name__ == "__main__":
    main()

