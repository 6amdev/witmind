# 🚀 START HERE - Witmind Quick Guide

## วิธีเริ่มใช้งาน (เริ่มตรงนี้!)

### 1. เปิด Terminal และรันคำสั่ง:

```bash
cd ~/witmind/workflow-dashboard/backend
source ../../.venv/bin/activate
python3 main.py
```

### 2. เปิดเว็บเบราว์เซอร์:

```
http://localhost:5000
```

### 3. ทดลองสร้าง Workflow:

**ตัวอย่างที่ 1: Portfolio Website**
```
Project Name: my_portfolio
Description: Create a modern portfolio website with dark theme
Template: Auto-detect (ปล่อยว่าง)
✅ Auto-approve
→ กด "Start Workflow"
```

**ตัวอย่างที่ 2: Mobile App**
```
Project Name: habit_tracker  
Description: Build a mobile app for iOS to track daily habits
Template: Mobile App
✅ Auto-approve
→ กด "Start Workflow"
```

**ตัวอย่างที่ 3: Blog Content**
```
Project Name: product_launch
Description: Create blog posts and social media content for new product launch
Template: Auto-detect
✅ Auto-approve
→ กด "Start Workflow"
```

### 4. ดูผลลัพธ์:

```bash
cd ~/witmind/workflow_projects/my_portfolio/
ls -la
cat SPEC.md
cat src/index.html
```

---

## 📋 Templates ที่มี (9 แบบ)

### Development:
- ✅ **Simple Website** - Portfolio, landing pages (PM, Frontend, QA)
- ✅ **Full-stack App** - Complete web apps (9 agents)
- ✅ **Mobile App** - iOS/Android apps (6 agents)
- ✅ **API Backend** - REST APIs (6 agents)
- ✅ **Code Review** - Review code (3 agents)

### Marketing:
- ✅ **Content Campaign** - Blog + SEO + Social (4 agents)
- ✅ **SEO Optimization** - Improve rankings (2 agents)

### Creative:
- ✅ **Branding** - Logo + Identity (3 agents)
- ✅ **Video Production** - Videos (3 agents)

---

## 💡 Tips

1. **Auto-detect ฉลาดมาก!** 
   - แค่อธิบายว่าอยากได้อะไร
   - ระบบเลือก template และ agents ให้อัตโนมัติ

2. **Auto-approve แนะนำให้เปิด**
   - Agents ทำงานต่อเนื่องไม่หยุด
   - เหมาะสำหรับทดลอง

3. **ดู Execution Log**
   - เห็น real-time ว่า agent กำลังทำอะไร
   - Debug ได้ง่าย

4. **ผลลัพธ์ใน workflow_projects/**
   - แต่ละ project มี folder ของตัวเอง
   - มีทั้ง SPEC, code, tests

---

## 🎯 สิ่งที่ควรรู้

### ระบบมี 2 อัน:

1. **Mission Control (Port 4001)** 
   - Kanban board
   - Manual task management
   - เหมือน Jira

2. **Workflow Dashboard (Port 5000)** ← ใหม่!
   - Autonomous AI workflows
   - Template-based
   - แค่อธิบาย มันทำให้!

### ใช้ตอนไหน?

- **Mission Control**: จัดการทีม, ควบคุมแต่ละ task
- **Workflow Dashboard**: สร้างของใหม่แบบเร็ว, automation

---

## 🚀 เริ่มเลย!

```bash
cd ~/witmind/workflow-dashboard/backend
python3 main.py
```

แล้วเปิด: **http://localhost:5000**

มีปัญหา? อ่าน: `~/witmind/QUICKSTART.md`
