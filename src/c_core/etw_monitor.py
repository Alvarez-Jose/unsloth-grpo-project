"""
ETW Event Monitor - Captures Windows system events in real-time

This module monitors:
- File system operations (create, read, write, delete)
- Process creation and termination
- Registry modifications
- Network connections

Events are analyzed to predict user intent and trigger agent activation.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any  # Added 'Any' here
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from queue import Queue
import logging
import time

try:
    import psutil
except ImportError:
    print("Error: psutil not installed. Run: pip install psutil")
    exit(1)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    print("Warning: watchdog not installed. File monitoring disabled.")
    print("Run: pip install watchdog")
    WATCHDOG_AVAILABLE = False

from loguru import logger


# FIXED: Only ONE SystemEvent class definition - using dataclass
@dataclass
class SystemEvent:
    """Represents a captured system event"""
    timestamp: str
    event_type: str  # file, process, registry, network
    source: str
    operation: str  # create, read, write, delete, execute
    target: str
    process_name: str
    user: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def is_developer_activity(self) -> bool:
        """Heuristic to detect developer-related activities"""
        dev_indicators = [
            'visual studio', 'vscode', 'code.exe', 'devenv.exe',
            'git.exe', 'python.exe', 'node.exe', 'cargo.exe',
            '.cpp', '.py', '.js', '.rs', '.go', '.java'
        ]
        target_lower = self.target.lower()
        process_lower = self.process_name.lower()
        
        return any(ind in target_lower or ind in process_lower 
                   for ind in dev_indicators)
    
    def is_debugging_session(self) -> bool:
        """Detect if this looks like a debugging session start"""
        debug_indicators = [
            'devenv.exe', 'vshost.exe', 'debug', '.pdb', 
            'windbg.exe', 'gdb.exe', 'lldb.exe'
        ]
        return any(ind in self.process_name.lower() or ind in self.target.lower()
                   for ind in debug_indicators)


class FileEventHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(self, event_callback: Callable[[SystemEvent], None]):
        self.event_callback = event_callback
        super().__init__()
    
    def on_created(self, event):
        if not event.is_directory:
            self._create_event("create", event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self._create_event("write", event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._create_event("delete", event.src_path)
    
    def _create_event(self, operation: str, path: str):
        """Create a SystemEvent from file system event"""
        event = SystemEvent(
            timestamp=datetime.now().isoformat(),
            event_type="file",
            source="watchdog",
            operation=operation,
            target=path,
            process_name="explorer.exe",  # We can't easily get the actual process
            user="current_user",
            metadata={'path': path}
        )
        
        if self.event_callback:
            self.event_callback(event)


class ETWEventMonitor:
    """  
    Captures system events and provides them to the agent system
    for context-aware predictions.
    """
    
    def __init__(self, event_callback: Optional[Callable[[SystemEvent], None]] = None):
        """
        Args:
            event_callback: Function called when interesting events detected
        """
        self.event_callback = event_callback
        self.event_queue = Queue(maxsize=10000)
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # File system monitoring
        self.file_observer = None
        self.watch_paths = [
            str(Path.home() / "Desktop"),
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
        ]
        
        # Pattern detection
        self.recent_events: List[SystemEvent] = []
        self.max_recent_events = 100
        
        logger.info("ETW Event Monitor initialized")
    
    def start(self):
        """Start monitoring system events"""
        if self.is_running:
            logger.warning("Monitor already running")
            return
        
        self.is_running = True
        
        # Start process monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start file system monitoring if available
        if WATCHDOG_AVAILABLE:
            try:
                self.file_observer = Observer()
                handler = FileEventHandler(self._on_file_event)
                
                for path in self.watch_paths:
                    if Path(path).exists():
                        self.file_observer.schedule(handler, path, recursive=True)
                        logger.info(f"Watching: {path}")
                
                self.file_observer.start()
            except Exception as e:
                logger.warning(f"Could not start file monitoring: {e}")
        
        logger.info("ETW monitoring started")
    
    def _on_file_event(self, event: SystemEvent):
        """Callback for file system events"""
        if self._is_interesting(event):
            self._process_event(event)
    
    def stop(self):
        """Stop monitoring"""
        logger.info("Stopping AgentOS...")
        
        self.is_running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
        
        logger.info("ETW monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop - runs in separate thread"""
        import psutil
        import time
        
        logger.info("Starting real-time process monitoring...")
        
        # Track seen processes to detect new ones
        seen_pids = set(p.pid for p in psutil.process_iter(['pid']))
        
        while self.is_running:
            try:
                # Check for new processes
                current_pids = set(p.pid for p in psutil.process_iter(['pid']))
                new_pids = current_pids - seen_pids
                
                for pid in new_pids:
                    try:
                        proc = psutil.Process(pid)
                        # Create synthetic event for new process
                        event = SystemEvent(
                            timestamp=datetime.now().isoformat(),
                            event_type="process",
                            source="psutil",
                            operation="execute",
                            target=proc.exe() if proc.exe() else "unknown",
                            process_name=proc.name(),
                            user=proc.username() if proc.username() else "unknown",
                            metadata={'pid': pid}
                        )
                        
                        if self._is_interesting(event):
                            self._process_event(event)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                seen_pids = current_pids
                
            except Exception as e:
                logger.debug(f"Monitor loop error: {e}")
            
            # Small sleep to prevent CPU spinning
            time.sleep(0.5)
    
    def _is_interesting(self, event: SystemEvent) -> bool:
        """Filter out noise - only keep interesting events"""
        # Ignore system processes
        system_processes = ['svchost.exe', 'system', 'registry', 'smss.exe']
        if any(proc in event.process_name.lower() for proc in system_processes):
            return False
        
        # Ignore temp files
        if 'temp' in event.target.lower() or 'tmp' in event.target.lower():
            return False
        
        # Focus on developer activities
        return event.is_developer_activity() or event.is_debugging_session()
    
    def _process_event(self, event: SystemEvent):
        """Process an interesting event"""
        # Add to recent events
        self.recent_events.append(event)
        if len(self.recent_events) > self.max_recent_events:
            self.recent_events.pop(0)
        
        # Add to queue
        try:
            self.event_queue.put_nowait(event)
        except:
            logger.warning("Event queue full, dropping event")
        
        # Call callback if provided
        if self.event_callback:
            try:
                self.event_callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
        
        # Log interesting patterns
        if event.is_debugging_session():
            logger.info(f" Debugging session detected: {event.process_name}")
        
        logger.debug(f"Event: {event.event_type} - {event.operation} - {event.target}")
    
    def get_recent_events(self, count: int = 50) -> List[SystemEvent]:
        """Get recent events for pattern analysis"""
        return self.recent_events[-count:]
    
    def detect_pattern(self, pattern_name: str) -> bool:
        """
        Detect specific behavioral patterns from recent events
        """
        recent = self.get_recent_events(20)
        
        if pattern_name == 'debugging_session':
            # Pattern: IDE opened + debugger attached + looking at source files
            has_ide = any(e.is_debugging_session() for e in recent)
            has_source_files = any('.cpp' in e.target or '.py' in e.target 
                                   for e in recent)
            return has_ide and has_source_files
        
        elif pattern_name == 'code_review':
            # Pattern: Opening multiple source files quickly
            source_opens = [e for e in recent if any(ext in e.target 
                           for ext in ['.cpp', '.py', '.js', '.rs'])]
            return len(source_opens) >= 3
        
        elif pattern_name == 'documentation_search':
            # Pattern: Browser opens + searching docs
            has_browser = any('chrome' in e.process_name.lower() or 
                            'firefox' in e.process_name.lower() 
                            for e in recent)
            return has_browser  # Simplified for now
        
        return False


# FIXED: Proper async example usage
async def example_main():
    """Example usage with proper async/await"""
    
    def on_interesting_event(event: SystemEvent):
        """Callback when interesting events detected"""
        print(f"\n Interesting Event Detected!")
        print(f"   Type: {event.event_type}")
        print(f"   Operation: {event.operation}")
        print(f"   Target: {event.target}")
        print(f"   Process: {event.process_name}")
    
    # Create monitor
    monitor = ETWEventMonitor(event_callback=on_interesting_event)
    
    print(" Starting ETW Event Monitor...")
    print(" Monitoring for developer activities...")
    print("Press Ctrl+C to stop\n")
    
    try:
        monitor.start()
        
        # Keep running and check for patterns
        while True:
            await asyncio.sleep(5)  # FIXED: Use await
            
            # Example pattern detection
            if monitor.detect_pattern('debugging_session'):
                print("\nPATTERN DETECTED: Debugging session started!")
                print("   → Agent suggestion: Load recent crash logs")
                print("   → Agent suggestion: Prepare relevant documentation")
            
            if monitor.detect_pattern('code_review'):
                print("\n PATTERN DETECTED: Code review in progress!")
                print("   → Agent suggestion: Show git blame info")
                print("   → Agent suggestion: Load related test files")
    
    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
        monitor.stop()
        print("Monitor stopped. Goodbye!")


# Example usage / testing
if __name__ == "__main__":
    asyncio.run(example_main())