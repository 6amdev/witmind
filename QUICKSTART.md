# Witmind Quick Start Guide

เริ่มใช้งาน Witmind ภายใน 5 นาที! 🚀

---

## ขั้นตอนที่ 1: ติดตั้ง Dependencies

```bash
# 1. เข้าไปใน witmind directory
cd ~/witmind

# 2. สร้าง virtual environment (ถ้ายังไม่มี)
python3 -m venv .venv

# 3. เปิด virtual environment
source .venv/bin/activate

# 4. ติดตั้ง dependencies สำหรับ platform
pip install -r platform/requirements.txt

# 5. ติดตั้ง dependencies สำหรับ workflow dashboard
pip install -r workflow-dashboard/backend/requirements.txt
```

---

## ขั้นตอนที่ 2: เช็ค API Keys

ตรวจสอบว่ามี API key ใน `~/.env`:

```bash
cat ~/.env | grep -E "(OPENROUTER|ANTHROPIC)_API_KEY"
```

ควรเห็น:
```
OPENROUTER_API_KEY=sk-or-v1-...
```

**ถ้าไม่มี:** เพิ่มเข้าไปใน `~/.env`

---

## ขั้นตอนที่ 3: เริ่ม Workflow Dashboard

### วิธีที่ 1: ใช้ script (แนะนำ)

```bash
cd ~/witmind
./workflow-dashboard/start.sh
```

### วิธีที่ 2: รัน manual

```bash
cd ~/witmind/workflow-dashboard/backend
source ../../.venv/bin/activate
python3 main.py
```

เมื่อเริ่มแล้วจะเห็น:
```
🚀 Starting Witmind Workflow Dashboard
   Backend: http://localhost:5000
   API Docs: http://localhost:5000/docs

INFO:     Uvicorn running on http://0.0.0.0:5000
```

---

## ขั้นตอนที่ 4: เปิดใช้งาน Dashboard

1. เปิดเว็บเบราว์เซอร์
2. ไปที่: **http://localhost:5000**
3. จะเห็น Dashboard สวยๆ!

---

## ขั้นตอนที่ 5: สร้าง Workflow แรก

### ตัวอย่างที่ 1: Portfolio Website

ใน Dashboard:

1. **Project Name:** `my_portfolio`
2. **Description:** `Create a personal portfolio website with dark theme and contact form`
3. **Template:** เลือก "Auto-detect" (ระบบจะเลือกให้)
4. ✅ เช็ค "Auto-approve all stages"
5. กด **🚀 Start Workflow**

**ผลลัพธ์:**
- ระบบเลือก template: **Simple Website**
- Agents ทำงาน: PM → Frontend Dev → QA
- ไฟล์สร้างใน: `~/witmind/workflow_projects/my_portfolio/`

---

### ตัวอย่างที่ 2: Mobile App

1. **Project Name:** `expense_tracker`
2. **Description:** `Build a mobile app for iOS and Android to track daily expenses`
3. **Template:** เลือก "Mobile App" (หรือ auto-detect)
4. กด **🚀 Start Workflow**

**ผลลัพธ์:**
- Template: **Mobile Application**
- Agents: PM → Tech Lead → UX/UI → Mobile Dev → QA → DevOps

---

### ตัวอย่างที่ 3: Marketing Campaign

1. **Project Name:** `product_launch_campaign`
2. **Description:** `Create blog posts and social media content for product launch`
3. กด **🚀 Start Workflow**

**ผลลัพธ์:**
- Template: **Content Campaign**
- Agents: Marketing Lead → Content Writer → SEO → Social Media Manager

---

## 📊 ดู Execution Log

ระหว่างที่ workflow กำลังทำงาน คุณจะเห็น:

```
[19:45:23] Starting workflow: my_portfolio
[19:45:23] Description: Create a personal portfolio...
[19:45:24] Agent pm started
[19:45:35] Agent pm completed
[19:45:36] Agent frontend_dev started
[19:46:15] Agent frontend_dev completed
[19:46:16] Agent qa_tester started
[19:46:30] Agent qa_tester completed
[19:46:31] Workflow completed!
```

---

## 📁 ดูผลลัพธ์

ไฟล์จะอยู่ใน:

```bash
cd ~/witmind/workflow_projects/my_portfolio/
ls -la
```

จะเห็น:
```
REQUEST.md           # คำขอเริ่มต้น
SPEC.md             # Specification (จาก PM)
ARCHITECTURE.md     # Architecture design (ถ้ามี Tech Lead)
src/                # Source code
  ├── index.html
  ├── style.css
  └── script.js
TEST_REPORT.md      # Test results (จาก QA)
```

---

## 🎯 Templates ที่มี

### Development (5 templates)

1. **Simple Website**
   - Use: Landing page, portfolio, blog
   - Agents: PM, Frontend Dev, QA (3 agents)
   - Time: ~5-10 minutes
   - Example: "Create a portfolio website"

2. **Full-stack Application**
   - Use: Complete web apps with backend
   - Agents: PM, BA, Tech Lead, UX/UI, Frontend, Backend, QA, Security, DevOps (9 agents)
   - Time: ~20-30 minutes
   - Example: "Build a todo app with user authentication"

3. **Mobile App**
   - Use: iOS/Android apps
   - Agents: PM, Tech Lead, UX/UI, Mobile Dev, QA, DevOps (6 agents)
   - Time: ~15-20 minutes
   - Example: "Build a habit tracking app for mobile"

4. **API Backend**
   - Use: REST API, microservices
   - Agents: PM, Tech Lead, Backend Dev, QA, Security, DevOps (6 agents)
   - Time: ~15-20 minutes
   - Example: "Create a REST API for a blog"

5. **Code Review**
   - Use: Review existing code
   - Agents: Tech Lead, Security Auditor, QA (3 agents)
   - Time: ~5-10 minutes
   - Example: "Review the code in src/ directory"

### Marketing (2 templates)

6. **Content Campaign**
   - Use: Blog posts, SEO content
   - Agents: Marketing Lead, Content Writer, SEO, Social Media (4 agents)
   - Example: "Create content for product launch"

7. **SEO Optimization**
   - Use: Improve SEO
   - Agents: SEO Specialist, Content Writer (2 agents)
   - Example: "Optimize website for search engines"

### Creative (2 templates)

8. **Branding**
   - Use: Logo, brand identity
   - Agents: Creative Director, Graphic Designer, UI Designer (3 agents)
   - Example: "Design a logo and brand identity"

9. **Video Production**
   - Use: Promotional videos
   - Agents: Creative Director, Motion Designer, Video Editor (3 agents)
   - Example: "Create a product demo video"

---

## 🤖 Auto-Detection Examples

ไม่แน่ใจจะเลือก template ไหน? ปล่อยให้ระบบเลือกให้!

| คำอธิบาย | Template ที่ระบบจะเลือก |
|---------|------------------------|
| "Build a portfolio" | Simple Website |
| "Create a mobile app" | Mobile App |
| "Build an API" | API Backend |
| "Full-stack web app" | Full-stack Application |
| "Review my code" | Code Review |
| "Write blog posts" | Content Campaign |
| "Improve SEO" | SEO Optimization |
| "Design a logo" | Branding |
| "Create a video" | Video Production |

---

## 🔧 Advanced: ใช้ API โดยตรง

### Get Templates

```bash
curl http://localhost:5000/api/templates
```

### Suggest Template

```bash
curl "http://localhost:5000/api/templates/suggest?description=Build+a+mobile+app"
```

### Execute Workflow

```bash
curl -X POST http://localhost:5000/api/projects/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_project",
    "description": "Create a portfolio website",
    "template_id": null,
    "auto_approve": true
  }'
```

### List Projects

```bash
curl http://localhost:5000/api/projects
```

---

## 📖 API Documentation

เปิดเว็บเบราว์เซอร์ไปที่:
```
http://localhost:5000/docs
```

จะเห็น Swagger UI พร้อม:
- ทุก API endpoints
- Try it out feature
- Request/Response examples

---

## 🆚 Mission Control vs Workflow Dashboard

คุณมี 2 ระบบ ใช้งานคนละแบบ:

### Mission Control (Port 4001)
```bash
cd ~/witmind/mission-control
docker compose up -d

# เปิด: http://localhost:4001
```

**ใช้เมื่อ:**
- ต้องการควบคุมแต่ละ task เอง
- จัดการทีม agents แบบ manual
- Kanban board style

### Workflow Dashboard (Port 5000)
```bash
cd ~/witmind/workflow-dashboard/backend
python3 main.py

# เปิด: http://localhost:5000
```

**ใช้เมื่อ:**
- อยากได้ automation แบบ end-to-end
- แค่บอกว่าอยากได้อะไร แล้วปล่อยให้ AI ทำ
- ต้องการ smart template selection

**ใช้ร่วมกันได้!** ตามความเหมาะสม

---

## ⚠️ Troubleshooting

### ปัญหา: "OPENROUTER_API_KEY not found"

**แก้:**
```bash
# เพิ่ม API key ใน ~/.env
echo "OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE" >> ~/.env
```

### ปัญหา: "Port 5000 already in use"

**แก้:**
```bash
# หา process ที่ใช้ port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# หรือเปลี่ยน port ใน main.py
```

### ปัญหา: "Module not found"

**แก้:**
```bash
# ตรวจสอบว่าอยู่ใน virtual environment
source ~/witmind/.venv/bin/activate

# ติดตั้ง dependencies ใหม่
pip install -r workflow-dashboard/backend/requirements.txt
```

### ปัญหา: Workflow ช้าหรือค้าง

**สาเหตุ:**
- LLM API อาจจะช้า
- Timeout settings

**แก้:**
- รอให้จบ (บาง workflow ใช้เวลานาน)
- เช็ค logs ใน terminal
- ลด max_iterations ใน agent configs

---

## 📈 Next Steps

เมื่อใช้งานได้แล้ว:

1. **ทดลอง templates ต่างๆ**
   - ลองทุก template ดูว่าแต่ละแบบทำงานยังไง

2. **ปรับแต่ง agent configs**
   - ดูใน `platform/teams/*/agents/*.yaml`
   - แก้ prompts, capabilities, limits

3. **สร้าง custom templates**
   - เพิ่มใน `workflow_templates.py`
   - กำหนด agents ที่ต้องการเอง

4. **ดู metrics**
   - เช็คว่าใช้ cost เท่าไหร่
   - Agent ไหนใช้เวลานานที่สุด
   - Success rate เป็นยังไง

5. **เชื่อมกับ Mission Control**
   - ใช้ทั้ง 2 ระบบร่วมกัน
   - Workflow Dashboard สำหรับเริ่มต้น
   - Mission Control สำหรับ fine-tune

---

## 🎉 สรุป

```bash
# 1. ติดตั้ง
cd ~/witmind
source .venv/bin/activate
pip install -r workflow-dashboard/backend/requirements.txt

# 2. เริ่ม Dashboard
./workflow-dashboard/start.sh

# 3. เปิดเบราว์เซอร์
http://localhost:5000

# 4. สร้าง Workflow
Project Name: my_portfolio
Description: Create a portfolio website
→ Start Workflow

# 5. ดูผลลัพธ์
cd ~/witmind/workflow_projects/my_portfolio/
ls -la
```

**ง่ายมาก!** แค่อธิบายว่าอยากได้อะไร ระบบทำให้! 🚀

---

## 📞 ต้องการความช่วยเหลือ?

- **Documentation:** `~/witmind/docs/`
- **Examples:** `~/witmind/examples/`
- **API Docs:** http://localhost:5000/docs
- **GitHub:** https://github.com/6amdev/witmind
