# OpenRouter API Key 更新指南

## 🔑 问题说明

当前API Key返回 `401 - User not found` 错误，这意味着：
- API Key已过期
- API Key被撤销/删除
- 账户需要重新验证

---

## 📝 获取新API Key的步骤

### 1. 登录OpenRouter

访问：https://openrouter.ai/

### 2. 进入设置

1. 点击右上角的用户头像
2. 选择 "Settings"

### 3. 创建API Key

1. 在左侧菜单选择 "API Keys"
2. 点击 "Create New Key" 按钮
3. （可选）输入Key名称/描述
4. 点击 "Create"
5. **立即复制API Key**（格式：`sk-or-v1-xxxxxxxxx`）

⚠️ **重要**：API Key只会显示一次，请妥善保管！

---

## 🔧 更新API Key

### 方法1：使用更新工具（推荐）

```bash
python update_api_key.py
```

按提示输入新的API Key即可。

### 方法2：手动编辑

编辑 `backend/.env` 文件：

```bash
OPENROUTER_API_KEY=sk-or-v1-你的新密钥
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_IMAGE_MODEL=google/gemini-3-pro-image-preview
```

---

## ✅ 验证和测试

### 1. 验证API Key

```bash
python verify_openrouter_key.py
```

预期输出：
```
✅ API Key 验证成功！
```

### 2. 测试图片转译

```bash
python test_image_translation.py
```

---

## 💡 关于OpenRouter模型

### 免费模型
- `meta-llama/llama-3-8b-instruct:free`
- `mistralai/mistral-7b-instruct:free`

### 图片转译模型（需要付费）
- `google/gemini-3-pro-image-preview` - 当前使用
- `openai/gpt-4-vision-preview`
- `anthropic/claude-3.5-sonnet`

### 💰 充值

1. 登录OpenRouter
2. 进入 Settings → Billing
3. 选择充值金额（最低$5）
4. 完成支付

---

## 🆘 常见问题

### Q: 为什么充值了还是401错误？
A: 401是认证错误，不是余额问题。需要创建新的API Key。

### Q: API Key在哪里？
A: https://openrouter.ai/settings/keys

### Q: 忘记复制API Key了怎么办？
A: 删除旧的Key，重新创建一个新的。

### Q: 可以使用其他AI服务吗？
A: 可以！系统已��置硅基流动DeepSeek，也可以配置其他服务。

---

## 📞 需要帮助？

- OpenRouter文档：https://openrouter.ai/docs
- OpenRouter Discord：https://discord.gg/openrouter
- 邮箱支持：support@openrouter.ai
