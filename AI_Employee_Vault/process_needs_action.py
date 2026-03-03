#!/usr/bin/env python3
"""
process_needs_action.py - Processes task files from /Needs_Action folder.

Responsibilities:
1. Reads new task files
2. Creates a plan in /Plans folder
3. Moves completed tasks to /Done folder
4. Updates Dashboard.md automatically

Compatible with Windows and WSL (Windows Subsystem for Linux).

FIXES APPLIED:
- Duplicate processing prevention with processed_files tracking
- File lock/permission error handling with retry logic
- Better error messages and logging
- Safe file operations with existence checks
"""

import os
import sys
import re
import shutil
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Set

# =============================================================================
# CONFIGURATION
# =============================================================================

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()

# Vault folder paths
VAULT_ROOT = SCRIPT_DIR
NEEDS_ACTION_FOLDER = VAULT_ROOT / "Needs_Action"
INBOX_FOLDER = VAULT_ROOT / "Inbox"
PLANS_FOLDER = VAULT_ROOT / "Plans"
DONE_FOLDER = VAULT_ROOT / "Done"
LOGS_FOLDER = VAULT_ROOT / "Logs"
DASHBOARD_FILE = VAULT_ROOT / "Dashboard.md"

# Ensure all folders exist
for folder in [PLANS_FOLDER, DONE_FOLDER, LOGS_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# Log file configuration
LOG_FILE = LOGS_FOLDER / f"processor_{datetime.now().strftime('%Y-%m-%d')}.log"

# Track processed files to avoid duplicates (stored in log for persistence)
PROCESSED_FILES_LOG = LOGS_FOLDER / "processed_files.log"

# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging():
    """
    Configure logging to write to both file and console.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# =============================================================================
# DUPLICATE PREVENTION
# =============================================================================

def get_processed_files() -> Set[str]:
    """
    Load the set of already processed files from the log.
    
    Returns:
        Set of filenames that have been processed
    """
    processed = set()
    if PROCESSED_FILES_LOG.exists():
        try:
            with open(PROCESSED_FILES_LOG, 'r', encoding='utf-8') as f:
                for line in f:
                    filename = line.strip()
                    if filename:
                        processed.add(filename)
        except Exception as e:
            logger.warning(f"Could not read processed files log: {e}")
    return processed

def mark_file_processed(filename: str):
    """
    Mark a file as processed by adding it to the log.
    
    Args:
        filename: Name of the file that was processed
    """
    try:
        with open(PROCESSED_FILES_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{filename}\n")
    except Exception as e:
        logger.error(f"Could not mark file as processed: {e}")

def is_file_already_processed(filename: str) -> bool:
    """
    Check if a file has already been processed.
    
    Args:
        filename: Name of the file to check
    
    Returns:
        True if file was already processed, False otherwise
    """
    processed = get_processed_files()
    return filename in processed

# =============================================================================
# FILE LOCK HANDLING
# =============================================================================

def safe_read_file(file_path: Path, max_retries: int = 3, retry_delay: float = 0.5) -> Optional[str]:
    """
    Safely read a file with retry logic for file lock handling.
    
    Args:
        file_path: Path to the file
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        File content if successful, None if failed
    """
    for attempt in range(max_retries):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except PermissionError as e:
            logger.warning(f"Permission denied (attempt {attempt + 1}/{max_retries}): {file_path.name}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        except OSError as e:
            # Handle file lock errors on Windows
            if "sharing violation" in str(e).lower() or "used by another process" in str(e).lower():
                logger.warning(f"File locked (attempt {attempt + 1}/{max_retries}): {file_path.name}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            else:
                logger.error(f"OS error reading file: {e}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error reading file: {e}")
            return None
    
    logger.error(f"Failed to read file after {max_retries} attempts: {file_path.name}")
    return None

def safe_move_file(src: Path, dst: Path, max_retries: int = 3, retry_delay: float = 0.5) -> bool:
    """
    Safely move a file with retry logic for file lock handling.
    
    Args:
        src: Source file path
        dst: Destination file path
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        True if successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            shutil.move(str(src), str(dst))
            return True
        except PermissionError as e:
            logger.warning(f"Permission denied moving file (attempt {attempt + 1}/{max_retries}): {src.name}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        except OSError as e:
            if "sharing violation" in str(e).lower() or "used by another process" in str(e).lower():
                logger.warning(f"File locked during move (attempt {attempt + 1}/{max_retries}): {src.name}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            else:
                logger.error(f"OS error moving file: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error moving file: {e}")
            return False
    
    logger.error(f"Failed to move file after {max_retries} attempts: {src.name}")
    return False

# =============================================================================
# TASK PARSING
# =============================================================================

def parse_task_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse a task file and extract metadata and content.
    
    Args:
        file_path: Path to the task file
    
    Returns:
        Dictionary containing task metadata and content
    """
    task_data = {
        'filename': file_path.name,
        'path': str(file_path),
        'title': file_path.stem,
        'created': datetime.now().isoformat(),
        'priority': 'medium',
        'deadline': None,
        'status': 'pending',
        'content': '',
        'requirements': [],
        'source_folder': file_path.parent.name
    }
    
    try:
        # Use safe read function with retry logic
        content = safe_read_file(file_path)
        
        if content is None:
            task_data['error'] = "Could not read file (may be locked or permission denied)"
            return task_data
        
        task_data['content'] = content
        
        # Extract frontmatter (YAML-like metadata between --- markers)
        frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            
            # Extract priority
            priority_match = re.search(r'priority:\s*(\w+)', frontmatter)
            if priority_match:
                task_data['priority'] = priority_match.group(1).lower()
            
            # Extract deadline
            deadline_match = re.search(r'deadline:\s*(.+)', frontmatter)
            if deadline_match:
                task_data['deadline'] = deadline_match.group(1).strip()
            
            # Extract status
            status_match = re.search(r'status:\s*(\w+)', frontmatter)
            if status_match:
                task_data['status'] = status_match.group(1).lower()
        
        # Extract title from first heading if available
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            task_data['title'] = title_match.group(1).strip()
        
        # Extract requirements (checkbox items)
        requirements = re.findall(r'- \[ \]\s+(.+)$', content, re.MULTILINE)
        task_data['requirements'] = requirements
        
        logger.info(f"Parsed task: {task_data['title']}")
        
    except Exception as e:
        logger.error(f"Error parsing task file {file_path}: {str(e)}")
        task_data['error'] = str(e)
    
    return task_data

# =============================================================================
# PLAN CREATION
# =============================================================================

def create_plan(task_data: Dict[str, Any]) -> Optional[Path]:
    """
    Create a plan file in the /Plans folder based on task data.
    
    Args:
        task_data: Dictionary containing parsed task information
    
    Returns:
        Path to the created plan file, or None if creation failed
    """
    try:
        # Generate plan filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plan_filename = f"Plan_{timestamp}_{task_data['filename']}"
        plan_path = PLANS_FOLDER / plan_filename
        
        # Create plan content
        plan_content = f"""---
created: {datetime.now().isoformat()}
source_task: {task_data['filename']}
priority: {task_data['priority']}
deadline: {task_data.get('deadline', 'N/A')}
status: in_progress
---

# Plan: {task_data['title']}

## Source Task
- **File**: {task_data['filename']}
- **Priority**: {task_data['priority']}
- **Deadline**: {task_data.get('deadline', 'N/A')}
- **Created**: {task_data['created']}

## Action Plan

### Step 1: Review Task Requirements
- [ ] Read and understand the task
- [ ] Identify required resources
- [ ] Estimate time needed

### Step 2: Execute Task
- [ ] Complete primary objective
- [ ] Document progress

### Step 3: Verify Completion
- [ ] Review completed work
- [ ] Ensure all requirements met
- [ ] Prepare for archival

## Original Task Content

{task_data['content']}

## Processing Log

- **Plan Created**: {datetime.now().isoformat()}
- **Processor**: process_needs_action.py

---
*This plan was automatically generated by the AI Employee system.*
"""
        
        # Write plan file
        with open(plan_path, 'w', encoding='utf-8') as f:
            f.write(plan_content)
        
        logger.info(f"Plan created: {plan_path.name}")
        return plan_path
        
    except Exception as e:
        logger.error(f"Error creating plan: {str(e)}")
        return None

# =============================================================================
# TASK COMPLETION
# =============================================================================

def mark_task_completed(task_path: Path, plan_path: Optional[Path] = None) -> bool:
    """
    Mark a task as completed by moving it to /Done folder.
    
    Args:
        task_path: Path to the task file
        plan_path: Optional path to the associated plan file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if source file exists before trying to move
        if not task_path.exists():
            logger.error(f"Source file does not exist: {task_path}")
            return False
        
        # Generate destination filename with completion timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest_filename = f"Done_{timestamp}_{task_path.name}"
        dest_path = DONE_FOLDER / dest_filename
        
        # Check if destination already exists (avoid overwriting)
        if dest_path.exists():
            # Add microseconds to make filename unique
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            dest_filename = f"Done_{timestamp}_{task_path.name}"
            dest_path = DONE_FOLDER / dest_filename
        
        # Use safe move function with retry logic
        success = safe_move_file(task_path, dest_path)
        
        if not success:
            logger.error(f"Failed to move task to Done: {task_path.name}")
            return False
        
        logger.info(f"Task moved to Done: {dest_filename}")
        
        # Also move the plan if it exists
        if plan_path and plan_path.exists():
            plan_dest = DONE_FOLDER / f"Done_{timestamp}_{plan_path.name}"
            plan_success = safe_move_file(plan_path, plan_dest)
            if plan_success:
                logger.info(f"Plan moved to Done: {plan_dest.name}")
            else:
                logger.warning(f"Failed to move plan: {plan_path.name}")
        
        # Log the completion
        log_completion(task_path.name, dest_filename)
        
        # Mark file as processed to avoid duplicates
        mark_file_processed(task_path.name)
        
        return True
        
    except Exception as e:
        logger.error(f"Error moving task to Done: {str(e)}")
        return False

def log_completion(original_file: str, done_file: str):
    """
    Log task completion to the logs folder.
    
    Args:
        original_file: Original filename
        done_file: New filename in Done folder
    """
    completion_log = LOGS_FOLDER / "completions.log"
    
    with open(completion_log, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} | COMPLETED | "
               f"{original_file} -> {done_file}\n")

# =============================================================================
# DASHBOARD UPDATE
# =============================================================================

def update_dashboard():
    """
    Update the Dashboard.md file with current statistics and recent activity.
    Uses complete rewrite to avoid duplicate sections.
    """
    try:
        logger.info("Updating Dashboard.md...")
        
        # Count files in each folder
        inbox_count = len(list(INBOX_FOLDER.glob("*.md")))
        needs_action_count = len(list(NEEDS_ACTION_FOLDER.glob("*.md")))
        plans_count = len(list(PLANS_FOLDER.glob("*.md")))
        done_count = len(list(DONE_FOLDER.glob("*.md")))
        
        # Get recent activity from logs
        recent_activity = get_recent_activity()
        
        # Get pending approvals (tasks in Needs_Action)
        pending_approvals = get_pending_approvals()
        
        # Get completed tasks (recent ones from Done folder)
        completed_tasks = get_completed_tasks()
        
        # Create complete dashboard content (rewrite to avoid duplicates)
        dashboard_content = f"""# AI Employee Dashboard

> **Status**: Active | **Tier**: Bronze | **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Recent Activity

{recent_activity}

---

## Pending Approvals

{pending_approvals}

---

## Completed Tasks

{completed_tasks}

---

## Notes

<!-- General notes and observations -->

- Dashboard auto-updates when tasks are processed
- Check `/Logs` folder for detailed activity logs
- New tasks should be added to `/Inbox` or `/Needs_Action`

---

## Quick Stats

| Metric | Count |
|--------|-------|
| Tasks in Inbox | {inbox_count} |
| Tasks Needing Action | {needs_action_count} |
| Plans in Progress | {plans_count} |
| Completed Tasks | {done_count} |

---

*This dashboard is automatically maintained by the AI Employee system.*
"""
        
        # Write updated dashboard (complete rewrite)
        with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
            f.write(dashboard_content)
        
        logger.info("Dashboard.md updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating dashboard: {str(e)}")

def get_recent_activity(limit: int = 5) -> str:
    """
    Get recent activity from logs.
    
    Args:
        limit: Maximum number of entries to return
    
    Returns:
        Formatted string of recent activity
    """
    activity_lines = []
    
    # Check detections log
    detections_log = LOGS_FOLDER / "detections.log"
    if detections_log.exists():
        with open(detections_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-limit:]
            for line in reversed(lines):
                parts = line.strip().split(' | ')
                if len(parts) >= 4:
                    timestamp = parts[0]
                    action = parts[2]
                    filename = parts[3]
                    activity_lines.append(f"- **{timestamp}**: {action} - {filename}")
    
    if not activity_lines:
        return "*No recent activity.*"
    
    return "\n".join(activity_lines)

def get_pending_approvals() -> str:
    """
    Get list of pending approvals from Needs_Action folder.
    
    Returns:
        Formatted string of pending approvals
    """
    pending = []
    
    for file_path in NEEDS_ACTION_FOLDER.glob("*.md"):
        pending.append(f"- `{file_path.name}`")
    
    if not pending:
        return "*No pending approvals.*"
    
    return "\n".join(pending)

def get_completed_tasks(limit: int = 5) -> str:
    """
    Get list of recently completed tasks from Done folder.
    
    Args:
        limit: Maximum number of entries to return
    
    Returns:
        Formatted string of completed tasks
    """
    completed = []
    
    # Get files sorted by modification time
    done_files = sorted(
        DONE_FOLDER.glob("*.md"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )[:limit]
    
    for file_path in done_files:
        completed.append(f"- `{file_path.name}`")
    
    if not completed:
        return "*No completed tasks yet.*"
    
    return "\n".join(completed)

def update_dashboard_section(content: str, section_header: str, new_content: str) -> str:
    """
    Update a specific section in the dashboard.
    
    Args:
        content: Current dashboard content
        section_header: Header of the section to update
        new_content: New content for the section
    
    Returns:
        Updated dashboard content
    """
    # Pattern to match section from header to next ## header or end of content
    # Use non-greedy match and handle multiple occurrences
    pattern = f'({re.escape(section_header)}\\n\\n)(.*?)(?=\\n## |\\n---|\\Z)'
    
    replacement = f'{section_header}\\n\\n{new_content}\\n'
    
    # Use re.DOTALL to match across lines, but only replace FIRST occurrence
    new_content_result = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
    
    return new_content_result

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_task(file_path: Path) -> bool:
    """
    Process a single task file.
    
    Args:
        file_path: Path to the task file
    
    Returns:
        True if processing was successful, False otherwise
    """
    logger.info("-" * 50)
    logger.info(f"Processing task: {file_path.name}")
    logger.info(f"Source: {file_path.parent.name}")
    
    # FIX #1: Check if file has already been processed (duplicate prevention)
    if is_file_already_processed(file_path.name):
        logger.info(f"SKIP: File already processed: {file_path.name}")
        logger.info("To reprocess, remove the filename from Logs/processed_files.log")
        return True  # Return True as it was already processed successfully
    
    # FIX #2: Check if file exists before processing
    if not file_path.exists():
        logger.error(f"ERROR: File does not exist: {file_path}")
        return False
    
    # Parse the task file
    task_data = parse_task_file(file_path)
    
    if 'error' in task_data and task_data['error']:
        logger.error(f"Failed to parse task: {task_data['error']}")
        return False
    
    # Create a plan
    plan_path = create_plan(task_data)
    
    if not plan_path:
        logger.error("Failed to create plan")
        return False
    
    logger.info(f"Task processed successfully: {task_data['title']}")
    
    # Move to Done folder (for Bronze tier, tasks are considered complete after planning)
    success = mark_task_completed(file_path, plan_path)
    
    if success:
        # FIX #3: Log success message clearly
        logger.info("=" * 50)
        logger.info(f"SUCCESS: {file_path.name} processed and moved to Done/")
        logger.info("=" * 50)
        
        # Update dashboard
        update_dashboard()
    else:
        logger.error(f"FAILED: Could not move {file_path.name} to Done folder")
    
    return success

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AI Employee Task Processor")
    logger.info("=" * 60)
    
    # Check if file path was provided as argument
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            sys.exit(1)
        
        success = process_task(file_path)
        sys.exit(0 if success else 1)
    
    else:
        # No file specified - process all files in Needs_Action folder
        logger.info("No file specified. Processing all files in Needs_Action folder...")
        
        processed_count = 0
        for file_path in NEEDS_ACTION_FOLDER.glob("*.md"):
            if process_task(file_path):
                processed_count += 1
        
        logger.info(f"Processed {processed_count} task(s)")
        
        # Also process Inbox files
        logger.info("Checking Inbox folder...")
        for file_path in INBOX_FOLDER.glob("*.md"):
            if process_task(file_path):
                processed_count += 1
        
        logger.info(f"Total processed: {processed_count} task(s)")
        
        # Update dashboard
        update_dashboard()
    
    logger.info("Processing complete.")
