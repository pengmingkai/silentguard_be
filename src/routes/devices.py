from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models import db
from src.models.device import Device
from src.models.sensor_data import SensorData

devices_bp = Blueprint('devices', __name__)

@devices_bp.route('/devices', methods=['GET'])
def get_devices():
    """获取所有设备列表"""
    try:
        device_type = request.args.get('type')  # microbit, esp32
        status = request.args.get('status')     # online, offline, error
        
        query = Device.query
        if device_type:
            query = query.filter_by(device_type=device_type)
        if status:
            query = query.filter_by(status=status)
            
        devices = query.all()
        return jsonify({
            'success': True,
            'data': [device.to_dict() for device in devices],
            'count': len(devices)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@devices_bp.route('/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    """获取单个设备详情"""
    try:
        device = Device.get_by_device_id(device_id)
        if not device:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
            
        return jsonify({
            'success': True,
            'data': device.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@devices_bp.route('/devices/<device_id>/status', methods=['PUT'])
def update_device_status(device_id):
    """更新设备状态"""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'success': False, 'error': 'Status is required'}), 400
            
        device = Device.get_by_device_id(device_id)
        if not device:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
            
        device.update_status(data['status'])
        return jsonify({
            'success': True,
            'message': 'Device status updated',
            'data': device.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@devices_bp.route('/devices/<device_id>/data', methods=['GET'])
def get_device_data(device_id):
    """获取设备传感器数据"""
    try:
        device = Device.get_by_device_id(device_id)
        if not device:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
            
        # 获取查询参数
        sensor_type = request.args.get('sensor_type')
        limit = int(request.args.get('limit', 50))
        hours = request.args.get('hours')  # 获取最近N小时的数据
        
        if hours:
            # 获取指定时间范围的数据
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=int(hours))
            data = SensorData.get_data_by_time_range(device_id, start_time, end_time, sensor_type)
        else:
            # 获取最新数据
            data = SensorData.get_latest_data(device_id, sensor_type, limit)
            
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in data],
            'count': len(data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@devices_bp.route('/devices/<device_id>/data/summary', methods=['GET'])
def get_device_data_summary(device_id):
    """获取设备数据统计摘要"""
    try:
        device = Device.get_by_device_id(device_id)
        if not device:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
            
        hours = int(request.args.get('hours', 24))
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取所有传感器类型
        sensor_types = db.session.query(SensorData.sensor_type).filter_by(device_id=device_id).distinct().all()
        sensor_types = [st[0] for st in sensor_types]
        
        summary = {}
        for sensor_type in sensor_types:
            avg_value = SensorData.get_average_value(device_id, sensor_type, start_time, end_time)
            latest_data = SensorData.get_latest_data(device_id, sensor_type, 1)
            
            summary[sensor_type] = {
                'average': avg_value,
                'latest': latest_data[0].to_dict() if latest_data else None
            }
            
        return jsonify({
            'success': True,
            'device_id': device_id,
            'time_range_hours': hours,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@devices_bp.route('/devices/stats', methods=['GET'])
def get_devices_stats():
    """获取设备统计信息"""
    try:
        total_devices = Device.query.count()
        online_devices = Device.query.filter_by(status='online').count()
        microbit_devices = Device.query.filter_by(device_type='microbit').count()
        esp32_devices = Device.query.filter_by(device_type='esp32').count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_devices': total_devices,
                'online_devices': online_devices,
                'offline_devices': total_devices - online_devices,
                'microbit_devices': microbit_devices,
                'esp32_devices': esp32_devices
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

