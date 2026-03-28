# 🚀 快速启动指南

## 📋 前置要求

- **Python**: 3.11+
- **PostgreSQL**: 15+
- **Redis**: 7+

## 🛠️ 安装步骤

### 1. 克隆项目

```bash
cd backend
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入必要配置：
# - 数据库连接信息
# - Redis 连接信息
# - DeepSeek API Key
# - OpenRouter API Key（可选）
```

**最低配置要求：**
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/docwriting
DATABASE_URL_SYNC=postgresql+psycopg2://user:password@localhost:5432/docwriting
REDIS_URL=redis://localhost:6379/0
SILICONFLOW_API_KEY=your_api_key_here
SECRET_KEY=your-secret-key-here
```

### 5. 启动数据库服务

**使用 Docker（推荐）：**
```bash
docker-compose up -d postgres redis
```

**或手动启动：**
```bash
# PostgreSQL
# Windows: 从服务管理器启动
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql

# Redis
# Windows: 从服务管理器启动
# macOS: brew services start redis
# Linux: sudo systemctl start redis
```

### 6. 创建数据库

```bash
# 连接到 PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE docwriting;
\q
```

### 7. 初始化数据库

```bash
# 运行 Alembic ���移
alembic upgrade head

# 或使用初始化脚本（开发环境）
python scripts/init_db.py
```

### 8. 启动服务

```bash
# 开发模式（自动重载）
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 9. 验证安装

访问以下地址：

- **API 文档（Swagger）**: http://localhost:8000/docs
- **API 文档（ReDoc）**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/api/v1/health

预期响应：
```json
{
  "status": "healthy",
  "service": "公文写作AI系统",
  "version": "1.0.0"
}
```

## 📦 可选：启动 Celery Worker

如果需要使用异步任务：

```bash
# 终端 1：启动 Celery Worker
celery -A tasks.celery_app worker --loglevel=info

# 终端 2：启动 Flower（监控）
celery -A tasks.celery_app flower

# 访问 Flower: http://localhost:5555
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=.

# 运行特定测试文件
pytest tests/test_api/test_documents.py
```

## 🔧 开发工具

### 代码格式化

```bash
# Black（代码格式化）
black .

# isort（导入排序）
isort .
```

### 代码检查

```bash
# Flake8（代码规范检查）
flake8 .

# mypy（类型检查）
mypy .
```

### 一键格式化 + 检查

```bash
black . && isort . && flake8 . && mypy .
```

## 📝 开发流程示例

### 1. 创建新的 API 端点

```python
# api/endpoints/your_feature.py
from fastapi import APIRouter, Depends
from core.database import get_db

router = APIRouter()

@router.get("/your-endpoint")
async def your_endpoint(db: AsyncSession = Depends(get_db)):
    return {"message": "Hello"}
```

### 2. 注册路由

```python
# api/v1/api.py
from api.endpoints import your_feature

api_router.include_router(
    your_feature.router,
    prefix="/your-feature",
    tags=["Your Feature"],
)
```

### 3. 启动服务

```bash
python main.py
```

### 4. 测试 API

访问 http://localhost:8000/docs，找到你的端点进行测试。

## ⚠️ 常见问题

### 问题 1：数据库连接失败

**解决方案：**
1. 检查 PostgreSQL 是否运行
2. 检查 .env 中的数据库连接字符串
3. 确认数据库已创建

### 问题 2：Redis 连接失败

**解决方案：**
1. 检查 Redis 是否运行
2. 检查 .env 中的 Redis URL
3. 测试连接：`redis-cli ping`

### 问题 3：API 调用失败

**解决方案：**
1. 检查 API Key 是否正确
2. 查看日志：`logs/app.log`
3. 开启 DEBUG 模式查看详细错误

### 问题 4：端口被占用

**解决方案：**
```bash
# 查看占用端口的进程
# Windows
netstat -ano | findstr :8000

# macOS/Linux
lsof -i :8000

# 或修改 .env 中的 API_PORT
API_PORT=8001
```

## 📚 下一步

1. 阅读 [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) 了解项目结构
2. 查看 [STRUCTURE_TREE.txt](./STRUCTURE_TREE.txt) 可视化目录树
3. 开始实现文档库功能

## 🆘 需要帮助？

- 查看日志：`tail -f logs/app.log`
- 提 Issue：[GitHub Issues](链接)
- 联系团队：邮箱或企业微信

---

**Happy Coding! 🎉**
