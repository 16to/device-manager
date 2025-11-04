# 配置文件说明

## 配置文件位置
`config.json` - 位于项目根目录

## 配置项说明

### server - 服务器配置
```json
{
  "host": "0.0.0.0",      // 监听地址，0.0.0.0表示监听所有网卡
  "port": 3000,           // 服务端口号，建议3000-9999之间
  "debug": true           // 调试模式，生产环境建议设为false
}
```

### admin - 管理员账号配置
```json
{
  "username": "admin",    // 管理员用户名
  "password": "admin123"  // 管理员密码
}
```

### database - 数据库配置
```json
{
  "path": "backend/device_manager.db"  // 数据库文件路径（相对于项目根目录）
}
```

### user - 用户配置
```json
{
  "default_password": "123456"  // 新增用户的默认密码
}
```

### socketio - WebSocket配置
```json
{
  "ping_timeout": 120,              // ping超时时间（秒）
  "ping_interval": 25,              // ping间隔时间（秒）
  "max_http_buffer_size": 1073741824  // 最大HTTP缓冲区大小（字节，1GB）
}
```

## 修改配置

1. **修改服务端口**
   编辑 `config.json`，将 `server.port` 改为想要的端口号
   ```json
   "server": {
     "port": 8080
   }
   ```

2. **修改管理员账号**
   编辑 `config.json`，修改 `admin` 配置
   ```json
   "admin": {
     "username": "superadmin",
     "password": "NewSecurePassword@2025"
   }
   ```

3. **修改用户默认密码**
   编辑 `config.json`，修改 `user.default_password`
   ```json
   "user": {
     "default_password": "Welcome123"
   }
   ```

## 注意事项

1. **修改配置后需要重启服务才能生效**
   ```bash
   ./stop.sh
   ./start.sh
   ```

2. **管理员密码安全**
   - 生产环境请务必修改默认管理员密码
   - 建议使用强密码（包含大小写字母、数字、特殊字符）
   - 定期更换密码

3. **端口占用**
   - 确保选择的端口未被其他程序占用
   - macOS系统请避免使用5000端口（AirPlay占用）
   - Linux系统1024以下端口需要root权限

4. **配置文件权限**
   - 建议设置适当的文件权限保护配置文件
   ```bash
   chmod 600 config.json
   ```

5. **备份配置**
   - 修改配置前建议先备份原配置文件
   ```bash
   cp config.json config.json.backup
   ```

## 默认配置

如果配置文件不存在或读取失败，系统将使用以下默认配置：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 3000,
    "debug": true
  },
  "admin": {
    "username": "admin",
    "password": "admin123"
  },
  "database": {
    "path": "backend/device_manager.db"
  },
  "user": {
    "default_password": "123456"
  },
  "socketio": {
    "ping_timeout": 120,
    "ping_interval": 25,
    "max_http_buffer_size": 1073741824
  }
}
```

## 生产环境建议配置

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false
  },
  "admin": {
    "username": "administrator",
    "password": "YourStrongPassword@2025"
  },
  "database": {
    "path": "backend/device_manager.db"
  },
  "user": {
    "default_password": "Welcome@123"
  },
  "socketio": {
    "ping_timeout": 120,
    "ping_interval": 25,
    "max_http_buffer_size": 1073741824
  }
}
```
