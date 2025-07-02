from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 导入所有模型
from .device import Device
from .sensor_data import SensorData
from .user import User

