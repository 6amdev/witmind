# Agent Memory Template

> Template สำหรับสร้าง Memory file ของ agent
> Copy ไปใช้ที่: `platform/teams/{team}/agents/{agent_id}/MEMORY.md`

---

## 📋 Basic Info

```yaml
agent_id: {AGENT_ID}
agent_name: {AGENT_NAME}
team: {TEAM_ID}
created: {DATE}
last_updated: {DATE}
```

---

## 🎯 My Role

**ฉันคือ:** {ROLE_DESCRIPTION}

**หน้าที่หลัก:**
- [ ] {RESPONSIBILITY_1}
- [ ] {RESPONSIBILITY_2}
- [ ] {RESPONSIBILITY_3}

---

## ✅ Skills (สิ่งที่ทำได้)

| Skill | Level | Notes |
|-------|-------|-------|
| {SKILL_1} | Expert | {NOTES} |
| {SKILL_2} | Good | {NOTES} |
| {SKILL_3} | Basic | {NOTES} |

---

## ❌ Limitations (สิ่งที่ทำไม่ได้)

- ❌ {LIMITATION_1}
- ❌ {LIMITATION_2}
- ❌ {LIMITATION_3}

---

## 🔧 Tools Available

```
✅ Can use:
- Read, Write, Edit
- Bash (limited)
- {OTHER_TOOLS}

❌ Cannot use:
- {RESTRICTED_TOOL}
```

---

## 📥 I Receive From

| Agent | What | When |
|-------|------|------|
| {AGENT} | {DOCUMENT/TASK} | {TRIGGER} |

---

## 📤 I Send To

| Agent | What | When |
|-------|------|------|
| {AGENT} | {DOCUMENT/OUTPUT} | {TRIGGER} |

---

## 📚 Learnings (Update เรื่อยๆ)

### Mistakes & Corrections

#### {DATE}
- ❌ **ผิด:** {WHAT_WENT_WRONG}
- ✅ **แก้:** {HOW_TO_FIX}
- 💡 **จำ:** {LESSON_LEARNED}

### Patterns Discovered

- 📌 {PATTERN_1}
- 📌 {PATTERN_2}

### User Preferences

- 👤 {PREFERENCE_1}
- 👤 {PREFERENCE_2}

---

## 📊 Performance Log

| Date | Task | Result | Notes |
|------|------|--------|-------|
| {DATE} | {TASK} | ✅/❌ | {NOTES} |

---

## 🔗 Related Files

- Agent definition: `platform/teams/{team}/agents/{agent_id}.yaml`
- Prompt: `platform/prompts/{agent_id}.md`
- Team config: `platform/teams/{team}/team.yaml`

---

*Template version: 1.0*
