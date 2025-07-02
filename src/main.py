import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.config import config
from src.models import db
from src.models.device import Device
from src.models.sensor_data import SensorData
from src.models.user import User

# 导入所有路由蓝图
from src.routes.user import user_bp
from src.routes.devices import devices_bp
from src.routes.data import data_bp
from src.routes.microbit import microbit_bp
from src.routes.esp32 import esp32_bp

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # 加载配置
    config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # 启用CORS支持
    CORS(app, origins="*")
    
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
    
    # 注册蓝图
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(devices_bp, url_prefix='/api')
    app.register_blueprint(data_bp, url_prefix='/api')
    app.register_blueprint(microbit_bp, url_prefix='/api/microbit')
    app.register_blueprint(esp32_bp, url_prefix='/api/esp32')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
        # 创建默认管理员用户（如果不存在）
        admin_user = User.get_by_username('admin')
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@iot-server.local',
                role='admin',
                password_hash='admin123'  # 在实际应用中应该使用哈希密码
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✓ 创建默认管理员用户: admin")
    
    # API根路径
    @app.route('/api')
    def api_info():
        """API信息"""
        return jsonify({
            'name': 'IoT Server API',
            'version': '1.0.0',
            'description': 'Flask-RESTful API for IoT devices',
            'endpoints': {
                'devices': '/api/devices',
                'data': '/api/data',
                'microbit': '/api/microbit',
                'esp32': '/api/esp32',
                'users': '/api/users'
            },
            'status': 'running'
        })
    
    # 健康检查
    @app.route('/health')
    def health_check():
        """健康检查端点"""
        try:
            # 检查数据库连接
            db.session.execute('SELECT 1')
            db_status = 'healthy'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        # 统计设备数量
        try:
            total_devices = Device.query.count()
            online_devices = Device.query.filter_by(status='online').count()
            microbit_devices = Device.query.filter_by(device_type='microbit').count()
            esp32_devices = Device.query.filter_by(device_type='esp32').count()
        except:
            total_devices = online_devices = microbit_devices = esp32_devices = 0
        
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'devices': {
                'total': total_devices,
                'online': online_devices,
                'microbit': microbit_devices,
                'esp32': esp32_devices
            },
            'timestamp': db.func.now()
        })
    
    # 静态文件服务
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                # 返回API信息而不是404
                return jsonify({
                    'message': 'IoT Server is running',
                    'api_endpoint': '/api',
                    'health_check': '/health',
                    'documentation': 'See README.md for API documentation'
                })
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'success': False, 'error': 'Bad request'}), 400
    
    return app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("IoT Server Starting...")
    print("=" * 50)
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')}")
    print("API Endpoints:")
    print("  - /api - API信息")
    print("  - /health - 健康检查")
    print("  - /api/devices - 设备管理")
    print("  - /api/data - 数据管理")
    print("  - /api/microbit - micro:bit接口")
    print("  - /api/esp32 - ESP32接口")
    print("  - /api/users - 用户管理")
    print("=" * 50)
    
    # 启动服务器
    app.run(host='0.0.0.0', port=5000, debug=True)

