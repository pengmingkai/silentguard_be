from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models import db
from src.models.device import Device
from src.models.sensor_data import SensorData

esp32_bp = Blueprint('esp32', __name__)

@esp32_bp.route('/register', methods=['POST'])
def register_esp32():
    """注册ESP32设备"""
    try:
        data = request.get_json() or {}
        
        # 从请求中获取设备信息
        device_id = data.get('device_id') or request.args.get('device_id')
        name = data.get('name') or request.args.get('name', f'ESP32-{device_id}')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'device_id is required'}), 400
        
        # 检查设备数量限制
        existing_count = Device.query.filter_by(device_type='esp32').count()
        existing_device = Device.get_by_device_id(device_id)
        
        if not existing_device and existing_count >= 1:
            return jsonify({
                'success': False, 
                'error': 'Maximum number of ESP32 devices (1) reached'
            }), 400
        
        # ESP32配置信息
        esp32_config = {
            'sensors': data.get('sensors', [
                'temperature', 'humidity', 'pressure', 'light', 
                'motion', 'distance', 'analog_inputs'
            ]),
            'capabilities': data.get('capabilities', [
                'wifi', 'bluetooth', 'gpio', 'pwm', 'adc', 'dac'
            ]),
            'gpio_pins': data.get('gpio_pins', {}),
            'wifi_info': {
                'ssid': data.get('wifi_ssid'),
                'ip_address': data.get('ip_address'),
                'mac_address': data.get('mac_address')
            },
            'firmware_version': data.get('firmware_version'),
            'chip_model': data.get('chip_model', 'ESP32')
        }
        
        # 注册或更新设备
        device = Device.register_device(
            device_id=device_id,
            device_type='esp32',
            name=name,
            description=data.get('description', 'ESP32 IoT device'),
            config=esp32_config
        )
        
        # 更新设备状态为在线
        device.update_status('online')
        
        return jsonify({
            'success': True,
            'message': 'ESP32 device registered successfully',
            'device': device.to_dict(),
            'server_time': datetime.utcnow().isoformat(),
            'assigned_id': device_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@esp32_bp.route('/heartbeat', methods=['POST', 'GET'])
def esp32_heartbeat():
    """ESP32心跳检测"""
    try:
        # 支持GET和POST请求
        if request.method == 'POST':
            data = request.get_json() or {}
            device_id = data.get('device_id')
            system_info = data.get('system_info', {})
        else:
            device_id = request.args.get('device_id')
            system_info = {}
        
        if not device_id:
            return jsonify({'success': False, 'error': 'device_id is required'}), 400
        
        device = Device.get_by_device_id(device_id)
        if not device:
            return jsonify({'success': False, 'error': 'Device not registered'}), 404
        
        # 更新设备状态和系统信息
        device.update_status('online')
        
        # 如果提供了系统信息，更新配置
        if system_info:
            current_config = device.config or {}
            current_config.update({
                'system_info': system_info,
                'last_heartbeat': datetime.utcnow().isoformat()
            })
            device.config = current_config
            db.session.commit()
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'status': 'online',
            'server_time': datetime.utcnow().isoformat(),
            'config_updated': bool(system_info)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@esp32_bp.route('/data', methods=['POST'])
def upload_esp32_data():
    """上传ESP32传感器数据"""
    try:
        data = request.get_json() or {}
        
        device_id = data.get('device_id')
        if not device_id:
            return jsonify({'success': False, 'error': 'device_id is required'}), 400
        
        # 验证设备
        device = Device.get_by_device_id(device_id)
        if not device or device.device_type != 'esp32':
            return jsonify({'success': False, 'error': 'Invalid ESP32 device'}), 404
        
        # 更新设备状态
        device.update_status('online')
        
        # 处理传感器数据
        added_data = []
        
        # 环境传感器数据
        sensor_mappings = {
            'temperature': '°C',
            'humidity': '%',
            'pressure': 'hPa',
            'light': 'lux',
            'uv_index': 'UV',
            'air_quality': 'AQI'
        }
        
        for sensor_type, unit in sensor_mappings.items():
            if sensor_type in data:
                sensor_data = SensorData.add_data(
                    device_id=device_id,
                    sensor_type=sensor_type,
                    value=float(data[sensor_type]),
                    unit=unit
                )
                added_data.append(sensor_data.to_dict())
        
        # 运动传感器
        if 'motion' in data:
            sensor_data = SensorData.add_data(
                device_id=device_id,
                sensor_type='motion',
                value=1 if data['motion'] else 0,
                unit='bool'
            )
            added_data.append(sensor_data.to_dict())
        
        # 距离传感器
        if 'distance' in data:
            sensor_data = SensorData.add_data(
                device_id=device_id,
                sensor_type='distance',
                value=float(data['distance']),
                unit='cm'
            )
            added_data.append(sensor_data.to_dict())
        
        # 模拟输入
        if 'analog_inputs' in data and isinstance(data['analog_inputs'], dict):
            for pin, value in data['analog_inputs'].items():
                sensor_data = SensorData.add_data(
                    device_id=device_id,
                    sensor_type=f'analog_pin_{pin}',
                    value=float(value),
                    unit='V',
                    metadata={'pin': pin, 'type': 'analog_input'}
                )
                added_data.append(sensor_data.to_dict())
        
        # 数字输入
        if 'digital_inputs' in data and isinstance(data['digital_inputs'], dict):
            for pin, value in data['digital_inputs'].items():
                sensor_data = SensorData.add_data(
                    device_id=device_id,
                    sensor_type=f'digital_pin_{pin}',
                    value=1 if value else 0,
                    unit='bool',
                    metadata={'pin': pin, 'type': 'digital_input'}
                )
                added_data.append(sensor_data.to_dict())
        
        # 系统状态
        if 'system_status' in data:
            status = data['system_status']
            if 'free_heap' in status:
                sensor_data = SensorData.add_data(
                    device_id=device_id,
                    sensor_type='free_heap',
                    value=float(status['free_heap']),
                    unit='bytes'
                )
                added_data.append(sensor_data.to_dict())
            
            if 'wifi_rssi' in status:
                sensor_data = SensorData.add_data(
                    device_id=device_id,
                    sensor_type='wifi_rssi',
                    value=float(status['wifi_rssi']),
                    unit='dBm'
                )
                added_data.append(sensor_data.to_dict())
        
        return jsonify({
            'success': True,
            'message': f'Uploaded {len(added_data)} sensor readings',
            'device_id': device_id,
            'data_count': len(added_data),
            'server_time': datetime.utcnow().isoformat()
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': 'Invalid data format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@esp32_bp.route('/control', methods=['POST'])
def control_esp32():
    """控制ESP32设备"""
    try:
        data = request.get_json() or {}
        
        device_id = data.get('device_id')
        action = data.get('action')
        
        if not device_id or not action:
            return jsonify({'success': False, 'error': 'device_id and action are required'}), 400
        
        # 验证设备
        device = Device.get_by_device_id(device_id)
        if not device or device.device_type != 'esp32':
            return jsonify({'success': False, 'error': 'Invalid ESP32 device'}), 404
        
        # 支持的控制动作
        supported_actions = {
            'gpio_write': ['pin', 'value'],
            'pwm_write': ['pin', 'value', 'frequency'],
            'dac_write': ['pin', 'value'],
            'servo_write': ['pin', 'angle'],
            'led_control': ['pin', 'brightness'],
            'relay_control': ['pin', 'state'],
            'restart': [],
            'deep_sleep': ['duration'],
            'wifi_reconnect': []
        }
        
        if action not in supported_actions:
            return jsonify({
                'success': False, 
                'error': f'Unsupported action. Supported: {list(supported_actions.keys())}'
            }), 400
        
        # 验证必需参数
        required_params = supported_actions[action]
        for param in required_params:
            if param not in data:
                return jsonify({'success': False, 'error': f'Missing parameter: {param}'}), 400
        
        # 构建控制命令
        control_data = {
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'device_id': device_id,
            'parameters': {param: data[param] for param in required_params if param in data}
        }
        
        # 在实际应用中，这里可以通过MQTT、WebSocket或其他方式将命令推送给ESP32
        # 目前返回命令信息供ESP32轮询获取
        
        return jsonify({
            'success': True,
            'message': f'Control command "{action}" queued for device',
            'control_data': control_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@esp32_bp.route('/config/<device_id>', methods=['GET', 'PUT'])
def esp32_config(device_id):
    """获取或更新ESP32设备配置"""
    try:
        device = Device.get_by_device_id(device_id)
        if not device or device.device_type != 'esp32':
            return jsonify({'success': False, 'error': 'Invalid ESP32 device'}), 404
        
        if request.method == 'GET':
            # 获取配置
            return jsonify({
                'success': True,
                'device_id': device_id,
                'config': device.config or {},
                'server_time': datetime.utcnow().isoformat()
            })
        
        elif request.method == 'PUT':
            # 更新配置
            data = request.get_json() or {}
            new_config = data.get('config', {})
            
            # 合并配置
            current_config = device.config or {}
            current_config.update(new_config)
            current_config['last_config_update'] = datetime.utcnow().isoformat()
            
            device.config = current_config
            device.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Configuration updated',
                'device_id': device_id,
                'config': device.config
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@esp32_bp.route('/status/<device_id>', methods=['GET'])
def get_esp32_status(device_id):
    """获取ESP32设备详细状态"""
    try:
        device = Device.get_by_device_id(device_id)
        if not device or device.device_type != 'esp32':
            return jsonify({'success': False, 'error': 'Invalid ESP32 device'}), 404
        
        # 获取最新传感器数据
        latest_data = SensorData.get_latest_data(device_id, limit=20)
        
        # 按传感器类型组织数据
        sensor_readings = {}
        system_status = {}
        
        for data_point in latest_data:
            reading_info = {
                'value': data_point.value,
                'unit': data_point.unit,
                'timestamp': data_point.timestamp.isoformat()
            }
            
            # 区分系统状态和传感器数据
            if data_point.sensor_type in ['free_heap', 'wifi_rssi']:
                system_status[data_point.sensor_type] = reading_info
            else:
                sensor_readings[data_point.sensor_type] = reading_info
        
        return jsonify({
            'success': True,
            'device': device.to_dict(),
            'sensor_readings': sensor_readings,
            'system_status': system_status,
            'server_time': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@esp32_bp.route('/devices', methods=['GET'])
def list_esp32_devices():
    """列出所有ESP32设备"""
    try:
        devices = Device.query.filter_by(device_type='esp32').all()
        
        device_list = []
        for device in devices:
            device_info = device.to_dict()
            # 添加最新数据
            latest_data = SensorData.get_latest_data(device.device_id, limit=10)
            device_info['latest_readings'] = [data.to_dict() for data in latest_data]
            device_list.append(device_info)
        
        return jsonify({
            'success': True,
            'devices': device_list,
            'count': len(device_list),
            'max_devices': 1
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@esp32_bp.route('/firmware', methods=['POST'])
def esp32_firmware_update():
    """ESP32固件更新接口"""
    try:
        data = request.get_json() or {}
        
        device_id = data.get('device_id')
        firmware_version = data.get('firmware_version')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'device_id is required'}), 400
        
        device = Device.get_by_device_id(device_id)
        if not device or device.device_type != 'esp32':
            return jsonify({'success': False, 'error': 'Invalid ESP32 device'}), 404
        
        # 更新固件版本信息
        current_config = device.config or {}
        current_config['firmware_version'] = firmware_version
        current_config['last_firmware_update'] = datetime.utcnow().isoformat()
        
        device.config = current_config
        device.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Firmware version updated',
            'device_id': device_id,
            'firmware_version': firmware_version
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

