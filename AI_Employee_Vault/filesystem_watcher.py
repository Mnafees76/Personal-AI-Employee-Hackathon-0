#!/usr/bin/env python3
"""
filesystem_watcher.py - Monitors /Needs_Action and /Inbox folders for new files.

When a new file is detected:
1. Logs the detection in /Logs folder
2. Triggers process_needs_action.py to handle the task

Compatible with Windows and WSL (Windows Subsystem for Linux).
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# =============================================================================
# CONFIGURATION
# =============================================================================

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()

# Vault folder paths
VAULT_ROOT = SCRIPT_DIR
NEEDS_ACTION_FOLDER = VAULT_ROOT / "Needs_Action"
INBOX_FOLDER = VAULT_ROOT / "Inbox"
LOGS_FOLDER = VAULT_ROOT / "Logs"

# Ensure logs folder exists
LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

# Log file configuration
LOG_FILE = LOGS_FOLDER / f"watcher_{datetime.now().strftime('%Y-%m-%d')}.log"

# Process script path
PROCESS_SCRIPT = VAULT_ROOT / "process_needs_action.py"

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
# EVENT HANDLER
# =============================================================================

class TaskFileHandler(FileSystemEventHandler):
    """
    Handles file system events for task files.
    
    Triggers processing when new .md files are created or modified.
    """
    
    def __init__(self, folder_name: str):
        """
        Initialize the handler with folder name for logging.
        
        Args:
            folder_name: Name of the folder being monitored (for log messages)
        """
        super().__init__()
        self.folder_name = folder_name
        self.processed_files = set()  # Track processed files to avoid duplicates
    
    def on_created(self, event):
        """
        Handle file creation events.
        
        Args:
            event: FileSystemEvent object containing event details
        """
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only process markdown files
        if file_path.suffix.lower() != '.md':
            logger.debug(f"Ignoring non-markdown file: {file_path.name}")
            return
        
        # Avoid processing the same file multiple times
        if str(file_path) in self.processed_files:
            logger.debug(f"File already processed: {file_path.name}")
            return
        
        self.processed_files.add(str(file_path))
        self._process_file(file_path)
    
    def on_modified(self, event):
        """
        Handle file modification events.
        
        Args:
            event: FileSystemEvent object containing event details
        """
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only process markdown files
        if file_path.suffix.lower() != '.md':
            return
        
        # For modifications, re-process the file
        logger.info(f"File modified: {file_path.name}")
        self._process_file(file_path)
    
    def _process_file(self, file_path: Path):
        """
        Process a detected file by logging and triggering the processor script.
        
        Args:
            file_path: Path to the file to process
        """
        logger.info(f"[{self.folder_name}] New file detected: {file_path.name}")
        
        # Log the detection
        self._log_detection(file_path)
        
        # Trigger the processing script
        self._trigger_processor(file_path)
    
    def _log_detection(self, file_path: Path):
        """
        Log the file detection to the logs folder.
        
        Args:
            file_path: Path to the detected file
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'FILE_DETECTED',
            'folder': self.folder_name,
            'file': file_path.name,
            'path': str(file_path)
        }
        
        # Write to detailed log file
        detailed_log = LOGS_FOLDER / "detections.log"
        with open(detailed_log, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry['timestamp']} | {log_entry['action']} | "
                   f"{log_entry['folder']} | {log_entry['file']}\n")
        
        logger.info(f"Logged detection: {file_path.name}")
    
    def _trigger_processor(self, file_path: Path):
        """
        Trigger the process_needs_action.py script to handle the file.
        
        Args:
            file_path: Path to the file to process
        """
        try:
            # Run the processor script with the file path as argument
            cmd = [sys.executable, str(PROCESS_SCRIPT), str(file_path)]
            
            logger.info(f"Triggering processor for: {file_path.name}")
            
            # Use subprocess to run the script
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully processed: {file_path.name}")
                if result.stdout:
                    logger.debug(f"Processor output: {result.stdout}")
            else:
                logger.error(f"Processor failed for {file_path.name}: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"Processing timeout for: {file_path.name}")
        except FileNotFoundError:
            logger.error(f"Processor script not found: {PROCESS_SCRIPT}")
        except Exception as e:
            logger.error(f"Error triggering processor: {str(e)}")

# =============================================================================
# WATCHER FUNCTIONS
# =============================================================================

def create_observer(folder_path: Path, folder_name: str) -> tuple:
    """
    Create an observer for a specific folder.
    
    Args:
        folder_path: Path to the folder to monitor
        folder_name: Name of the folder (for logging)
    
    Returns:
        Tuple of (Observer, folder_path)
    """
    observer = Observer()
    event_handler = TaskFileHandler(folder_name)
    observer.schedule(event_handler, str(folder_path), recursive=False)
    return observer, folder_path

def start_watchers():
    """
    Start monitoring all relevant folders.
    
    Monitors /Needs_Action and /Inbox for new files.
    """
    logger.info("=" * 60)
    logger.info("Starting AI Employee File System Watcher")
    logger.info("=" * 60)
    logger.info(f"Vault Root: {VAULT_ROOT}")
    logger.info(f"Monitoring: {NEEDS_ACTION_FOLDER}, {INBOX_FOLDER}")
    logger.info(f"Log File: {LOG_FILE}")
    logger.info("=" * 60)
    
    # Create observers for each folder
    observers = []
    
    # Monitor Needs_Action folder
    if NEEDS_ACTION_FOLDER.exists():
        observer, path = create_observer(NEEDS_ACTION_FOLDER, "Needs_Action")
        observer.start()
        observers.append((observer, path))
        logger.info(f"Started watcher: {path}")
    else:
        logger.warning(f"Folder not found: {NEEDS_ACTION_FOLDER}")
    
    # Monitor Inbox folder
    if INBOX_FOLDER.exists():
        observer, path = create_observer(INBOX_FOLDER, "Inbox")
        observer.start()
        observers.append((observer, path))
        logger.info(f"Started watcher: {path}")
    else:
        logger.warning(f"Folder not found: {INBOX_FOLDER}")
    
    logger.info("All watchers started. Press Ctrl+C to stop.")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watchers...")
        for observer, path in observers:
            observer.stop()
            logger.info(f"Stopped watcher: {path}")
        
        # Wait for observers to finish
        for observer, _ in observers:
            observer.join()
        
        logger.info("All watchers stopped. Goodbye!")

# =============================================================================
# INITIAL PROCESSING (catch-up on existing files)
# =============================================================================

def process_existing_files():
    """
    Process any existing files in the monitored folders on startup.
    
    This ensures no files are missed if the watcher was stopped.
    """
    logger.info("Checking for existing files to process...")
    
    for folder, folder_name in [(NEEDS_ACTION_FOLDER, "Needs_Action"), 
                                  (INBOX_FOLDER, "Inbox")]:
        if not folder.exists():
            continue
            
        for file_path in folder.glob("*.md"):
            logger.info(f"Found existing file: {file_path.name}")
            handler = TaskFileHandler(folder_name)
            handler._process_file(file_path)

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Process any existing files first
    process_existing_files()
    
    # Start the watchers
    start_watchers()
