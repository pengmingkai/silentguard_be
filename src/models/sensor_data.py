from datetime import datetime
from src.models import db

class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('devices.device_id'), nullable=False, index=True)
    sensor_type = db.Column(db.String(50), nullable=False)  # temperature, humidity, light, accelerometer, etc.
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))  # °C, %, lux, g, etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # 额外的数据字段（JSON格式）
    extra_data = db.Column(db.JSON)
    
    def __repr__(self):
        return f'<SensorData {self.device_id}: {self.sensor_type}={self.value}{self.unit}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'sensor_type': self.sensor_type,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metadata': self.extra_data
        }
    
    @classmethod
    def add_data(cls, device_id, sensor_type, value, unit=None, metadata=None):
        """添加传感器数据"""
        data = cls(
            device_id=device_id,
            sensor_type=sensor_type,
            value=value,
            unit=unit,
            extra_data=metadata
        )
        db.session.add(data)
        db.session.commit()
        return data
    
    @classmethod
    def get_latest_data(cls, device_id, sensor_type=None, limit=10):
        """获取最新的传感器数据"""
        query = cls.query.filter_by(device_id=device_id)
        if sensor_type:
            query = query.filter_by(sensor_type=sensor_type)
        return query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_data_by_time_range(cls, device_id, start_time, end_time, sensor_type=None):
        """根据时间范围获取数据"""
        query = cls.query.filter(
            cls.device_id == device_id,
            cls.timestamp >= start_time,
            cls.timestamp <= end_time
        )
        if sensor_type:
            query = query.filter_by(sensor_type=sensor_type)
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_average_value(cls, device_id, sensor_type, start_time, end_time):
        """获取指定时间范围内的平均值"""
        result = db.session.query(db.func.avg(cls.value)).filter(
            cls.device_id == device_id,
            cls.sensor_type == sensor_type,
            cls.timestamp >= start_time,
            cls.timestamp <= end_time
        ).scalar()
        return float(result) if result else None

