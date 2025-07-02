from datetime import datetime
from src.models import db

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    device_type = db.Column(db.Enum('microbit', 'esp32', name='device_types'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum('online', 'offline', 'error', name='device_status'), default='offline')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 设备配置信息（JSON格式存储）
    config = db.Column(db.JSON)
    
    # 关联传感器数据
    sensor_data = db.relationship('SensorData', backref='device', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Device {self.device_id}: {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'device_type': self.device_type,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'config': self.config
        }
    
    def update_status(self, status):
        """更新设备状态和最后在线时间"""
        self.status = status
        self.last_seen = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def get_by_device_id(cls, device_id):
        """根据设备ID获取设备"""
        return cls.query.filter_by(device_id=device_id).first()
    
    @classmethod
    def get_online_devices(cls, device_type=None):
        """获取在线设备"""
        query = cls.query.filter_by(status='online')
        if device_type:
            query = query.filter_by(device_type=device_type)
        return query.all()
    
    @classmethod
    def register_device(cls, device_id, device_type, name, description=None, config=None):
        """注册新设备"""
        existing_device = cls.get_by_device_id(device_id)
        if existing_device:
            # 更新现有设备信息
            existing_device.name = name
            existing_device.description = description
            existing_device.config = config
            existing_device.updated_at = datetime.utcnow()
            db.session.commit()
            return existing_device
        else:
            # 创建新设备
            new_device = cls(
                device_id=device_id,
                device_type=device_type,
                name=name,
                description=description,
                config=config
            )
            db.session.add(new_device)
            db.session.commit()
            return new_device

