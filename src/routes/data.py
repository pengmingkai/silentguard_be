from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models import db
from src.models.sensor_data import SensorData
from src.models.device import Device

data_bp = Blueprint('data', __name__)

@data_bp.route('/data', methods=['POST'])
def add_sensor_data():
    """添加传感器数据（通用接口）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        required_fields = ['device_id', 'sensor_type', 'value']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        # 验证设备是否存在
        device = Device.get_by_device_id(data['device_id'])
        if not device:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        # 更新设备状态为在线
        device.update_status('online')
        
        # 添加传感器数据
        sensor_data = SensorData.add_data(
            device_id=data['device_id'],
            sensor_type=data['sensor_type'],
            value=float(data['value']),
            unit=data.get('unit'),
            metadata=data.get('metadata')
        )
        
        return jsonify({
            'success': True,
            'message': 'Data added successfully',
            'data': sensor_data.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'error': 'Invalid value format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@data_bp.route('/data/batch', methods=['POST'])
def add_batch_sensor_data():
    """批量添加传感器数据"""
    try:
        data = request.get_json()
        if not data or 'data_list' not in data:
            return jsonify({'success': False, 'error': 'No data_list provided'}), 400
            
        data_list = data['data_list']
        if not isinstance(data_list, list):
            return jsonify({'success': False, 'error': 'data_list must be an array'}), 400
        
        added_data = []
        errors = []
        
        for i, item in enumerate(data_list):
            try:
                required_fields = ['device_id', 'sensor_type', 'value']
                for field in required_fields:
                    if field not in item:
                        errors.append(f'Item {i}: Missing field {field}')
                        continue
                
                # 验证设备是否存在
                device = Device.get_by_device_id(item['device_id'])
                if not device:
                    errors.append(f'Item {i}: Device {item["device_id"]} not found')
                    continue
                
                # 添加传感器数据
                sensor_data = SensorData.add_data(
                    device_id=item['device_id'],
                    sensor_type=item['sensor_type'],
                    value=float(item['value']),
                    unit=item.get('unit'),
                    metadata=item.get('metadata')
                )
                added_data.append(sensor_data.to_dict())
                
                # 更新设备状态
                device.update_status('online')
                
            except Exception as e:
                errors.append(f'Item {i}: {str(e)}')
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(data_list)} items',
            'added_count': len(added_data),
            'error_count': len(errors),
            'added_data': added_data,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@data_bp.route('/data/query', methods=['GET'])
def query_sensor_data():
    """查询传感器数据"""
    try:
        device_id = request.args.get('device_id')
        sensor_type = request.args.get('sensor_type')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        limit = int(request.args.get('limit', 100))
        
        if not device_id:
            return jsonify({'success': False, 'error': 'device_id is required'}), 400
        
        # 验证设备是否存在
        device = Device.get_by_device_id(device_id)
        if not device:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        if start_time and end_time:
            # 时间范围查询
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                data = SensorData.get_data_by_time_range(device_id, start_dt, end_dt, sensor_type)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid datetime format'}), 400
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

@data_bp.route('/data/latest', methods=['GET'])
def get_latest_data():
    """获取所有设备的最新数据"""
    try:
        device_type = request.args.get('device_type')  # microbit, esp32
        
        # 获取设备列表
        query = Device.query.filter_by(status='online')
        if device_type:
            query = query.filter_by(device_type=device_type)
        devices = query.all()
        
        result = {}
        for device in devices:
            # 获取每个设备的最新数据
            latest_data = SensorData.get_latest_data(device.device_id, limit=5)
            result[device.device_id] = {
                'device_info': device.to_dict(),
                'latest_data': [item.to_dict() for item in latest_data]
            }
        
        return jsonify({
            'success': True,
            'data': result,
            'device_count': len(devices)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@data_bp.route('/data/statistics', methods=['GET'])
def get_data_statistics():
    """获取数据统计信息"""
    try:
        hours = int(request.args.get('hours', 24))
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # 统计总数据量
        total_records = SensorData.query.filter(
            SensorData.timestamp >= start_time,
            SensorData.timestamp <= end_time
        ).count()
        
        # 按设备类型统计
        device_stats = db.session.query(
            Device.device_type,
            db.func.count(SensorData.id).label('record_count')
        ).join(SensorData, Device.device_id == SensorData.device_id).filter(
            SensorData.timestamp >= start_time,
            SensorData.timestamp <= end_time
        ).group_by(Device.device_type).all()
        
        # 按传感器类型统计
        sensor_stats = db.session.query(
            SensorData.sensor_type,
            db.func.count(SensorData.id).label('record_count')
        ).filter(
            SensorData.timestamp >= start_time,
            SensorData.timestamp <= end_time
        ).group_by(SensorData.sensor_type).all()
        
        return jsonify({
            'success': True,
            'time_range_hours': hours,
            'statistics': {
                'total_records': total_records,
                'by_device_type': {stat[0]: stat[1] for stat in device_stats},
                'by_sensor_type': {stat[0]: stat[1] for stat in sensor_stats}
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

