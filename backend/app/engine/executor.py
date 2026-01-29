"""
Script execution engine for running security detection scripts.
"""
import os
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ScriptExecutor:
    """
    Executes security detection scripts in a controlled environment.
    """
    
    def __init__(
        self,
        timeout: int = None,
        max_memory_mb: int = None,
    ):
        self.timeout = timeout or settings.SCRIPT_TIMEOUT_SECONDS
        self.max_memory_mb = max_memory_mb or settings.SCRIPT_MAX_MEMORY_MB
        self.scripts_dir = Path(settings.SCRIPTS_DIR)
        self.logs_dir = Path(settings.LOGS_DIR)
        
        # Ensure directories exist
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(
        self,
        script_path: str,
        target_ip: str,
        task_id: int,
        result_id: int,
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Execute a detection script.
        
        Args:
            script_path: Relative path to the script
            target_ip: Target IP address
            task_id: Task ID for logging
            result_id: Result ID for logging
            
        Returns:
            Tuple of (status, error_message, log_path)
            status: 'pass', 'fail', or 'error'
        """
        full_script_path = self.scripts_dir / script_path
        
        # Validate script exists
        if not full_script_path.exists():
            logger.error(f"Script not found: {full_script_path}")
            return "error", f"Script not found: {script_path}", None
        
        # Create log file
        log_filename = f"task_{task_id}_result_{result_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
        log_path = self.logs_dir / log_filename
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env["TARGET_IP"] = target_ip
            env["TASK_ID"] = str(task_id)
            env["RESULT_ID"] = str(result_id)
            
            # Determine script type and command
            script_ext = full_script_path.suffix.lower()
            if script_ext == ".py":
                cmd = ["python3", str(full_script_path)]
            elif script_ext == ".sh":
                cmd = ["bash", str(full_script_path)]
            else:
                return "error", f"Unsupported script type: {script_ext}", None
            
            # Add target IP as argument
            cmd.append(target_ip)
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            # Execute script
            with open(log_path, "w") as log_file:
                log_file.write(f"=== Script Execution Log ===\n")
                log_file.write(f"Script: {script_path}\n")
                log_file.write(f"Target: {target_ip}\n")
                log_file.write(f"Task ID: {task_id}\n")
                log_file.write(f"Result ID: {result_id}\n")
                log_file.write(f"Start Time: {datetime.utcnow().isoformat()}\n")
                log_file.write(f"{'=' * 40}\n\n")
                log_file.flush()
                
                start_time = time.time()
                
                process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    env=env,
                    cwd=str(self.scripts_dir),
                )
                
                try:
                    return_code = process.wait(timeout=self.timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    log_file.write(f"\n\n=== TIMEOUT after {self.timeout}s ===\n")
                    return "error", f"Script timeout after {self.timeout}s", str(log_path)
                
                elapsed = time.time() - start_time
                log_file.write(f"\n\n{'=' * 40}\n")
                log_file.write(f"End Time: {datetime.utcnow().isoformat()}\n")
                log_file.write(f"Elapsed: {elapsed:.2f}s\n")
                log_file.write(f"Return Code: {return_code}\n")
            
            # Interpret return code
            # Convention: 0 = pass, 1 = fail (vulnerability found), other = error
            if return_code == 0:
                return "pass", None, str(log_path)
            elif return_code == 1:
                return "fail", None, str(log_path)
            else:
                return "error", f"Script exited with code {return_code}", str(log_path)
                
        except Exception as e:
            logger.exception(f"Script execution failed: {e}")
            return "error", str(e), str(log_path) if log_path.exists() else None
    
    def validate_script(self, script_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a script before execution.
        
        Args:
            script_path: Relative path to the script
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        full_path = self.scripts_dir / script_path
        
        if not full_path.exists():
            return False, "Script file not found"
        
        if not full_path.is_file():
            return False, "Path is not a file"
        
        # Check file extension
        allowed_extensions = {".py", ".sh"}
        if full_path.suffix.lower() not in allowed_extensions:
            return False, f"Invalid script type. Allowed: {allowed_extensions}"
        
        # Check file is readable
        if not os.access(full_path, os.R_OK):
            return False, "Script file is not readable"
        
        return True, None
