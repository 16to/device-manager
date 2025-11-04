# 🖥️ 服务器设备使用管理系统

## 📋 系统概述
为小型团队设计的服务器设备使用管理系统，旨在帮助管理员高效地管理服务器设备的使用情况。该系统提供设备录入、设备占用、使用记录、报表生成功能。管理员和普通用户均可通过网页界面访问系统，进行设备的维护和占用操作。

## ✨ 功能模块
- **设备录入**：管理员可以添加、编辑和删除服务器设备的信息，包括型号、账号/密码、位置等
- **设备占用**：用户可以查看设备列表，申请占用设备，并记录占用时间和用途
- **使用记录**：记录每台设备的使用情况，包括使用时间、使用人、用途等
- **报表生成**：生成设备使用和维护的报表，帮助管理员进行分析和决策

## 🛠️ 技术栈  
- **前端**：HTML、CSS、JavaScript、Vue.js 3
- **后端**：Python 3、Flask、Flask-SQLAlchemy
- **数据库**：SQLite
- **部署**：单机部署，支持本地运行

## 🚀 快速开始

### 前置要求
- Python 3.8 或更高版本
- pip3（Python包管理器）

### 安装和启动

1. **使用启动脚本（推荐）**
```bash
chmod +x start.sh
./start.sh
```

2. **手动启动**
```bash
# 安装依赖
pip3 install -r requirements.txt

# 启动服务
cd backend
python3 app.py
```

3. **访问系统**
在浏览器中打开：http://localhost:3000

## 📖 使用说明

详细的使用说明请参考 [USAGE.md](USAGE.md) 文件。

## 🔑 默认管理员账号
系统启动时会自动创建一个默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`

## 📁 项目结构
```
device-manager/
├── README.md                 # 项目说明文档
├── USAGE.md                  # 详细使用说明
├── requirements.txt          # Python依赖包列表
├── start.sh                  # 一键启动脚本（Linux/Mac）
├── backend/                  # 后端代码
│   ├── app.py               # Flask应用主文件
│   ├── models.py            # 数据库模型
│   └── device_manager.db    # SQLite数据库（运行后生成）
└── frontend/                 # 前端代码
    └── index.html           # 前端单页面应用
```

## 🌟 主要功能特性

### 1. 设备管理
- ✅ 添加、编辑、删除设备
- ✅ 查看设备状态（空闲/占用中）
- ✅ 记录设备详细信息（型号、位置、账号密码）

### 2. 设备占用
- ✅ 占用空闲设备
- ✅ 释放已占用设备
- ✅ 记录使用人和使用目的

### 3. 使用记录
- ✅ 查看所有设备的使用历史
- ✅ 自动计算使用时长
- ✅ 支持按设备筛选记录

### 4. 统计报表
- ✅ 设备总数统计
- ✅ 空闲/占用设备统计
- ✅ 使用次数排行榜
- ✅ 实时数据更新

## 🔧 API接口

系统提供完整的RESTful API，详细文档请参考 [USAGE.md](USAGE.md) 的API接口部分。

主要接口：
- `GET /api/devices` - 获取设备列表
- `POST /api/devices` - 创建新设备
- `POST /api/devices/<id>/occupy` - 占用设备
- `POST /api/devices/<id>/release` - 释放设备
- `GET /api/records` - 获取使用记录
- `GET /api/statistics` - 获取统计数据

## ⚠️ 注意事项
1. 系统使用SQLite数据库，数据文件保存在 `backend/device_manager.db`
2. 首次运行会自动创建空数据库表和默认管理员账号
3. 数据库文件不会被提交到git，部署时会创建全新的空数据库
4. 建议在Chrome、Firefox、Safari等现代浏览器中使用
5. 生产环境部署时，请修改默认管理员密码（在 config.json 中）
6. 系统前后端已合并，统一使用3000端口
7. 可在 config.json 中修改端口等配置
8. 所有静态资源已本地化，无需依赖外部CDN

## 📝 许可证
MIT License

## 👨‍💻 作者
Device Manager Team

---

**系统已成功部署并运行！** 🎉
- 访问地址: http://localhost:3000