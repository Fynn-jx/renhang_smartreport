# 公文写作 AI 系统后端

## 📖 项目简介

这是一个基于 FastAPI 的企业级文档管理与 AI 处理平台，提供 Zotero 式的文档管理能力和五大 AI 工作流。

## 🚀 技术栈

- **框架**: FastAPI 0.109+
- **数据库**: PostgreSQL 15+ (通过 SQLAlchemy 2.0)
- **缓存/队列**: Redis 7+
- **任务队列**: Celery 5+
- **AI 服务**: DeepSeek (硅基流动)、OpenRouter
- **向量检索**: pgvector / Qdrant

## 📁 项目结构

详见 [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)

## 🔧 快速开始

### 1. 环境要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 2. 安装依赖

```bash
# 使用 poetry（推荐）
poetry install

# 或使用 pip
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

### 4. 初始化数据库

```bash
# 运行数据库迁移
alembic upgrade head

# 或使用初始化脚本
python scripts/init_db.py
```

### 5. 启动服务

```bash
# 启动 FastAPI 服务
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 启动 Celery Worker（可选）

```bash
celery -A tasks.celery_app worker --loglevel=info
```

### 7. 启动 Flower（可选，用于监控 Celery）

```bash
celery -A tasks.celery_app flower
```

## 📚 API 文档

启动服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=.

# 运行特定测试
pytest tests/test_api/test_documents.py
```

## 📝 开发规范

### 代码风格

```bash
# 格式化代码
black .
isort .

# 检查代码规范
flake8 .

# 类型检查
mypy .
```

### 提交规范

使用 Conventional Commits 规范：
- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具链相关

## 🔐 安全注意事项

1. **生产环境必须修改**：
   - `SECRET_KEY`（JWT 密钥）
   - 数据库密码
   - API 密钥

2. **敏感信息管理**：
   - 不要将 `.env` 文件提交到版本控制
   - 使用环境变量或密钥管理服务

## 📊 监控与日志

- 日志位置：`./logs/`
- Flower 监控：http://localhost:5555

## 🚧 待办事项

- [ ] 完成文档库功能
- [ ] 实现五大工作流
- [ ] 实现 SSE 流式输出
- [ ] 完善单元测试
- [ ] Docker 部署方案

## 📄 License

MIT License

## 👥 联系方式

如有问题，请提 Issue 或联系开发团队。
