from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models import db
from src.models.device import Device
from src.models.sensor_data import SensorData

microbit_bp = Blueprint('microbit', __name__)

@microbit_bp.route('/register', methods=['POST'])
def register_microbit():
    """注册micro:bit设备"""
    try:
        data = request.get_json() or {}
        
        # 从请求中获取设备信息
        device_id = data.get('device_id') or request.args.get('device_id')
        name = data.get('name') or request.args.get('name', f'MicroBit-{device_id}')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'device_id is required'}), 400
        
        # 检查设备数量限制
        existing_count = Device.query.filter_by(device_type='microbit').count()
        existing_device = Device.get_by_device_id(device_id)
        
        if not existing_device and existing_count >= 2:
            return jsonify({
                'success': False, 
                'error': 'Maximum number of micro:bit devices (2) reached'
            }), 400
        
        # 注册或更新设备
        device = Device.register_device(
            device_id=device_id,
            device_type='microbit',
            name=name,
            description=data.get('description', 'BBC micro:bit device'),
            config={
                'sensors': ['temperature', 'light', 'accelerometer', 'compass'],
                'capabilities': ['display', 'buttons', 'radio']
            }
        )
        
        # 更新设备状态为在线
        device.update_status('online')
        
        return jsonify({
            'success': True,
            'message': 'Device registered successfully',
            'device': device.to_dict(),
            'server_time': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@microbit_bp.route('/heartbeat', methods=['POST', 'GET'])
def microbit_heartbeat():
    """micro:bit心跳检测"""
    try:
        # 支持GET和POST请求
        if request.method == 'POST':
            data = request.get_json() or {}
            device_id = data.get('device_id')
        else:
            device_id = request.args.get('device_id')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'device_id is required'}), 400
        
        device = Device.get_by_device_id(device_id)
        if not device:
            return jsonify({'success': False, 'error': 'Device not registered'}), 404
        
        # 更新设备状态
        device.update_status('online')
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'status': 'online',
            'server_time': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@microbit_bp.route('/data', methods=['POST'])
def upload_microbit_data():
    """上传micro:bit传感器数据"""
    try:
        data = request.get_json() or {}
        
        device_id = data.get('device_id')
        if not device_id:
            return jsonify({'success': False, 'error': 'device_id is required'}), 400
        
        # 验证设备
        device = Device.get_by_device_id(device_id)
        if not device or device.device_type != 'microbit':
            return jsonify({'success': False, 'error': 'Invalid micro:bit device'}), 404
        
        # 更新设备状态
        device.update_status('online')
        
        # 处理传感器数据
        added_data = []
        
        # 温度数据
        if 'temperature' in data:
            sensor_data = SensorData.add_data(
                device_id=device_id,
                sensor_type='temperature',
                value=float(data['temperature']),
                unit='°C'
            )
            added_data.append(sensor_data.to_dict())
        
        # 光照数据
        if 'light' in data:
            sensor_data = SensorData.add_data(
                device_id=device_id,
                sensor_type='light',
                value=float(data['light']),
                unit='lux'
            )
            added_data.append(sensor_data.to_dict())
        
        # 加速度计数据
        if 'accelerometer' in data:
            accel_data = data['accelerometer']
            if isinstance(accel_data, dict):
                # 分别存储X, Y, Z轴数据
                for axis in ['x', 'y', 'z']:
                    if axis in accel_data:
                        sensor_data = SensorData.add_data(
                            device_id=device_id,
                            sensor_type=f'accelerometer_{axis}',
                            value=float(accel_data[axis]),
                            unit='g'
                        )
                        added_data.append(sensor_data.to_dict())
            else:
                # 存储加速度计总值
                sensor_data = SensorData.add_data(
                    device_id=device_id,
                    sensor_type='accelerometer',
                    value=float(accel_data),
                    unit='g'
                )
                added_data.append(sensor_data.to_dict())
        
        # 指南针数据
        if 'compass' in data:
            sensor_data = SensorData.add_data(
                device_id=device_id,
                sensor_type='compass',
                value=float(data['compass']),
                unit='°'
            )
            added_data.append(sensor_data.to_dict())
        
        # 按钮状态
        if 'button_a' in data:
            sensor_data = SensorData.add_data(
                device_id=device_id,
                sensor_type='button_a',
                value=1 if data['button_a'] else 0,
                unit='bool'
            )
            added_data.append(sensor_data.to_dict())
        
        if 'button_b' in data:
            sensor_data = SensorData.add_data(
                device_id=device_id,
                sensor_type='button_b',
                value=1 if data['button_b'] else 0,
                unit='bool'
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

@microbit_bp.route('/command', methods=['POST'])
def send_microbit_command():
    """向micro:bit发送命令"""
    try:
        data = request.get_json() or {}
        
        device_id = data.get('device_id')
        command = data.get('command')
        
        if not device_id or not command:
            return jsonify({'success': False, 'error': 'device_id and command are required'}), 400
        
        # 验证设备
        device = Device.get_by_device_id(device_id)
        if not device or device.device_type != 'microbit':
            return jsonify({'success': False, 'error': 'Invalid micro:bit device'}), 404
        
        # 支持的命令类型
        supported_commands = {
            'display_text': 'text',
            'display_icon': 'icon',
            'play_melody': 'melody',
            'set_pixel': 'pixel_data',
            'clear_display': None,
            'show_temperature': None,
            'show_light': None
        }
        
        if command not in supported_commands:
            return jsonify({
                'success': False, 
                'error': f'Unsupported command. Supported: {list(supported_commands.keys())}'
            }), 400
        
        # 构建命令响应
        command_data = {
            'command': command,
            'timestamp': datetime.utcnow().isoformat(),
            'device_id': device_id
        }
        
        # 添加命令参数
        param_key = supported_commands[command]
        if param_key and param_key in data:
            command_data[param_key] = data[param_key]
        
        # 在实际应用中，这里可以通过WebSocket或其他方式将命令推送给micro:bit
        # 目前返回命令信息供micro:bit轮询获取
        
        return jsonify({
            'success': True,
            'message': 'Command queued for device',
            'command_data': command_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@microbit_bp.route('/status/<device_id>', methods=['GET'])
def get_microbit_status(device_id):
    """获取micro:bit设备状态"""
    try:
        device = Device.get_by_device_id(device_id)
        if not device or device.device_type != 'microbit':
            return jsonify({'success': False, 'error': 'Invalid micro:bit device'}), 404
        
        # 获取最新传感器数据
        latest_data = SensorData.get_latest_data(device_id, limit=10)
        
        # 按传感器类型组织数据
        sensor_readings = {}
        for data_point in latest_data:
            sensor_readings[data_point.sensor_type] = {
                'value': data_point.value,
                'unit': data_point.unit,
                'timestamp': data_point.timestamp.isoformat()
            }
        
        return jsonify({
            'success': True,
            'device': device.to_dict(),
            'sensor_readings': sensor_readings,
            'server_time': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@microbit_bp.route('/devices', methods=['GET'])
def list_microbit_devices():
    """列出所有micro:bit设备"""
    try:
        devices = Device.query.filter_by(device_type='microbit').all()
        
        device_list = []
        for device in devices:
            device_info = device.to_dict()
            # 添加最新数据
            latest_data = SensorData.get_latest_data(device.device_id, limit=5)
            device_info['latest_readings'] = [data.to_dict() for data in latest_data]
            device_list.append(device_info)
        
        return jsonify({
            'success': True,
            'devices': device_list,
            'count': len(device_list),
            'max_devices': 2
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

