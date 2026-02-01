import json
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any
from pathlib import Path

import json
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any
from pathlib import Path

class CBridge:
    """Bridge to C components"""
    
    def __init__(self):
        base_path = Path(__file__).parent.parent
        build_dir = base_path / "build"
        
        # Create build directory if it doesn't exist
        build_dir.mkdir(exist_ok=True)
        
        self.c_bridge_path = build_dir / "py_bridge"
        self.monitor_path = build_dir / "system_monitor"
        
        # Check if binaries exist
        if not self.c_bridge_path.exists():
            print(f"Warning: C bridge binary not found at {self.c_bridge_path}")
        
        if not self.monitor_path.exists():
            print(f"Warning: System monitor binary not found at {self.monitor_path}")
        
        return None
    
    def get_system_stats(self) -> Optional[Dict[str, Any]]:
        """Get system stats from C monitor"""
        try:
            result = subprocess.run(
                [str(self.monitor_path)],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout.strip())
        except Exception as e:
            print(f"Monitor error: {e}")
        
        return None
    
    def start_hotkey_daemon(self) -> bool:
        """Start the hotkey daemon"""
        hotkey_path = Path(__file__).parent.parent / "build" / "hotkey_daemon"
        
        try:
            # Start in background
            subprocess.Popen(
                [str(hotkey_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return True
        except Exception as e:
            print(f"Hotkey daemon error: {e}")
            return False