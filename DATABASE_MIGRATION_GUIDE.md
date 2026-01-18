# 数据库升级指南

## 问题：部署后登录信息功能不可用

### 快速解决方案

运行智能数据库迁移脚本：

```bash
cd /path/to/device-manager
python3 migrate_db.py
sudo systemctl restart device-manager  # 或 ./start.sh
```

## 工作原理

`migrate_db.py` 是一个智能数据库迁移工具，它会：

1. ✅ **自动检测**：对比代码中的模型定义与数据库实际结构
2. ✅ **自动升级**：添加缺失的表和字段
3. ✅ **保留数据**：不删除任何现有数据
4. ✅ **幂等操作**：可以重复运行，安全可靠

## 使用场景

### 场景1：新部署系统
```bash
sudo ./deploy.sh
# 选择 Y 运行数据库迁移
# 会自动创建数据库和所有表
```

### 场景2：升级现有系统
```bash
# 拉取最新代码
git pull

# 运行数据库迁移
python3 migrate_db.py

# 重启服务
sudo systemctl restart device-manager
```

### 场景3：恢复旧数据库
```bash
# 恢复备份
cp ~/backup/old_db.db backend/device_manager.db

# 升级到最新结构
python3 migrate_db.py

# 重启
sudo systemctl restart device-manager
```

## 验证升级成功

### 1. 检查迁移输出
运行 `migrate_db.py` 后应该看到：
```
✅ 数据库结构已是最新，无需升级
或
✅ 数据库已成功升级到最新版本！
```

### 2. 验证表结构
```bash
sqlite3 backend/device_manager.db "PRAGMA table_info(usage_records);"
```
应该看到 `login_info` 字段。

### 3. 测试功能
1. 登录系统
2. 占用一个有SSH配置的设备
3. 进入"使用记录"
4. 应该能看到"🖥️ 查看"按钮

## 常见问题

**Q: migrate_db.py 会删除数据吗？**  
A: 不会。它只添加缺失的表和字段，完全保留所有现有数据。

**Q: 可以多次运行吗？**  
A: 可以。脚本会自动检测已有的表和字段，不会重复添加。

**Q: 如果升级失败怎么办？**  
A: 检查错误信息，通常是权限问题或数据库文件被锁定。确保：
- 数据库文件有写权限
- 应用程序已停止（避免文件被锁定）

**Q: 旧的升级脚本还能用吗？**  
A: 可以，但不推荐。`update_db_add_login_info.py` 只能添加一个字段，而 `migrate_db.py` 能处理所有表结构变更。

## 部署最佳实践

1. **首次部署**
   ```bash
   ./deploy.sh  # 会自动运行迁移
   ```

2. **代码更新后**
   ```bash
   git pull
   python3 migrate_db.py
   sudo systemctl restart device-manager
   ```

3. **定期备份**
   ```bash
   # 设置定时备份（crontab）
   0 2 * * * cp /opt/device-manager/backend/device_manager.db /backup/db_$(date +\%Y\%m\%d).db
   ```

## 技术细节

### 支持的操作
- ✅ 创建新表
- ✅ 添加新字段
- ✅ 创建默认管理员账号
- ❌ 不删除表或字段（安全设计）
- ❌ 不修改现有数据类型（需手动处理）

### 表结构定义
所有表结构定义在 `backend/models.py` 中：
- `users` - 用户表
- `devices` - 设备表
- `usage_records` - 使用记录表（包含 `login_info` 字段）
- `allowed_users` - 授权用户表
- `audit_logs` - 审计日志表

### 迁移过程
```
1. 连接数据库
2. 获取现有表列表
3. 对比每个模型：
   - 如果表不存在 → 创建表
   - 如果表存在 → 检查字段
     - 如果字段缺失 → 添加字段
4. 验证结果
5. 显示统计信息
```

## 获取帮助

如遇问题，请提供：
1. `migrate_db.py` 的完整输出
2. 错误日志：`sudo journalctl -u device-manager -n 100`
3. 数据库文件权限：`ls -l backend/device_manager.db`
