# 登录信息功能故障排除

## 问题：重新部署后，登录信息功能不可用

### 症状
- 在使用记录中看不到"查看登录信息"按钮
- 或者点击按钮后显示空白或错误

### 可能原因
1. **使用了旧版本的数据库备份**：恢复的数据库缺少 `login_info` 字段
2. **部署时跳过了数据库初始化**：没有创建完整的表结构

### 解决方案

#### 方法1：智能数据库迁移（推荐）⭐
```bash
cd /path/to/device-manager
python3 migrate_db.py
```

该脚本会：
- ✅ 自动检测所有表的结构差异
- ✅ 自动添加缺失的表和字段（包括 `login_info`）
- ✅ 完全保留所有现有数据
- ✅ 提供详细的迁移报告

#### 方法2：快速检查修复
```bash
cd /path/to/device-manager
python3 check_and_fix_db.py
```

#### 方法3：手动添加字段（已废弃）
```bash
cd /path/to/device-manager
python3 update_db_add_login_info.py
```
注意：此方法只能添加 `login_info` 字段，不推荐使用

#### 方法3：完全重新初始化（会删除所有数据）
```bash
cd /path/to/device-manager
# 备份现有数据（如果需要）
cp backend/device_manager.db ~/backup/device_manager_backup.db
# 重新初始化
python3 init_db.py
```

### 验证修复
1. **检查数据库结构**
```bash
sqlite3 backend/device_manager.db "PRAGMA table_info(usage_records);"
```
应该看到包含 `login_info` 字段的输出

2. **重启应用**
```bash
# 如果使用 systemd
sudo systemctl restart device-manager

# 或者手动重启
./stop.sh
./start.sh
```

3. **测试功能**
- 登录系统
- 占用一个设备（确保设备有SSH配置）
- 进入"使用记录"页面
- 查看是否有"🖥️ 查看"按钮

### 预防措施

#### 部署新系统时
1. **使用自动部署脚本**
```bash
sudo ./deploy.sh
```
部署时会提示是否运行数据库升级脚本

2. **恢复旧数据库后**
```bash
# 恢复数据库
cp ~/backup/old_database.db backend/device_manager.db
# 运行升级脚本
python3 check_and_fix_db.py
# 重启服务
sudo systemctl restart device-manager
```

#### 数据库备份最佳实践
```bash
# 定期备份
cp backend/device_manager.db ~/backup/device_manager_$(date +%Y%m%d_%H%M%S).db

# 或使用自动备份脚本
0 2 * * * cd /opt/device-manager && cp backend/device_manager.db ~/backup/device_manager_$(date +\%Y\%m\%d).db
```

### 常见问题

**Q: 运行升级脚本会删除数据吗？**
A: 不会。升级脚本只是添加新字段，不会删除或修改现有数据。

**Q: 可以多次运行升级脚本吗？**
A: 可以。脚本会先检查字段是否存在，如果已存在则跳过，不会重复添加。

**Q: 如何确认登录信息功能正常？**
A: 占用一个有SSH配置的设备后，在使用记录中应该能看到"🖥️ 查看"按钮，点击后可以看到Linux登录信息。

**Q: 为什么有些记录没有登录信息？**
A: 可能原因：
- 设备没有配置SSH连接
- SSH连接失败（密码错误、网络问题等）
- 设备不是Linux系统或不支持相关命令

## 技术细节

### 数据库表结构
`usage_records` 表应该包含以下字段：
```
id              INTEGER (主键)
device_id       INTEGER (外键)
user_name       VARCHAR(100)
user_account    VARCHAR(100)
purpose         TEXT
start_time      DATETIME
end_time        DATETIME
login_info      TEXT         ← 登录信息字段
```

### 升级SQL
```sql
ALTER TABLE usage_records ADD COLUMN login_info TEXT;
```

### 相关文件
- `backend/models.py` - 数据库模型定义
- `init_db.py` - 数据库初始化脚本
- `update_db_add_login_info.py` - 登录信息字段升级脚本
- `check_and_fix_db.py` - 数据库检查和修复脚本
- `LOGIN_INFO_FEATURE.md` - 登录信息功能文档

## 获取帮助
如果以上方法都无法解决问题，请：
1. 运行 `python3 check_and_fix_db.py` 并保存输出
2. 检查应用日志 `sudo journalctl -u device-manager -n 100`
3. 联系系统管理员
