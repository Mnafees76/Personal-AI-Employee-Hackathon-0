# AI Employee Vault - Bronze Tier

A Personal AI Employee system built for Obsidian that automates task management through file-based workflows.

---

## Table of Contents

- [Overview](#overview)
- [Folder Structure](#folder-structure)
- [Quick Start](#quick-start)
- [Setup Instructions](#setup-instructions)
- [Running the Watchers](#running-the-watchers)
- [Adding New Tasks](#adding-new-tasks)
- [Dashboard Updates](#dashboard-updates)
- [WSL Compatibility](#wsl-compatibility)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Bronze-tier AI Employee is an automated task management system that:

- **Monitors** folders for new task files
- **Processes** tasks automatically
- **Creates** action plans
- **Tracks** completion status
- **Updates** a central dashboard

### Features

| Feature | Status |
|---------|--------|
| File System Watching | ✅ |
| Automatic Task Processing | ✅ |
| Plan Generation | ✅ |
| Dashboard Auto-Update | ✅ |
| Logging | ✅ |
| Windows Support | ✅ |
| WSL Support | ✅ |

---

## Folder Structure

```
AI_Employee_Vault/
├── .obsidian/              # Obsidian configuration
├── Done/                   # Completed tasks archive
├── Inbox/                  # New incoming tasks
├── Logs/                   # System activity logs
├── Needs_Action/           # Tasks requiring processing
├── Plans/                  # Task plans and strategies
├── Skills/                 # AI capability documentation
├── Company_Handbook.md     # Rules and guidelines
├── Dashboard.md            # Main status dashboard
├── filesystem_watcher.py   # Folder monitoring script
├── process_needs_action.py # Task processing script
└── README.md               # This file
```

---

## Quick Start

### Windows (PowerShell/CMD)

```powershell
# 1. Navigate to the vault
cd "C:\path\to\AI_Employee_Vault"

# 2. Install dependencies
pip install watchdog

# 3. Start the watcher
python filesystem_watcher.py
```

### WSL (Windows Subsystem for Linux)

```bash
# 1. Navigate to the vault
cd /mnt/c/path/to/AI_Employee_Vault

# 2. Install dependencies
pip install watchdog

# 3. Start the watcher
python3 filesystem_watcher.py
```

---

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Obsidian (optional, for viewing markdown files)

### Step 1: Verify Python Installation

**Windows:**
```powershell
python --version
```

**WSL:**
```bash
python3 --version
```

If Python is not installed, download from [python.org](https://www.python.org/downloads/).

### Step 2: Install Dependencies

The system requires the `watchdog` library for file system monitoring.

**Windows:**
```powershell
pip install watchdog
```

**WSL:**
```bash
pip3 install watchdog
```

### Step 3: Verify Folder Structure

Ensure all required folders exist:

```
AI_Employee_Vault/
├── Done/
├── Inbox/
├── Logs/
├── Needs_Action/
├── Plans/
└── Skills/
```

If any folders are missing, create them:

**Windows:**
```powershell
mkdir Done, Inbox, Logs, Needs_Action, Plans, Skills
```

**WSL:**
```bash
mkdir -p Done Inbox Logs Needs_Action Plans Skills
```

### Step 4: Open in Obsidian (Optional)

1. Open Obsidian
2. Click "Open folder as vault"
3. Select the `AI_Employee_Vault` folder

---

## Running the Watchers

### Start the File System Watcher

The watcher monitors `/Needs_Action` and `/Inbox` folders for new files.

**Windows:**
```powershell
python filesystem_watcher.py
```

**WSL:**
```bash
python3 filesystem_watcher.py
```

### Running in Background

**Windows (PowerShell):**
```powershell
Start-Process python -ArgumentList "filesystem_watcher.py" -WindowStyle Hidden
```

**WSL:**
```bash
nohup python3 filesystem_watcher.py > /dev/null 2>&1 &
```

### Stop the Watcher

Press `Ctrl+C` in the terminal to stop the watcher.

### Verify Watcher is Running

Check the logs folder for recent activity:

**Windows:**
```powershell
Get-Content Logs\watcher_*.log -Tail 20
```

**WSL:**
```bash
tail -20 Logs/watcher_*.log
```

---

## Adding New Tasks

### Method 1: Create File in Inbox

1. Create a new markdown file in the `/Inbox` folder
2. Use the task template below
3. The watcher will automatically process it

### Method 2: Create File in Needs_Action

1. Create a new markdown file in the `/Needs_Action` folder
2. The watcher will detect and process it immediately

### Task File Template

```markdown
---
created: 2026-03-03
priority: high
deadline: 2026-03-10
status: pending
---

# Task Title

## Description
Describe what needs to be done.

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## Notes
Any additional information or context.
```

### Priority Levels

| Priority | Response Time |
|----------|---------------|
| high | Within 24 hours |
| medium | Within 1 week |
| low | When capacity allows |

### Example Task File

Create `2026-03-03_ReviewQuarterlyReport.md` in `/Inbox`:

```markdown
---
created: 2026-03-03
priority: high
deadline: 2026-03-05
status: pending
---

# Review Quarterly Report

## Description
Review and approve the Q1 2026 financial report.

## Requirements
- [ ] Read full report
- [ ] Check all figures
- [ ] Add comments
- [ ] Send approval email

## Notes
Report is located in /Documents/Q1_2026_Report.pdf
```

---

## Dashboard Updates

The `Dashboard.md` file is automatically updated when:

- New tasks are detected
- Tasks are processed
- Plans are created
- Tasks are completed

### Manual Dashboard Refresh

If you need to manually refresh the dashboard:

**Windows:**
```powershell
python process_needs_action.py
```

**WSL:**
```bash
python3 process_needs_action.py
```

### Dashboard Sections

| Section | Description |
|---------|-------------|
| Recent Activity | Log of recent system actions |
| Pending Approvals | Tasks awaiting processing |
| Completed Tasks | Recently finished tasks |
| Quick Stats | Current task counts |

---

## WSL Compatibility

### Running on WSL

The AI Employee system is fully compatible with WSL (Windows Subsystem for Linux).

### Accessing Windows Files from WSL

Windows files are accessible under `/mnt/`:

```bash
cd /mnt/c/Users/ADMIN/Documents/GitHub/Personal\ AI\ Employee\ Hackathon\ 0/AI_Employee_Vault
```

### WSL-Specific Commands

```bash
# Install Python (if not installed)
sudo apt update && sudo apt install python3 python3-pip

# Install watchdog
pip3 install watchdog

# Run the watcher
python3 filesystem_watcher.py

# Run in background
nohup python3 filesystem_watcher.py &

# Check running processes
ps aux | grep filesystem_watcher

# Stop the watcher
pkill -f filesystem_watcher
```

### WSL Path Conversion

| Windows Path | WSL Path |
|--------------|----------|
| `C:\Users\ADMIN\...` | `/mnt/c/Users/ADMIN/...` |
| `D:\Projects\...` | `/mnt/d/Projects/...` |

### Running from Windows but Editing in WSL

You can run the watcher from Windows while editing files from WSL (or vice versa) since both access the same file system.

---

## Troubleshooting

### Watcher Not Starting

**Problem:** `python: command not found`

**Solution:** Ensure Python is installed and in your PATH.

**Windows:**
```powershell
# Check Python installation
python --version

# If not found, add to PATH or reinstall Python
```

**WSL:**
```bash
# Install Python
sudo apt install python3 python3-pip
```

### Module Not Found: watchdog

**Problem:** `ModuleNotFoundError: No module named 'watchdog'`

**Solution:**
```powershell
pip install watchdog
```

### Files Not Being Processed

**Problem:** Files in `/Needs_Action` are not being processed.

**Solutions:**
1. Ensure the watcher is running
2. Check file extension is `.md`
3. Verify file permissions
4. Check logs for errors: `Logs/watcher_*.log`

### Dashboard Not Updating

**Problem:** Dashboard.md is not being updated.

**Solutions:**
1. Run the processor manually: `python process_needs_action.py`
2. Check write permissions on Dashboard.md
3. Verify the script completed without errors

### Logs Location

All logs are stored in the `/Logs` folder:

| Log File | Description |
|----------|-------------|
| `watcher_YYYY-MM-DD.log` | Daily watcher logs |
| `processor_YYYY-MM-DD.log` | Daily processor logs |
| `detections.log` | File detection history |
| `completions.log` | Task completion history |

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Permission denied` | File locked or no write access | Close file in other programs |
| `File not found` | Path incorrect | Verify file exists |
| `Timeout` | Processing took too long | Check task complexity |

---

## Support

For issues or questions:

1. Check the logs in `/Logs` folder
2. Review `Company_Handbook.md` for guidelines
3. Verify folder structure is intact

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-03 | Initial Bronze-tier release |

---

*Built for the Personal AI Employee Hackathon*
