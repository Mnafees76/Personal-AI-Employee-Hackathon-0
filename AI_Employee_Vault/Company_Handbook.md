# Company Handbook

## Welcome to Your Personal AI Employee System

This handbook outlines the rules, guidelines, and best practices for operating your Bronze-tier Personal AI Employee.

---

## Core Principles

### 1. Task Management
- All new tasks must be placed in `/Inbox` or `/Needs_Action`
- Tasks are automatically processed by the watcher system
- Completed tasks are moved to `/Done`
- Plans are stored in `/Plans` for tracking

### 2. Communication
- Use clear, descriptive filenames for tasks
- Include relevant metadata in task files (priority, deadline, etc.)
- Log all actions in the `/Logs` folder

### 3. Organization
- Keep the vault structure intact
- Do not manually move files between folders (let automation handle it)
- Review the Dashboard regularly for status updates

---

## Folder Structure

```
/AI_Employee_Vault
├── /.obsidian          # Obsidian configuration
├── /Done               # Completed tasks archive
├── /Inbox              # New incoming tasks
├── /Logs               # System activity logs
├── /Needs_Action       # Tasks requiring processing
├── /Plans              # Task plans and strategies
├── /Skills             # AI capability documentation
├── Company_Handbook.md # This file
├── Dashboard.md        # Main status dashboard
├── filesystem_watcher.py
├── process_needs_action.py
└── README.md
```

---

## Task Lifecycle

1. **Creation**: Task file created in `/Inbox` or `/Needs_Action`
2. **Detection**: `filesystem_watcher.py` detects new file
3. **Processing**: `process_needs_action.py` creates a plan
4. **Execution**: Plan is executed (manual or automated)
5. **Completion**: Task moved to `/Done`
6. **Logging**: All steps recorded in `/Logs`

---

## Guidelines

### File Naming Convention
- Use format: `YYYY-MM-DD_TaskDescription.md`
- Example: `2026-03-03_ReviewQuarterlyReport.md`

### Task File Template
```markdown
---
created: {{date}}
priority: high|medium|low
deadline: {{deadline}}
status: pending
---

# Task Title

## Description
[Describe the task]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Notes
[Any additional notes]
```

### Priority Levels
- **High**: Must be completed within 24 hours
- **Medium**: Complete within 1 week
- **Low**: Complete when capacity allows

---

## System Rules

1. **Automation First**: Let the watcher scripts handle file movements
2. **Log Everything**: All actions must be traceable via logs
3. **Single Source of Truth**: Dashboard.md reflects current state
4. **No Manual Overrides**: Don't bypass the automation system
5. **Regular Reviews**: Check pending tasks daily

---

## Escalation Procedures

If a task cannot be completed:
1. Add comment to task file explaining the blocker
2. Move task back to `/Needs_Action` if reprocessing needed
3. Log the issue in `/Logs` with details

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-03 | Initial Bronze-tier setup |

---

*For questions or modifications, refer to README.md*
