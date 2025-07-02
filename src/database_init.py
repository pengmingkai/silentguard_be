"""
数据库初始化脚本
用于创建数据库表和初始数据
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from src.config import config
from src.models import db
from src.models.device import Device
from src.models.sensor_data import SensorData
from src.models.user import User

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 加载配置
    config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # 尝试连接MySQL，失败则使用SQLite
    try:
        # 测试MySQL连接
        import pymysql
        connection = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            port=app.config['MYSQL_PORT'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD']
        )
        
        # 创建数据库（如果不存在）
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {app.config['MYSQL_DATABASE']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.commit()
        connection.close()
        
        print(f"✓ MySQL数据库连接成功: {app.config['MYSQL_DATABASE']}")
        
    except Exception as e:
        print(f"⚠ MySQL连接失败，使用SQLite: {e}")
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['FALLBACK_DATABASE_URI']
        
        # 确保SQLite数据库目录存在
        db_dir = os.path.dirname(app.config['FALLBACK_DATABASE_URI'].replace('sqlite:///', ''))
        os.makedirs(db_dir, exist_ok=True)
    
    # 初始化数据库
    db.init_app(app)
    
    return app

def init_database():
    """初始化数据库表和数据"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✓ 数据库表创建完成")
        
        # 创建默认管理员用户
        admin_user = User.get_by_username('admin')
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@iot-server.local',
                role='admin',
                password_hash='admin123'  # 在实际应用中应该使用哈希密码
            )
            db.session.add(admin_user)
            print("✓ 创建默认管理员用户: admin")
        
        # 提交更改
        db.session.commit()
        print("✓ 数据库初始化完成")

if __name__ == '__main__':
    init_database()

