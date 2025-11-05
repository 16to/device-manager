# 离线部署指南

本项目支持完全离线部署，无需网络连接即可安装所有 Python 依赖。

## 📦 准备离线安装包

在有网络的环境中，运行导出脚本：

```bash
chmod +x export-libs.sh
./export-libs.sh
```

这将：
1. 下载所有 Python 依赖包到 `libs/` 目录（约 17MB，24 个包）
2. 打包后可在离线环境使用

## 🚀 离线部署步骤

### 方法一：使用 start.sh（本地运行）

```bash
# 1. 将整个项目目录（包含 libs/）复制到目标机器
# 2. 确保目标机器已安装 Python 3.8+
# 3. 运行启动脚本
./start.sh
```

**自动检测：**
- 如果存在 `libs/` 目录，自动使用离线模式
- 如果不存在，自动从镜像源下载

### 方法二：使用 deploy.sh（生产部署）

```bash
# 1. 将整个项目目录（包含 libs/）复制到目标服务器
# 2. 运行部署脚本
sudo ./deploy.sh
```

**自动检测：**
- 优先使用 `libs/` 目录进行离线安装
- 如果不存在，自动从镜像源下载

## 📋 系统要求

**必须：**
- Python 3.8 或更高版本
- 基本的 Python 工具（python3-venv，通常系统自带）

**可选：**
- 网络连接（仅在没有 libs/ 目录时需要）

## 🎯 使用场景

### 场景一：有网络环境
```bash
# 直接运行，自动下载依赖
./start.sh
```

### 场景二：完全离线环境
```bash
### 第一步：准备离线依赖包

在有网络环境的机器上：

```bash
# 导出所有依赖到 libs/ 目录（包括构建工具 setuptools 和 wheel）
./export-libs.sh
```

**注意**：export-libs.sh 会自动下载：
- 构建依赖：setuptools (<70, 兼容 Python 3.8), wheel
- 项目依赖：Flask, SQLAlchemy, paramiko 等所有 requirements.txt 中的包
- Python 3.8/3.9 兼容性依赖：importlib-metadata, zipp
- Linux x86_64 平台包：bcrypt, cryptography, PyNaCl, cffi, MarkupSafe（用于跨平台部署）

**重要**：
- setuptools 70+ 需要 Python 3.9+，脚本会自动下载 setuptools 69.x
- importlib-metadata 是 Python 3.8/3.9 环境下 Flask 的必需依赖
- 包含 macOS 和 Linux x86_64 两个平台的二进制包，支持跨平台部署
- 总共约 33 个包，大小约 24MB

# 2. 打包整个项目（包含 libs/）
tar -czf device-manager.tar.gz .

# 3. 在离线机器上解压并运行
tar -xzf device-manager.tar.gz
./start.sh  # 自动使用离线模式
```

### 场景三：内网环境部署
```bash
# 1. 准备离线包
./export-libs.sh

# 2. 通过内网传输到目标服务器
# 3. 部署
sudo ./deploy.sh  # 自动检测并使用 libs/
```

## 📊 libs/ 目录说明

```
libs/
├── Flask-2.3.3-py3-none-any.whl
├── Flask_SQLAlchemy-2.5.1-py2.py3-none-any.whl
├── Werkzeug-2.3.8-py3-none-any.whl
├── SQLAlchemy-1.4.54.tar.gz
├── ... （共 24 个包，约 17MB）
```

**特点：**
- 包含所有直接依赖和间接依赖
- 预编译的 wheel 文件，安装快速
- 跨平台兼容（Python 3.8+）

## ⚠️ 注意事项

1. **Python 版本**：libs/ 中的包适用于 Python 3.8+
2. **平台兼容**：MacOS 上导出的包可能包含平台特定文件，建议在目标平台上重新运行 `export-libs.sh`
3. **更新依赖**：修改 `requirements.txt` 后需要重新运行 `export-libs.sh`
4. **存储空间**：libs/ 目录约 17MB，打包后约 10MB

## 🔄 更新离线包

当项目依赖更新时：

```bash
# 删除旧的离线包
rm -rf libs/

# 重新导出
./export-libs.sh

# 提交到 git（可选）
git add libs/
git commit -m "更新离线依赖包"
```

## 📝 技术细节

**安装命令：**
```bash
# 离线模式
pip3 install --no-index --find-links=libs -r requirements.txt

# 在线模式
pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

**自动检测逻辑：**
```bash
if [ -d "libs" ] && [ "$(ls -A libs 2>/dev/null)" ]; then
    # 使用离线模式
else
    # 使用在线模式
fi
```

## ✅ 验证安装

```bash
# 激活虚拟环境
source .venv/bin/activate

# 查看已安装的包
pip3 list | grep -E "Flask|SQLAlchemy|socketio|paramiko"

# 应该看到所有依赖都已安装
```

---

**完全离线部署 = Python 3.8+ + 项目代码 + libs/ 目录** 🎉
