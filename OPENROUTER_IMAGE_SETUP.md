# OpenRouter 图片转译功能配置指南

## 问题描述

如果图片转译功能出现 **401 "User not found"** 错误，这是因为 OpenRouter API Key 未正确配置。

## 解决方案

### 1. 获取 OpenRouter API Key

1. 访问 [OpenRouter官网](https://openrouter.ai/)
2. 注册或登录账号
3. 进入 "Keys" 页面
4. 创建一个新的 API Key
5. 复制生成的 API Key

### 2. 配置后端环境变量

在后端项目根目录创建 `.env` 文件（如果不存在）：

```bash
cd backend
cp .env.example .env
```

然后编辑 `.env` 文件，设置你的 OpenRouter API Key：

```env
# OpenRouter (图片转译)
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_IMAGE_MODEL=google/gemini-2.0-flash-exp
```

### 3. 支持的模型

OpenRouter 支持多个支持图片的模型，常用的有：

- `google/gemini-2.0-flash-exp` - 推荐，快速且准确
- `google/gemini-2.5-pro-exp` - 更强大的模型
- `anthropic/claude-3.5-sonnet` - 支持图片
- `openai/gpt-4o` - OpenAI 的多模态模型

**注意**：不同模型价格不同，请查看 [OpenRouter Pricing](https://openrouter.ai/models?modality=image) 了解详情。

### 4. 重启后端服务

配置完成后，重启后端服务：

```bash
cd backend
# 如果使用 uvicorn
uvicorn main:app --reload

# 或者使用其他启动方式
python main.py
```

### 5. 验证配置

1. 打开前端应用
2. 进入"图片转译"模块
3. 上传一张包含英文的图片
4. 点击"开始转译"
5. 如果配置正确，应该能看到转译进度和结果

## 免费替代方案

如果不想使用 OpenRouter，可以考虑以下免费方案：

### 方案1：使用本地 OCR + 翻译

可以集成以下本地工具：
- **Tesseract OCR** - 文字识别
- **翻译 API** - 使用免费的翻译服务

### 方案2：使用其他 AI 服务

- **Google Cloud Vision API** - 有免费额度
- **Azure Computer Vision** - 有免费层级
- **百度 OCR** - 国内服务，有免费额度

## 常见问题

### Q: 图片转译需要多少钱？

A: OpenRouter 按使用量计费。以 Gemini 2.0 Flash 为例，大约是：
- 输入：$0.075 / 1M tokens
- 输出：$0.30 / 1M tokens

普通图片转译成本约为 $0.01-0.05 / 张。

### Q: 为什么不使用免费的方案？

A: 免费方案通常有以下限制：
- 请求频率限制
- 每日/每月配额限制
- 功能不如付费方案完善
- 可能需要更复杂的集成

### Q: 能否批量转译多张图片？

A: 可以！系统支持一次上传最多 5 张图片进行批量转译。

### Q: 转译失败后怎么办？

A: 检查以下几点：
1. API Key 是否正确配置
2. 账户余额是否充足
3. 图片格式是否支持（JPG、PNG、GIF、WebP、BMP）
4. 图片大小是否超过限制（10MB）
5. 网络连接是否正常

## 技术支持

如果遇到问题，请查看：
1. 后端日志：`backend/logs/app.log`
2. 浏览器控制台错误信息
3. [OpenRouter 文档](https://openrouter.ai/docs)

## 更新日志

- 2026-03-31: 初始版本，添加 OpenRouter 图片转译功能配置指南
