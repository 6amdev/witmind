# LLM Providers Guide

## ตัวเลือก LLM ที่รองรับ

Witmind รองรับ 3 providers:

### 1. 🌟 OpenRouter (แนะนำ!)

**ทำไมถึงแนะนำ:**
- ✅ คีย์เดียว ใช้ได้หลาย models (Claude, GPT-4, Gemini, Llama)
- ✅ มี **models ฟรี** สำหรับทดสอบ
- ✅ Pay-as-you-go (ไม่มี subscription)
- ✅ ราคาถูกกว่า API ตรง

**Setup:**
```bash
# 1. สมัครที่ https://openrouter.ai
# 2. ไปที่ https://openrouter.ai/keys
# 3. สร้าง API key
# 4. เพิ่มใน .env

echo "OPENROUTER_API_KEY=sk-or-v1-xxx" >> ~/.env
```

**Models แนะนำ:**

| Model | ราคา | เหมาะสำหรับ |
|-------|------|------------|
| `google/gemini-flash-1.5` | **ฟรี!** | Development, Testing |
| `meta-llama/llama-3.2-3b-instruct` | **ฟรี!** | Simple tasks |
| `anthropic/claude-3-haiku` | ถูก (~$0.25/1M) | Fast tasks |
| `anthropic/claude-3.5-sonnet` | ปานกลาง (~$3/1M) | Smart agents |
| `openai/gpt-4o` | แพง (~$2.50/1M) | Complex tasks |

**การใช้งาน:**

```python
# ใช้ model ฟรี (Gemini)
llm = create_llm_client(
    provider='openrouter',
    model='google/gemini-flash-1.5'
)

# ใช้ Claude ผ่าน OpenRouter
llm = create_llm_client(
    provider='openrouter',
    model='anthropic/claude-3.5-sonnet'
)

# ใช้ GPT-4
llm = create_llm_client(
    provider='openrouter',
    model='openai/gpt-4o'
)
```

---

### 2. 🤖 Claude (Anthropic API)

**ข้อดี:**
- ✅ ฉลาดที่สุด สำหรับงานซับซ้อน
- ✅ API ตรงจาก Anthropic
- ✅ Sonnet 4.5 รุ่นล่าสุด

**ข้อเสีย:**
- ❌ แยกจาก claude.ai subscription
- ❌ ต้องเติมเงินขั้นต่ำ $5
- ❌ แพงกว่า OpenRouter เล็กน้อย

**Setup:**
```bash
# 1. ไป https://console.anthropic.com
# 2. สมัคร และเติมเงิน
# 3. สร้าง API key
# 4. เพิ่มใน .env

echo "ANTHROPIC_API_KEY=sk-ant-xxx" >> ~/.env
```

**ราคา:**
- Sonnet 4.5: ~$3/1M input tokens
- Haiku 4: ~$0.25/1M input tokens

**การใช้งาน:**
```python
llm = create_llm_client(provider='claude')

# จะใช้ claude-sonnet-4-20250514 (ล่าสุด)
```

---

### 3. 🖥️ Ollama (Local, ฟรี)

**ข้อดี:**
- ✅ **ฟรี 100%** ไม่มีค่าใช้จ่าย
- ✅ รันบน server นี้เอง
- ✅ ไม่ต้อง API key
- ✅ Privacy (data ไม่ออกจาก server)

**ข้อเสีย:**
- ❌ ไม่ฉลาดเท่า Claude/GPT-4
- ❌ ช้ากว่า (ถ้า CPU/GPU อ่อน)
- ❌ ใช้ RAM/VRAM เยอะ

**Setup:**
```bash
# Ollama รันอยู่แล้วใน Docker
docker compose ps ollama  # ตรวจสอบ

# ถ้ายังไม่รัน
cd ~/witmind/docker
docker compose up -d ollama
```

**Models ที่มี:**
```bash
# ดู models ที่ติดตั้งแล้ว
docker exec ollama ollama list

# ติดตั้ง model ใหม่
docker exec ollama ollama pull llama3.2
docker exec ollama ollama pull codellama
docker exec ollama ollama pull mistral
```

**การใช้งาน:**
```python
# ใช้ Ollama ใน Docker
llm = create_llm_client(
    provider='ollama',
    base_url='http://ollama:11434',  # Docker service
    model='llama3.2'
)

# ถ้ารัน Ollama นอก Docker
llm = create_llm_client(
    provider='ollama',
    base_url='http://localhost:11434',
    model='llama3.2'
)
```

---

## เปรียบเทียบ

| Feature | OpenRouter | Claude | Ollama |
|---------|-----------|--------|--------|
| **ราคา** | ฟรี-ปานกลาง | ปานกลาง | **ฟรี** |
| **ความฉลาด** | ดีมาก | **ดีที่สุด** | พอใช้ |
| **ความเร็ว** | เร็ว | เร็ว | ช้า |
| **Setup** | ง่าย | ง่าย | **ง่ายที่สุด** |
| **Privacy** | ส่งข้อมูลออก | ส่งข้อมูลออก | **ไม่ส่งออก** |
| **Models** | **หลายตัว** | Claude only | หลายตัว |

---

## แนะนำสำหรับแต่ละ Use Case

### 🧪 Development & Testing
```python
# ใช้ OpenRouter + Gemini (ฟรี!)
llm = create_llm_client('openrouter', model='google/gemini-flash-1.5')
```

### 🎯 Production (Smart Agents)
```python
# ใช้ OpenRouter + Claude (ถูกกว่า API ตรง)
llm = create_llm_client('openrouter', model='anthropic/claude-3.5-sonnet')
```

### 🔒 Privacy-focused / No internet
```python
# ใช้ Ollama (local)
llm = create_llm_client('ollama', base_url='http://ollama:11434')
```

### 💰 Free forever
```python
# ใช้ Ollama
llm = create_llm_client('ollama', model='llama3.2', base_url='http://ollama:11434')
```

---

## ทดสอบว่า Provider ไหนใช้ได้

```bash
cd ~/witmind

# ทดสอบทุก providers
python3 examples/test_llm_providers.py

# จะแสดง:
# ✅ Working providers
# ❌ Failed providers
# 💡 Recommendations
```

---

## Configuration แนะนำ

### สำหรับ Development:

```bash
# ~/.env
OPENROUTER_API_KEY=sk-or-v1-xxx  # สมัครฟรีที่ openrouter.ai
```

```python
# ใช้ model ฟรี
llm = create_llm_client('openrouter', model='google/gemini-flash-1.5')
```

### สำหรับ Production:

```bash
# ~/.env
OPENROUTER_API_KEY=sk-or-v1-xxx
```

```python
# Agent config
pm_agent = create_intelligent_agent(
    agent_id='pm',
    llm_client=create_llm_client('openrouter', model='anthropic/claude-3.5-sonnet'),
    ...
)

frontend_dev = create_intelligent_agent(
    agent_id='frontend_dev',
    llm_client=create_llm_client('openrouter', model='anthropic/claude-3-haiku'),  # ถูกกว่า
    ...
)

qa_tester = create_intelligent_agent(
    agent_id='qa',
    llm_client=create_llm_client('ollama', model='llama3.2'),  # ฟรี
    ...
)
```

---

## Quick Start

1. **สมัคร OpenRouter** (แนะนำ!):
   - ไป https://openrouter.ai/keys
   - สร้าง API key
   - `echo "OPENROUTER_API_KEY=xxx" >> ~/.env`

2. **ทดสอบ**:
   ```bash
   cd ~/witmind
   export $(grep -v '^#' ~/.env | xargs)
   python3 examples/test_llm_providers.py
   ```

3. **ใช้งาน**:
   ```python
   from core.llm_client import create_llm_client

   llm = create_llm_client('openrouter', model='google/gemini-flash-1.5')
   response = llm.chat(messages=[{'role': 'user', 'content': 'Hello!'}])
   ```

---

## Resources

- **OpenRouter**: https://openrouter.ai
- **Claude API**: https://console.anthropic.com
- **Ollama**: https://ollama.ai
- **Model Rankings**: https://openrouter.ai/rankings
