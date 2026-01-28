from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
import os
import sys
import json
from models import db
from terminal import TerminalManager

# 读取配置文件
basedir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.dirname(basedir)
config_path = os.path.join(project_root, 'config.json')

print(f"========== 设备管理系统启动 ==========")
print(f"Python版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")
print(f"backend目录: {basedir}")
print(f"项目根目录: {project_root}")
print(f"配置文件路径: {config_path}")
print(f"配置文件存在: {os.path.exists(config_path)}")

# 默认配置
DEFAULT_CONFIG = {
    "server": {"host": "0.0.0.0", "port": 3001, "debug": True},
    "admin": {"username": "admin", "password": "admin123"},
    "database": {"path": "backend/device_manager.db"},
    "user": {"default_password": "123456"},
    "device": {"max_devices_per_user": 1},  # 每个用户最多占用的设备数量
    "socketio": {"ping_timeout": 120, "ping_interval": 25, "max_http_buffer_size": 1073741824},
    "system": {"title": "设备使用管理系统"}  # 系统标题配置
}

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
        print(f"✅ 已加载配置文件: {config_path}")
except FileNotFoundError:
    CONFIG = DEFAULT_CONFIG
    print(f"⚠️ 配置文件不存在: {config_path}")
    print(f"⚠️ 使用默认配置")
    # 创建默认配置文件
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        print(f"✅ 已创建默认配置文件: {config_path}")
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
except Exception as e:
    CONFIG = DEFAULT_CONFIG
    print(f"❌ 读取配置文件失败: {e}")
    print(f"使用默认配置")

print(f"初始化Flask应用...")
static_folder = os.path.join(project_root, 'frontend')
print(f"静态文件目录: {static_folder}")
print(f"静态文件目录存在: {os.path.exists(static_folder)}")

app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

print(f"初始化SocketIO...")
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    max_http_buffer_size=CONFIG['socketio']['max_http_buffer_size'],
    ping_timeout=CONFIG['socketio']['ping_timeout'],
    ping_interval=CONFIG['socketio']['ping_interval']
)

# 创建终端管理器
print(f"初始化终端管理器...")
terminal_manager = TerminalManager(socketio)

# 配置数据库
db_path = os.path.join(project_root, CONFIG['database']['path'])
print(f"数据库路径: {db_path}")
print(f"数据库目录: {os.path.dirname(db_path)}")
os.makedirs(os.path.dirname(db_path), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
print(f"初始化数据库...")
try:
    db.init_app(app)
    print(f"✅ 数据库连接初始化成功")
except Exception as e:
    print(f"❌ 数据库连接初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 在数据库初始化后导入模型类（重要！确保模型能被正确注册）
from models import Device, User, UsageRecord, AllowedUser, AuditLog, QuickCommand

# 创建数据库表
print(f"创建数据库表...")
try:
    with app.app_context():
        # 确保数据库目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"✅ 创建数据库目录: {db_dir}")
        
        # 导入所有模型以确保它们被注册
        import models
        
        # 确保所有模型都已注册（显式引用）
        # 这样可以确保 SQLAlchemy 知道所有的表模型
        _ = [Device, User, UsageRecord, AllowedUser, AuditLog]
        
        # 创建所有表
        db.create_all()
        
        # 验证表是否真的被创建
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print(f"✅ 数据库表创建成功，当前存在的表: {', '.join(table_names)}")
        
        # 检查必需的表是否都存在
        required_tables = ['devices', 'users', 'usage_records', 'allowed_users', 'audit_logs']
        missing_tables = [t for t in required_tables if t not in table_names]
        if missing_tables:
            raise Exception(f"缺少必需的表: {', '.join(missing_tables)}")
        
        # 创建默认管理员用户
        print(f"检查管理员用户...")
        admin_username = CONFIG['admin']['username']
        admin_password = CONFIG['admin']['password']
        
        try:
            admin = User.query.filter_by(username=admin_username).first()
        except:
            # 如果查询失败（表可能刚创建），直接创建用户
            admin = None
        
        if not admin:
            admin = User(username=admin_username, password=admin_password, is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print(f"✅ 创建管理员用户: {admin_username}")
        else:
            print(f"✅ 管理员用户已存在: {admin_username}")
except Exception as e:
    print(f"❌ 数据库初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"✅ 所有初始化完成")
print(f"{'='*40}\n")

# ==================== 工具函数 ====================

def clean_old_audit_logs():
    """清理30天前的审计日志"""
    try:
        from datetime import timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # 删除30天前的审计日志
        deleted_count = AuditLog.query.filter(
            AuditLog.created_at < thirty_days_ago
        ).delete()
        
        if deleted_count > 0:
            db.session.commit()
            print(f"✅ 已清理 {deleted_count} 条30天前的审计日志")
        
        return deleted_count
    except Exception as e:
        print(f"❌ 清理审计日志失败: {e}")
        db.session.rollback()
        return 0

# ==================== 后台任务 ====================

def start_background_tasks():
    """启动后台定时任务"""
    import threading
    import time
    
    def cleanup_task():
        """定期清理任务"""
        while True:
            try:
                # 每24小时清理一次30天前的审计日志
                time.sleep(86400)  # 24小时 = 86400秒
                with app.app_context():
                    clean_old_audit_logs()
            except Exception as e:
                print(f"❌ 后台清理任务出错: {e}")
    
    # 启动清理线程
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    print(f"✅ 后台清理任务已启动（每24小时清理30天前的审计日志）")
    
    # 应用启动时立即清理一次
    try:
        with app.app_context():
            clean_old_audit_logs()
    except Exception as e:
        print(f"❌ 初始清理失败: {e}")

# ==================== 辅助函数 ====================

def log_audit(action_type, operator, details=None, ip_address=None):
    """
    记录审计日志
    
    :param action_type: 操作类型，如 'login', 'device_add', 'device_delete', 'user_add' 等
    :param operator: 操作人
    :param details: 操作详情（字典格式，会转为JSON）
    :param ip_address: IP地址，如果不提供则从request中获取
    """
    try:
        if ip_address is None:
            ip_address = request.remote_addr if request else None
        
        details_json = json.dumps(details, ensure_ascii=False) if details else None
        
        log = AuditLog(
            action_type=action_type,
            operator=operator,
            ip_address=ip_address,
            details=details_json
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"❌ 记录审计日志失败: {e}")
        db.session.rollback()

def check_and_release_expired_devices():
    """检查并自动释放过期的设备"""
    now = datetime.now()
    expired_devices = Device.query.filter(
        Device.status == 'occupied',
        Device.occupy_until < now
    ).all()
    
    for device in expired_devices:
        device.status = 'available'
        device.current_user = None
        device.current_user_account = None
        device.occupy_duration = 2
        device.occupy_until = None
        
        # 更新使用记录
        record = UsageRecord.query.filter_by(
            device_id=device.id,
            end_time=None
        ).order_by(UsageRecord.start_time.desc()).first()
        
        if record:
            record.end_time = now
    
    if expired_devices:
        db.session.commit()

# ==================== 前端路由 ====================

@app.route('/')
def index():
    """返回前端首页"""
    return send_from_directory(app.static_folder, 'index.html')

# ==================== 配置 API ====================

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置信息（不包含敏感信息）"""
    return jsonify({
        'admin_username': CONFIG['admin']['username'],
        'default_password': CONFIG['user']['default_password'],
        'system': {
            'title': CONFIG.get('system', {}).get('title', '设备使用管理系统')  # 获取系统标题，如果未配置则使用默认值
        },
        'device': {
            'max_devices_per_user': CONFIG.get('device', {}).get('max_devices_per_user', 1)  # 获取每个用户最多占用设备数量
        }
    })

@app.route('/api/config/system/title', methods=['PUT'])
def update_system_title():
    """更新系统标题"""
    data = request.json
    if not data or 'title' not in data:
        return jsonify({'message': '标题不能为空'}), 400
    
    new_title = data['title'].strip()
    if not new_title:
        return jsonify({'message': '标题不能为空'}), 400
    
    # 更新内存中的配置
    CONFIG.setdefault('system', {})
    CONFIG['system']['title'] = new_title
    
    # 保存到配置文件
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(CONFIG, f, ensure_ascii=False, indent=2)
        return jsonify({
            'message': '系统标题已更新',
            'title': new_title
        })
    except Exception as e:
        return jsonify({'message': f'保存配置失败: {str(e)}'}), 500

@app.route('/api/config/device/limit', methods=['PUT'])
def update_device_limit():
    """更新每个用户最多占用设备数量"""
    data = request.json
    if not data or 'max_devices_per_user' not in data:
        return jsonify({'message': '参数错误'}), 400
    
    try:
        max_devices = int(data['max_devices_per_user'])
        if max_devices < 1:
            return jsonify({'message': '设备数量必须大于等于1'}), 400
    except (ValueError, TypeError):
        return jsonify({'message': '设备数量必须是有效的整数'}), 400
    
    # 更新内存中的配置
    CONFIG.setdefault('device', {})
    CONFIG['device']['max_devices_per_user'] = max_devices
    
    # 保存到配置文件
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(CONFIG, f, ensure_ascii=False, indent=2)
        return jsonify({
            'message': f'设备数量限制已更新为 {max_devices}',
            'max_devices_per_user': max_devices
        })
    except Exception as e:
        return jsonify({'message': f'保存配置失败: {str(e)}'}), 500

# ==================== 审计日志 API ====================

@app.route('/api/audit-logs', methods=['GET'])
def get_audit_logs():
    """获取审计日志列表"""
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # 获取筛选参数
    action_type = request.args.get('action_type', '').strip()
    operator = request.args.get('operator', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    
    # 构建查询
    query = AuditLog.query
    
    # 按操作类型筛选
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    
    # 按操作人筛选
    if operator:
        query = query.filter(AuditLog.operator.like(f'%{operator}%'))
    
    # 按时间范围筛选
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            from datetime import timedelta
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AuditLog.created_at < end_dt)
        except ValueError:
            pass
    
    # 按时间倒序排列
    query = query.order_by(AuditLog.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    logs = []
    for log in pagination.items:
        log_data = {
            'id': log.id,
            'action_type': log.action_type,
            'operator': log.operator,
            'ip_address': log.ip_address,
            'details': json.loads(log.details) if log.details else None,
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        logs.append(log_data)
    
    return jsonify({
        'logs': logs,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@app.route('/api/audit-logs/action-types', methods=['GET'])
def get_action_types():
    """获取所有操作类型（用于筛选下拉框）"""
    from sqlalchemy import distinct
    
    action_types = db.session.query(distinct(AuditLog.action_type)).all()
    types = [t[0] for t in action_types if t[0]]
    
    return jsonify({
        'action_types': sorted(types)
    })

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """管理员登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == CONFIG['admin']['username'] and password == CONFIG['admin']['password']:
        # 记录登录成功的审计日志
        log_audit('admin_login', username, {
            'status': 'success',
            'message': '管理员登录成功'
        })
        return jsonify({'success': True, 'message': '登录成功'})
    else:
        # 记录登录失败的审计日志
        log_audit('admin_login_failed', username or 'unknown', {
            'status': 'failed',
            'message': '用户名或密码错误'
        })
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

# ==================== 设备管理 API ====================

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """获取所有设备列表"""
    # 检查并释放过期设备
    check_and_release_expired_devices()
    
    devices = Device.query.all()
    result = []
    for d in devices:
        device_data = {
            'id': d.id,
            'name': d.name,
            'ip': d.ip,
            'username': d.username,
            'password': d.password,
            'status': d.status,
            'current_user': d.current_user,
            'current_user_account': d.current_user_account,
            'occupy_duration': d.occupy_duration,
            'occupy_until': d.occupy_until.strftime('%Y-%m-%d %H:%M:%S') if d.occupy_until else None,
            'ssh_connections': json.loads(d.ssh_connections) if d.ssh_connections else [],
            'serial_connections': json.loads(d.serial_connections) if d.serial_connections else [],
            'tags': json.loads(d.tags) if d.tags else [],
            'created_at': d.created_at.strftime('%Y-%m-%d %H:%M:%S') if d.created_at else None
        }
        
        # 计算剩余时间（分钟）
        if d.occupy_until and d.status == 'occupied':
            remaining = (d.occupy_until - datetime.now()).total_seconds() / 60
            device_data['remaining_minutes'] = max(0, int(remaining))
        else:
            device_data['remaining_minutes'] = 0
            
        result.append(device_data)
    
    return jsonify(result)

@app.route('/api/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """获取单个设备信息"""
    device = Device.query.get_or_404(device_id)
    device_data = {
        'id': device.id,
        'name': device.name,
        'ip': device.ip,
        'username': device.username,
        'password': device.password,
        'status': device.status,
        'current_user': device.current_user,
        'current_user_account': device.current_user_account,
        'occupy_duration': device.occupy_duration,
        'occupy_until': device.occupy_until.strftime('%Y-%m-%d %H:%M:%S') if device.occupy_until else None,
        'ssh_connections': json.loads(device.ssh_connections) if device.ssh_connections else [],
        'serial_connections': json.loads(device.serial_connections) if device.serial_connections else [],
        'tags': json.loads(device.tags) if device.tags else [],
        'created_at': device.created_at.strftime('%Y-%m-%d %H:%M:%S') if device.created_at else None
    }
    
    # 计算剩余时间（分钟）
    if device.occupy_until and device.status == 'occupied':
        remaining = (device.occupy_until - datetime.now()).total_seconds() / 60
        device_data['remaining_minutes'] = max(0, int(remaining))
    else:
        device_data['remaining_minutes'] = 0
        
    return jsonify(device_data)

@app.route('/api/devices', methods=['POST'])
def create_device():
    """创建新设备"""
    data = request.json
    device = Device(
        name=data.get('name'),
        ip=data.get('ip'),
        username=data.get('username'),
        password=data.get('password'),
        ssh_connections=json.dumps(data.get('ssh_connections', [])),
        serial_connections=json.dumps(data.get('serial_connections', [])),
        tags=json.dumps(data.get('tags', [])),
        status='available'
    )
    db.session.add(device)
    db.session.commit()
    
    # 记录审计日志
    log_audit('device_add', 'admin', {
        'device_id': device.id,
        'device_name': device.name,
        'device_ip': device.ip
    })
    
    return jsonify({'message': '设备添加成功', 'id': device.id}), 201

@app.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """更新设备信息"""
    device = Device.query.get_or_404(device_id)
    data = request.json
    
    old_name = device.name
    
    device.name = data.get('name', device.name)
    device.ip = data.get('ip', device.ip)
    device.username = data.get('username', device.username)
    device.password = data.get('password', device.password)
    
    if 'ssh_connections' in data:
        device.ssh_connections = json.dumps(data.get('ssh_connections', []))
    if 'serial_connections' in data:
        device.serial_connections = json.dumps(data.get('serial_connections', []))
    if 'tags' in data:
        device.tags = json.dumps(data.get('tags', []))
    
    db.session.commit()
    
    # 记录审计日志
    log_audit('device_update', 'admin', {
        'device_id': device.id,
        'old_name': old_name,
        'new_name': device.name,
        'device_ip': device.ip
    })
    
    return jsonify({'message': '设备更新成功'})

@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """删除设备"""
    device = Device.query.get_or_404(device_id)
    device_name = device.name
    device_ip = device.ip
    
    # 先删除该设备的所有使用记录
    UsageRecord.query.filter_by(device_id=device_id).delete()
    
    # 再删除设备
    db.session.delete(device)
    db.session.commit()
    
    # 记录审计日志
    log_audit('device_delete', 'admin', {
        'device_id': device_id,
        'device_name': device_name,
        'device_ip': device_ip
    })
    
    return jsonify({'message': '设备删除成功'})

@app.route('/api/devices/batch-delete', methods=['POST'])
def batch_delete_devices():
    """批量删除设备"""
    data = request.json
    device_ids = data.get('device_ids', [])
    
    if not device_ids:
        return jsonify({'message': '没有要删除的设备'}), 400
    
    if not isinstance(device_ids, list):
        return jsonify({'message': '参数格式错误'}), 400
    
    try:
        # 获取要删除的设备名称（用于审计日志）
        devices_to_delete = Device.query.filter(Device.id.in_(device_ids)).all()
        device_names = [d.name for d in devices_to_delete]
        
        # 先删除这些设备的所有使用记录
        UsageRecord.query.filter(UsageRecord.device_id.in_(device_ids)).delete(synchronize_session=False)
        
        # 再批量删除设备
        deleted_count = Device.query.filter(Device.id.in_(device_ids)).delete(synchronize_session=False)
        
        db.session.commit()
        
        # 记录审计日志
        log_audit('device_batch_delete', 'admin', {
            'deleted_count': deleted_count,
            'device_ids': device_ids,
            'device_names': device_names
        })
        
        return jsonify({
            'message': f'成功删除 {deleted_count} 台设备',
            'deleted_count': deleted_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'删除失败: {str(e)}'}), 500

@app.route('/api/devices/batch-import', methods=['POST'])
def batch_import_devices():
    """批量导入设备"""
    data = request.json
    devices_data = data.get('devices', [])
    
    if not devices_data:
        return jsonify({'message': '没有要导入的设备数据'}), 400
    
    success_count = 0
    fail_count = 0
    error_messages = []
    
    for device_data in devices_data:
        try:
            name = device_data.get('name', '').strip()
            
            if not name:
                fail_count += 1
                error_messages.append(f'设备数据不完整（缺少名称）')
                continue
            
            # 检查设备名称是否已存在
            existing = Device.query.filter_by(name=name).first()
            if existing:
                fail_count += 1
                error_messages.append(f'设备 {name} 已存在')
                continue
            
            # 处理连接信息 - 所有连接都存储在ssh_connections中
            connections = device_data.get('connections', [])
            
            # 从connections中提取第一个IP作为主IP（用于旧的ip字段）
            primary_ip = ''
            for conn in connections:
                if not primary_ip and conn.get('ip'):
                    primary_ip = conn.get('ip')
            
            device = Device(
                name=name,
                ip=primary_ip or 'Unknown',  # 使用第一个IP，或默认值
                username=device_data.get('username', ''),
                password=device_data.get('password', ''),
                ssh_connections=json.dumps(connections),  # 所有连接都存在这里
                serial_connections=json.dumps([]),  # 不再使用，保留空数组以兼容
                tags=json.dumps(device_data.get('tags', [])),
                status='available'
            )
            
            db.session.add(device)
            success_count += 1
            
        except Exception as e:
            fail_count += 1
            error_messages.append(f'设备导入失败: {str(e)}')
    
    try:
        db.session.commit()
        
        # 记录审计日志
        log_audit('device_batch_import', 'admin', {
            'imported_count': success_count,
            'failed_count': fail_count,
            'total_count': len(devices_data)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'数据库提交失败: {str(e)}'}), 500
    
    return jsonify({
        'message': '批量导入完成',
        'imported_count': success_count,
        'failed_count': fail_count,
        'errors': error_messages[:10]  # 只返回前10条错误信息
    })

# ==================== 设备占用 API ====================

def get_linux_login_info(device):
    """通过SSH获取Linux登录信息"""
    import paramiko
    import socket
    
    # 如果设备没有配置SSH连接信息，返回提示信息
    if not device.ssh_connections:
        return "该设备未配置SSH连接信息，无法获取登录信息"
    
    try:
        ssh_connections = json.loads(device.ssh_connections)
        if not ssh_connections:
            return "该设备未配置SSH连接信息，无法获取登录信息"
        
        # 使用第一个SSH连接配置
        ssh_conn = ssh_connections[0]
        host = ssh_conn.get('ip')
        port = int(ssh_conn.get('port', 22))
        username = device.username
        password = device.password
        
        if not all([host, username, password]):
            return f"SSH连接配置不完整 (host={host}, port={port}, username={'已配置' if username else '未配置'}, password={'已配置' if password else '未配置'})"
        
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"[DEBUG] 尝试SSH连接: {username}@{host}:{port}")
        
        # 连接超时设置为5秒
        ssh.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=5,
            banner_timeout=5,
            auth_timeout=5
        )
        
        print(f"[DEBUG] SSH连接成功，开始获取登录信息")
        
        # 1. 执行who命令获取当前登录用户
        stdin, stdout, stderr = ssh.exec_command('who')
        who_output = stdout.read().decode('utf-8', errors='ignore').strip()
        
        # 2. 执行w命令获取详细信息
        stdin, stdout, stderr = ssh.exec_command('w')
        w_output = stdout.read().decode('utf-8', errors='ignore').strip()
        
        # 3. 执行last -n 30命令获取最近30次登录历史（包含IP地址）
        stdin, stdout, stderr = ssh.exec_command('last -n 30 -a')
        last_output = stdout.read().decode('utf-8', errors='ignore').strip()
        
        # 4. 执行lastlog命令获取所有用户的最后登录信息
        stdin, stdout, stderr = ssh.exec_command('lastlog | head -n 50')
        lastlog_output = stdout.read().decode('utf-8', errors='ignore').strip()
        
        # 5. 执行who -a命令获取更详细的当前登录信息
        stdin, stdout, stderr = ssh.exec_command('who -a')
        who_a_output = stdout.read().decode('utf-8', errors='ignore').strip()
        
        # 关闭连接
        ssh.close()
        
        print(f"[DEBUG] 成功执行所有命令，组合结果")
        
        # 组合信息
        login_info_parts = []
        
        if who_output:
            login_info_parts.append(f"=== 当前登录用户 (who) ===\n{who_output}")
        
        if who_a_output:
            login_info_parts.append(f"\n=== 详细当前登录 (who -a) ===\n{who_a_output}")
        
        if w_output:
            login_info_parts.append(f"\n=== 用户活动信息 (w) ===\n{w_output}")
        
        if last_output:
            login_info_parts.append(f"\n=== 最近30次登录历史 (last -n 30 -a) ===\n{last_output}")
        
        if lastlog_output:
            login_info_parts.append(f"\n=== 用户最后登录信息 (lastlog) ===\n{lastlog_output}")
        
        login_info = '\n'.join(login_info_parts) if login_info_parts else "未获取到登录信息（所有命令输出为空）"
        print(f"[DEBUG] 登录信息长度: {len(login_info)} 字符")
        return login_info
        
    except paramiko.AuthenticationException as e:
        error_msg = f"SSH认证失败 (用户名或密码错误): {str(e)}"
        print(f"[ERROR] {error_msg}")
        return error_msg
    except socket.timeout as e:
        error_msg = f"SSH连接超时 (无法连接到 {host}:{port}): {str(e)}"
        print(f"[ERROR] {error_msg}")
        return error_msg
    except (paramiko.SSHException, socket.error) as e:
        error_msg = f"SSH连接失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"获取登录信息时发生错误: {type(e).__name__}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return error_msg

@app.route('/api/devices/<int:device_id>/occupy', methods=['POST'])
def occupy_device(device_id):
    """占用设备"""
    from datetime import timedelta
    
    device = Device.query.get_or_404(device_id)
    
    if device.status == 'occupied':
        return jsonify({'message': '设备已被占用'}), 400
    
    data = request.json
    user_account = data.get('user_account')  # 用户账号
    purpose = data.get('purpose')
    duration = data.get('duration', 2)  # 默认2小时
    
    # 检查用户账号是否在授权列表中
    allowed_user = AllowedUser.query.filter_by(account=user_account).first()
    if not allowed_user:
        return jsonify({'message': f'账号 "{user_account}" 未授权，请联系管理员添加该账号到授权列表'}), 403
    
    # 使用中文名作为显示名称
    user_name = allowed_user.chinese_name
    
    # 检查用户当前占用的设备数量
    max_devices = CONFIG.get('device', {}).get('max_devices_per_user', 1)
    current_occupied = Device.query.filter_by(
        current_user_account=user_account,
        status='occupied'
    ).count()
    
    if current_occupied >= max_devices:
        return jsonify({
            'message': f'您已占用 {current_occupied} 台设备，达到最大限制 {max_devices} 台。请先释放其他设备后再占用。',
            'current_occupied': current_occupied,
            'max_devices': max_devices
        }), 403
    
    # 限制时长范围：1-48小时
    duration = max(1, min(48, int(duration)))
    
    # 获取Linux登录信息
    login_info = get_linux_login_info(device)
    
    # 记录日志以便调试
    print(f"[DEBUG] 占用设备 {device.name} (ID: {device_id})")
    print(f"[DEBUG] SSH配置: {device.ssh_connections[:100] if device.ssh_connections else 'None'}...")
    print(f"[DEBUG] 登录信息获取结果: {login_info[:200] if login_info else 'None'}...")
    
    # 更新设备状态
    device.status = 'occupied'
    device.current_user = user_name
    device.current_user_account = user_account
    device.occupy_duration = duration
    device.occupy_until = datetime.now() + timedelta(hours=duration)
    
    # 创建使用记录
    record = UsageRecord(
        device_id=device_id,
        user_name=user_name,
        user_account=user_account,
        purpose=purpose,
        start_time=datetime.now(),
        login_info=login_info
    )
    
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'message': '设备占用成功',
        'record_id': record.id,
        'occupy_until': device.occupy_until.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/devices/<int:device_id>/release', methods=['POST'])
def release_device(device_id):
    """释放设备"""
    device = Device.query.get_or_404(device_id)
    
    if device.status != 'occupied':
        return jsonify({'message': '设备未被占用'}), 400
    
    # 更新设备状态
    device.status = 'available'
    device.current_user = None
    device.current_user_account = None
    device.occupy_duration = 2
    device.occupy_until = None
    
    # 更新最后一条使用记录
    record = UsageRecord.query.filter_by(
        device_id=device_id,
        end_time=None
    ).order_by(UsageRecord.start_time.desc()).first()
    
    if record:
        record.end_time = datetime.now()
    
    db.session.commit()
    
    return jsonify({'message': '设备释放成功'})

# ==================== 使用记录 API ====================

@app.route('/api/records', methods=['GET'])
def get_records():
    """获取所有使用记录"""
    records = UsageRecord.query.order_by(UsageRecord.start_time.desc()).all()
    return jsonify([{
        'id': r.id,
        'device_id': r.device_id,
        'device_name': r.device.name if r.device else None,
        'user_name': r.user_name,
        'user_account': r.user_account,
        'purpose': r.purpose,
        'start_time': r.start_time.strftime('%Y-%m-%d %H:%M:%S') if r.start_time else None,
        'end_time': r.end_time.strftime('%Y-%m-%d %H:%M:%S') if r.end_time else None,
        'duration': r.get_duration(),
        'login_info': r.login_info
    } for r in records])

@app.route('/api/records/<int:device_id>', methods=['GET'])
def get_device_records(device_id):
    """获取指定设备的使用记录"""
    records = UsageRecord.query.filter_by(device_id=device_id).order_by(UsageRecord.start_time.desc()).all()
    return jsonify([{
        'id': r.id,
        'device_id': r.device_id,
        'device_name': r.device.name if r.device else None,
        'user_name': r.user_name,
        'user_account': r.user_account,
        'purpose': r.purpose,
        'start_time': r.start_time.strftime('%Y-%m-%d %H:%M:%S') if r.start_time else None,
        'end_time': r.end_time.strftime('%Y-%m-%d %H:%M:%S') if r.end_time else None,
        'duration': r.get_duration(),
        'login_info': r.login_info
    } for r in records])

# ==================== 报表统计 API ====================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取统计数据"""
    total_devices = Device.query.count()
    available_devices = Device.query.filter_by(status='available').count()
    occupied_devices = Device.query.filter_by(status='occupied').count()
    total_records = UsageRecord.query.count()
    
    # 获取设备使用排行
    device_usage = db.session.query(
        Device.name,
        db.func.count(UsageRecord.id).label('usage_count')
    ).join(UsageRecord).group_by(Device.id).order_by(db.desc('usage_count')).limit(10).all()
    
    # 获取使用人时长排行（统计所有记录，但只计算已结束记录的时长）
    # 获取所有记录
    all_records = UsageRecord.query.filter(
        UsageRecord.user_name.isnot(None)
    ).all()
    
    # 计算每个用户的总时长和使用次数
    user_stats = {}
    for record in all_records:
        if record.user_name not in user_stats:
            user_stats[record.user_name] = {'total_hours': 0, 'usage_count': 0}
        
        # 所有记录都算入使用次数
        user_stats[record.user_name]['usage_count'] += 1
        
        # 只有已结束的记录才计算时长
        if record.end_time:
            duration = record.get_duration()
            if duration:
                user_stats[record.user_name]['total_hours'] += duration
    
    # 排序并取前10
    user_duration_list = [
        {'user_name': name, 'total_hours': round(stats['total_hours'], 2), 'usage_count': stats['usage_count']}
        for name, stats in user_stats.items()
    ]
    user_duration_list.sort(key=lambda x: x['total_hours'], reverse=True)
    user_duration_ranking = user_duration_list[:10]
    
    return jsonify({
        'total_devices': total_devices,
        'available_devices': available_devices,
        'occupied_devices': occupied_devices,
        'total_records': total_records,
        'device_usage_ranking': [{'device_name': d[0], 'usage_count': d[1]} for d in device_usage],
        'user_duration_ranking': user_duration_ranking
    })

# ==================== 用户管理 API ====================

@app.route('/api/users', methods=['GET'])
def get_allowed_users():
    """获取授权用户列表"""
    users = AllowedUser.query.order_by(AllowedUser.created_at.desc()).all()
    return jsonify([{
        'id': u.id,
        'account': u.account,
        'chinese_name': u.chinese_name,
        'department': u.department,
        'password': u.password,  # 添加密码字段
        'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for u in users])

@app.route('/api/users', methods=['POST'])
def add_allowed_user():
    """添加授权用户"""
    data = request.json
    account = data.get('account', '').strip()
    chinese_name = data.get('chinese_name', '').strip()
    department = data.get('department', '').strip() or '未填写'
    password = data.get('password', '').strip() or '123456'  # 支持自定义密码，默认123456
    
    if not account:
        return jsonify({'message': '账号不能为空'}), 400
    if not chinese_name:
        return jsonify({'message': '中文名不能为空'}), 400
    
    # 检查账号是否已存在
    existing = AllowedUser.query.filter_by(account=account).first()
    if existing:
        return jsonify({'message': f'账号 "{account}" 已存在'}), 400
    
    user = AllowedUser(
        account=account,
        chinese_name=chinese_name,
        department=department,
        password=password  # 使用提供的密码或默认密码
    )
    db.session.add(user)
    db.session.commit()
    
    # 记录审计日志
    log_audit('user_add', 'admin', {
        'user_id': user.id,
        'account': account,
        'chinese_name': chinese_name,
        'department': department
    })
    
    return jsonify({
        'message': '用户添加成功',
        'id': user.id,
        'account': user.account,
        'chinese_name': user.chinese_name,
        'department': user.department
    }), 201

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_allowed_user(user_id):
    """删除授权用户"""
    user = AllowedUser.query.get_or_404(user_id)
    user_account = user.account
    user_name = user.chinese_name
    
    db.session.delete(user)
    db.session.commit()
    
    # 记录审计日志
    log_audit('user_delete', 'admin', {
        'user_id': user_id,
        'account': user_account,
        'chinese_name': user_name
    })
    
    return jsonify({'message': '用户删除成功'})

@app.route('/api/users/login', methods=['POST'])
def user_login():
    """普通用户登录"""
    data = request.json
    account = data.get('account', '').strip()
    password = data.get('password', '').strip()
    
    if not account or not password:
        return jsonify({'message': '账号和密码不能为空'}), 400
    
    # 查找用户
    user = AllowedUser.query.filter_by(account=account).first()
    if not user:
        # 记录登录失败
        log_audit('user_login_failed', account, {
            'status': 'failed',
            'reason': '账号不存在'
        })
        return jsonify({'message': '账号不存在'}), 401
    
    # 验证密码
    if user.password != password:
        # 记录登录失败
        log_audit('user_login_failed', account, {
            'status': 'failed',
            'reason': '密码错误'
        })
        return jsonify({'message': '密码错误'}), 401
    
    # 记录登录成功
    log_audit('user_login', account, {
        'status': 'success',
        'chinese_name': user.chinese_name,
        'department': user.department
    })
    
    return jsonify({
        'message': '登录成功',
        'user': {
            'username': user.account,
            'chinese_name': user.chinese_name,
            'department': user.department,
            'is_admin': False
        }
    })

@app.route('/api/users/change-password', methods=['POST'])
def change_password():
    """修改用户密码"""
    data = request.json
    account = data.get('account', '').strip()
    old_password = data.get('old_password', '').strip()
    new_password = data.get('new_password', '').strip()
    
    if not account or not old_password or not new_password:
        return jsonify({'message': '参数不完整'}), 400
    
    if len(new_password) < 6:
        return jsonify({'message': '新密码长度不能少于6位'}), 400
    
    # 查找用户
    user = AllowedUser.query.filter_by(account=account).first()
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 验证旧密码
    if user.password != old_password:
        return jsonify({'message': '原密码错误'}), 401
    
    # 更新密码
    user.password = new_password
    db.session.commit()
    
    return jsonify({'message': '密码修改成功'})

@app.route('/api/users/batch-delete', methods=['POST'])
def batch_delete_users():
    """批量删除授权用户"""
    data = request.json
    user_ids = data.get('user_ids', [])
    
    if not user_ids:
        return jsonify({'message': '没有选择要删除的用户'}), 400
    
    try:
        # 获取要删除的用户信息（用于审计日志）
        users_to_delete = AllowedUser.query.filter(AllowedUser.id.in_(user_ids)).all()
        user_accounts = [u.account for u in users_to_delete]
        
        deleted_count = AllowedUser.query.filter(AllowedUser.id.in_(user_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        # 记录审计日志
        log_audit('user_batch_delete', 'admin', {
            'deleted_count': deleted_count,
            'user_ids': user_ids,
            'accounts': user_accounts
        })
        
        return jsonify({
            'message': '批量删除成功',
            'deleted_count': deleted_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'批量删除失败: {str(e)}'}), 500

@app.route('/api/users/batch-import', methods=['POST'])
def batch_import_users():
    """批量导入授权用户"""
    data = request.json
    users_data = data.get('users', [])
    
    if not users_data:
        return jsonify({'message': '没有要导入的用户数据'}), 400
    
    success_count = 0
    fail_count = 0
    error_messages = []
    
    for user_data in users_data:
        try:
            account = user_data.get('account', '').strip()
            chinese_name = user_data.get('chinese_name', '').strip()
            department = user_data.get('department', '').strip() or '未填写'
            password = user_data.get('password', '').strip() or '123456'  # 如果没有提供密码，使用默认密码
            
            if not account or not chinese_name:
                fail_count += 1
                error_messages.append(f'账号 {account} 数据不完整')
                continue
            
            # 检查账号是否已存在
            existing = AllowedUser.query.filter_by(account=account).first()
            if existing:
                fail_count += 1
                error_messages.append(f'账号 {account} 已存在')
                continue
            
            user = AllowedUser(
                account=account,
                chinese_name=chinese_name,
                department=department,
                password=password  # 使用提供的密码或默认密码
            )
            db.session.add(user)
            success_count += 1
            
        except Exception as e:
            fail_count += 1
            error_messages.append(f'导入失败: {str(e)}')
    
    try:
        db.session.commit()
        
        # 记录审计日志
        log_audit('user_batch_import', 'admin', {
            'success_count': success_count,
            'fail_count': fail_count,
            'total_count': len(users_data)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'数据库提交失败: {str(e)}'}), 500
    
    return jsonify({
        'message': '批量导入完成',
        'success_count': success_count,
        'fail_count': fail_count,
        'errors': error_messages[:10]  # 只返回前10条错误信息
    })

# ==================== 快捷命令管理 ====================

@app.route('/api/quick-commands', methods=['GET'])
def get_quick_commands():
    """获取所有启用的快捷命令（所有用户可访问）"""
    try:
        commands = QuickCommand.query.filter_by(enabled=True).order_by(QuickCommand.order, QuickCommand.id).all()
        return jsonify({
            'commands': [cmd.to_dict() for cmd in commands]
        })
    except Exception as e:
        return jsonify({'message': f'获取快捷命令失败: {str(e)}'}), 500

@app.route('/api/quick-commands/all', methods=['GET'])
def get_all_quick_commands():
    """获取所有快捷命令（包括未启用的，仅管理员）"""
    # 验证token（简化版本）
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    try:
        commands = QuickCommand.query.order_by(QuickCommand.order, QuickCommand.id).all()
        return jsonify({
            'commands': [cmd.to_dict() for cmd in commands]
        })
    except Exception as e:
        return jsonify({'message': f'获取快捷命令失败: {str(e)}'}), 500

@app.route('/api/quick-commands', methods=['POST'])
def create_quick_command():
    """创建快捷命令（仅管理员）"""
    # 验证token（简化版本）
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    try:
        data = request.json
        
        # 检查是否已经有10个命令
        count = QuickCommand.query.count()
        if count >= 10:
            return jsonify({'message': '最多只能创建10个快捷命令'}), 400
        
        # 验证必填字段
        if not data.get('name') or not data.get('command'):
            return jsonify({'message': '名称和命令不能为空'}), 400
        
        command = QuickCommand(
            name=data.get('name'),
            command=data.get('command'),
            description=data.get('description', ''),
            order=data.get('order', count),
            enabled=data.get('enabled', True)
        )
        
        db.session.add(command)
        db.session.commit()
        
        return jsonify({
            'message': '快捷命令创建成功',
            'command': command.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'创建快捷命令失败: {str(e)}'}), 500

@app.route('/api/quick-commands/<int:command_id>', methods=['PUT'])
def update_quick_command(command_id):
    """更新快捷命令（仅管理员）"""
    # 验证token（简化版本）
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    try:
        command = QuickCommand.query.get_or_404(command_id)
        data = request.json
        
        # 验证必填字段
        if not data.get('name') or not data.get('command'):
            return jsonify({'message': '名称和命令不能为空'}), 400
        
        command.name = data.get('name')
        command.command = data.get('command')
        command.description = data.get('description', '')
        command.order = data.get('order', command.order)
        command.enabled = data.get('enabled', True)
        command.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'message': '快捷命令更新成功',
            'command': command.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'更新快捷命令失败: {str(e)}'}), 500

@app.route('/api/quick-commands/<int:command_id>', methods=['DELETE'])
def delete_quick_command(command_id):
    """删除快捷命令（仅管理员）"""
    # 验证token（简化版本）
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'message': '未授权'}), 401
    
    try:
        command = QuickCommand.query.get_or_404(command_id)
        db.session.delete(command)
        db.session.commit()
        
        return jsonify({'message': '快捷命令删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'删除快捷命令失败: {str(e)}'}), 500

# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok'})

# ==================== WebSocket事件处理 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('Client connected')
    emit('connected', {'status': 'ok'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print('Client disconnected')

@socketio.on('ssh_connect')
def handle_ssh_connect(data):
    """建立SSH连接"""
    session_id = data.get('session_id')
    host = data.get('host')
    port = data.get('port', 22)
    username = data.get('username')
    password = data.get('password')
    
    print(f"SSH连接请求: {username}@{host}:{port}")
    
    success, message = terminal_manager.create_ssh_connection(session_id, host, port, username, password)
    if success:
        emit('terminal_connected', {'session_id': session_id, 'type': 'ssh', 'message': message})
    else:
        emit('terminal_error', {'session_id': session_id, 'error': message})

@socketio.on('telnet_connect')
def handle_telnet_connect(data):
    """建立Telnet连接"""
    session_id = data.get('session_id')
    host = data.get('host')
    port = data.get('port', 23)
    
    print(f"Telnet连接请求: {host}:{port}")
    
    success, message = terminal_manager.create_telnet_connection(session_id, host, port)
    if success:
        emit('terminal_connected', {'session_id': session_id, 'type': 'telnet', 'message': message})
    else:
        emit('terminal_error', {'session_id': session_id, 'error': message})

@socketio.on('terminal_input')
def handle_terminal_input(data):
    """处理终端输入"""
    session_id = data.get('session_id')
    input_data = data.get('data')
    
    terminal_manager.send_data(session_id, input_data)

@socketio.on('close_terminal')
def handle_close_terminal(data):
    """关闭终端连接"""
    session_id = data.get('session_id')
    terminal_manager.close_connection(session_id)
    emit('terminal_closed', {'session_id': session_id})

@socketio.on('resize_terminal')
def handle_resize_terminal(data):
    """处理终端大小调整"""
    session_id = data.get('session_id')
    cols = data.get('cols', 80)
    rows = data.get('rows', 24)
    
    # 调用终端管理器的 resize 方法
    if terminal_manager and hasattr(terminal_manager, 'resize_terminal'):
        terminal_manager.resize_terminal(session_id, cols, rows)

@socketio.on('upload_file')
def handle_upload_file(data):
    """处理文件上传到远程服务器"""
    import base64
    
    session_id = data.get('session_id')
    filename = data.get('filename')
    filedata = data.get('filedata')
    filesize = data.get('filesize', 0)
    
    if not all([session_id, filename, filedata]):
        emit('terminal_output', {
            'session_id': session_id,
            'data': '\r\n❌ 错误: 文件上传参数不完整\r\n'
        })
        return
    
    try:
        # 解析base64数据
        if ',' in filedata:
            filedata = filedata.split(',')[1]
        
        file_bytes = base64.b64decode(filedata)
        
        # 获取SSH连接
        conn = terminal_manager.connections.get(session_id)
        if not conn:
            emit('terminal_output', {
                'session_id': session_id,
                'data': '\r\n❌ 错误: 终端连接不存在\r\n'
            })
            return
        
        # 检查是否是SSH连接（只有SSH支持SFTP）
        if not hasattr(conn, 'client') or not hasattr(conn, 'channel'):
            emit('terminal_output', {
                'session_id': session_id,
                'data': '\r\n❌ 错误: 仅SSH连接支持文件上传\r\n'
            })
            return
        
        if not conn.client or not conn.connected:
            emit('terminal_output', {
                'session_id': session_id,
                'data': '\r\n❌ 错误: SSH连接未建立\r\n'
            })
            return
        
        # 使用SFTP上传文件
        sftp = conn.client.open_sftp()
        remote_path = f'/tmp/{filename}'
        
        # 写入文件
        with sftp.file(remote_path, 'wb') as remote_file:
            remote_file.write(file_bytes)
        
        sftp.close()
        
        emit('terminal_output', {
            'session_id': session_id,
            'data': f'\r\n✅ 文件上传成功: {remote_path} ({filesize} bytes)\r\n'
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"文件上传失败: {error_details}")
        emit('terminal_output', {
            'session_id': session_id,
            'data': f'\r\n❌ 上传失败: {str(e)}\r\n'
        })

if __name__ == '__main__':
    try:
        # 启动后台任务
        start_background_tasks()
        
        # 从配置文件读取服务器配置
        server_config = CONFIG['server']
        print(f"\n{'='*50}")
        print(f"🚀 启动设备管理系统")
        print(f"{'='*50}")
        print(f"📍 主机: {server_config['host']}")
        print(f"📍 端口: {server_config['port']}")
        print(f"👤 管理员: {CONFIG['admin']['username']}")
        print(f"{'='*50}\n")
        
        socketio.run(
            app, 
            debug=server_config['debug'], 
            host=server_config['host'], 
            port=server_config['port'], 
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        import traceback
        print(f"\n{'='*50}")
        print(f"❌ 启动失败")
        print(f"{'='*50}")
        print(f"错误信息: {e}")
        print(f"\n详细错误:")
        traceback.print_exc()
        print(f"{'='*50}\n")
        sys.exit(1)
