"""
Web终端模块 - 支持SSH和Telnet连接
"""
import paramiko
import socket
import threading
import time
from flask_socketio import emit

class SSHConnection:
    """SSH连接管理"""
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.channel = None
        self.connected = False
        
    def connect(self):
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            # 创建伪终端，设置终端类型和大小
            self.channel = self.client.invoke_shell(
                term='xterm',  # 设置终端类型为xterm
                width=80,      # 终端宽度
                height=24      # 终端高度
            )
            self.channel.settimeout(0.1)
            self.connected = True
            return True, "连接成功"
        except paramiko.AuthenticationException:
            error_msg = f"SSH认证失败: 用户名或密码错误"
            print(error_msg)
            return False, error_msg
        except paramiko.SSHException as e:
            error_msg = f"SSH连接错误: {str(e)}"
            print(error_msg)
            return False, error_msg
        except socket.timeout:
            error_msg = f"SSH连接超时: 无法连接到 {self.host}:{self.port}"
            print(error_msg)
            return False, error_msg
        except socket.error as e:
            error_msg = f"网络错误: {str(e)}"
            print(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"SSH连接失败: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def send(self, data):
        """发送数据"""
        if self.channel and self.connected:
            try:
                self.channel.send(data)
                return True
            except Exception as e:
                print(f"发送数据失败: {e}")
                self.connected = False
                return False
        return False
    
    def receive(self):
        """接收数据"""
        if self.channel and self.connected:
            try:
                if self.channel.recv_ready():
                    return self.channel.recv(1024).decode('utf-8', errors='ignore')
            except Exception as e:
                if 'timed out' not in str(e):
                    print(f"接收数据失败: {e}")
                    self.connected = False
        return None
    
    def close(self):
        """关闭连接"""
        self.connected = False
        if self.channel:
            try:
                self.channel.close()
            except:
                pass
        if self.client:
            try:
                self.client.close()
            except:
                pass


class TelnetConnection:
    """Telnet连接管理（使用原始socket）"""
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client = None
        self.connected = False
        
    def connect(self):
        """建立Telnet连接"""
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(10)
            self.client.connect((self.host, self.port))
            self.client.setblocking(False)  # 非阻塞模式
            self.connected = True
            return True, "连接成功"
        except socket.timeout:
            error_msg = f"Telnet连接超时: 无法连接到 {self.host}:{self.port}"
            print(error_msg)
            return False, error_msg
        except ConnectionRefusedError:
            error_msg = f"连接被拒绝: {self.host}:{self.port} (Telnet服务可能未启动)"
            print(error_msg)
            return False, error_msg
        except socket.gaierror:
            error_msg = f"主机名解析失败: {self.host}"
            print(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Telnet连接失败: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def send(self, data):
        """发送数据"""
        if self.client and self.connected:
            try:
                self.client.sendall(data.encode('utf-8'))
                return True
            except Exception as e:
                print(f"发送数据失败: {e}")
                self.connected = False
                return False
        return False
    
    def receive(self):
        """接收数据"""
        if self.client and self.connected:
            try:
                data = self.client.recv(4096)
                if data:
                    return data.decode('utf-8', errors='ignore')
            except BlockingIOError:
                # 非阻塞模式下没有数据
                return None
            except Exception as e:
                if 'timed out' not in str(e):
                    print(f"接收数据失败: {e}")
                    self.connected = False
        return None
    
    def close(self):
        """关闭连接"""
        self.connected = False
        if self.client:
            try:
                self.client.close()
            except:
                pass


class TerminalManager:
    """终端管理器"""
    def __init__(self, socketio):
        self.socketio = socketio
        self.connections = {}  # session_id -> connection
        self.read_threads = {}  # session_id -> thread
        
    def create_ssh_connection(self, session_id, host, port, username, password):
        """创建SSH连接"""
        # 关闭已存在的连接
        self.close_connection(session_id)
        
        # 创建新连接
        conn = SSHConnection(host, port, username, password)
        success, message = conn.connect()
        if success:
            self.connections[session_id] = conn
            # 启动读取线程
            thread = threading.Thread(
                target=self._read_loop,
                args=(session_id,),
                daemon=True
            )
            thread.start()
            self.read_threads[session_id] = thread
            return True, message
        return False, message
    
    def create_telnet_connection(self, session_id, host, port):
        """创建Telnet连接"""
        # 关闭已存在的连接
        self.close_connection(session_id)
        
        # 创建新连接
        conn = TelnetConnection(host, port)
        success, message = conn.connect()
        if success:
            self.connections[session_id] = conn
            # 启动读取线程
            thread = threading.Thread(
                target=self._read_loop,
                args=(session_id,),
                daemon=True
            )
            thread.start()
            self.read_threads[session_id] = thread
            return True, message
        return False, message
    
    def send_data(self, session_id, data):
        """发送数据"""
        conn = self.connections.get(session_id)
        if conn:
            return conn.send(data)
        return False
    
    def resize_terminal(self, session_id, cols, rows):
        """调整终端大小"""
        conn = self.connections.get(session_id)
        if conn and isinstance(conn, SSHConnection) and conn.channel:
            try:
                # 只有 SSH 连接支持调整终端大小
                conn.channel.resize_pty(width=cols, height=rows)
                print(f"终端大小已调整: {session_id} -> {cols}x{rows}")
                return True
            except Exception as e:
                print(f"调整终端大小失败: {e}")
                return False
        return False
    
    def close_connection(self, session_id):
        """关闭连接"""
        conn = self.connections.get(session_id)
        if conn:
            conn.close()
            del self.connections[session_id]
        
        if session_id in self.read_threads:
            # 线程会自动结束，因为连接已关闭
            del self.read_threads[session_id]
    
    def _read_loop(self, session_id):
        """读取循环"""
        conn = self.connections.get(session_id)
        if not conn:
            return
        
        while conn.connected:
            data = conn.receive()
            if data:
                # 通过SocketIO发送数据到客户端
                self.socketio.emit('terminal_output', {
                    'session_id': session_id,
                    'data': data
                })
            time.sleep(0.01)  # 避免CPU占用过高
        
        # 连接断开，通知客户端
        self.socketio.emit('terminal_disconnected', {
            'session_id': session_id
        })
