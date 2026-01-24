"""
Expert Agents - Specialized models for specific tasks

Each expert is a domain-specific model (3-7B parameters) that excels
at particular types of tasks. Experts share knowledge through the
episodic memory layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time
from pathlib import Path

from loguru import logger
from etw_monitor import SystemEvent


@dataclass
class ExpertResponse:
    """Response from an expert agent"""
    success: bool
    response: str
    actions_taken: List[str]
    confidence: float
    execution_time: float
    metadata: Dict[str, Any]


class ExpertAgent(ABC):
    """
    Base class for all expert agents
    
    Each expert:
    - Specializes in a specific domain
    - Can read/write to episodic memory
    - Reports execution metrics
    - Learns from outcomes
    """
    
    def __init__(self, name: str, model_path: Optional[str] = None):
        self.name = name
        self.model_path = model_path
        self.model = None
        self.execution_count = 0
        self.total_time = 0.0
        
        logger.info(f"Initializing {name} expert")
    
    @abstractmethod
    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        system_events: List[SystemEvent]
    ) -> ExpertResponse:
        """
        Execute the expert's specialized task
        
        Args:
            task: The task to perform
            context: Additional context (from memory, user prefs, etc.)
            system_events: Recent system events for context
        
        Returns:
            ExpertResponse with results
        """
        pass
    
    @abstractmethod
    def can_handle(self, task: str, context: Dict) -> float:
        """
        Determine if this expert can handle the task
        
        Returns:
            Confidence score 0.0-1.0
        """
        pass
    
    def _update_metrics(self, execution_time: float):
        """Update execution metrics"""
        self.execution_count += 1
        self.total_time += execution_time
    
    def get_stats(self) -> Dict:
        """Get expert statistics"""
        avg_time = self.total_time / self.execution_count if self.execution_count > 0 else 0
        return {
            'name': self.name,
            'executions': self.execution_count,
            'total_time': self.total_time,
            'avg_time_ms': avg_time * 1000
        }


class DebuggingExpert(ExpertAgent):
    """
    Debugging Expert - Specializes in:
    - Analyzing crash logs
    - Interpreting stack traces
    - Suggesting fixes for common bugs
    - Loading relevant documentation
    """
    
    def __init__(self, model_path: Optional[str] = None):
        super().__init__("DebuggingExpert", model_path)
        self.crash_patterns = self._load_crash_patterns()
    
    def _load_crash_patterns(self) -> Dict[str, str]:
        """Load common crash patterns and solutions"""
        return {
            'null_pointer': {
                'pattern': ['null', 'nullptr', '0x00000000', 'access violation'],
                'suggestion': 'Check for null pointer dereference. Add null checks before accessing objects.'
            },
            'stack_overflow': {
                'pattern': ['stack overflow', 'stackoverflow', 'recursion'],
                'suggestion': 'Likely infinite recursion. Check recursive functions for base case.'
            },
            'memory_leak': {
                'pattern': ['memory leak', 'heap corruption', 'out of memory'],
                'suggestion': 'Check for unreleased memory. Verify delete/free calls match new/malloc.'
            },
            'race_condition': {
                'pattern': ['race condition', 'deadlock', 'thread'],
                'suggestion': 'Potential threading issue. Check mutex locks and shared resource access.'
            },
            'array_bounds': {
                'pattern': ['array', 'out of bounds', 'index', 'buffer overflow'],
                'suggestion': 'Array index out of bounds. Verify loop conditions and array access.'
            }
        }
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        system_events: List[SystemEvent]
    ) -> ExpertResponse:
        """Execute debugging task"""
        start_time = time.time()
        
        logger.info(f"🔍 Debugging Expert executing: {task[:100]}...")
        
        actions_taken = []
        response_parts = []
        
        # 1. Analyze recent system events for debugging context
        debug_events = [e for e in system_events if e.is_debugging_session()]
        if debug_events:
            actions_taken.append("Analyzed recent debugging session events")
            response_parts.append(
                f"📊 Detected {len(debug_events)} debugging-related events."
            )
        
        # 2. Look for crash logs in recent file access
        crash_logs = [e for e in system_events 
                      if any(term in e.target.lower() 
                            for term in ['crash', 'error', 'exception', '.log', '.dmp'])]
        
        if crash_logs:
            actions_taken.append(f"Found {len(crash_logs)} potential crash logs")
            recent_log = crash_logs[-1]
            response_parts.append(
                f"📝 Found crash log: {Path(recent_log.target).name}"
            )
        
        # 3. Pattern matching on task description
        detected_issues = []
        for issue_type, pattern_info in self.crash_patterns.items():
            if any(pattern in task.lower() for pattern in pattern_info['pattern']):
                detected_issues.append((issue_type, pattern_info['suggestion']))
        
        if detected_issues:
            actions_taken.append("Matched crash patterns")
            response_parts.append("\n🎯 Detected Issues:")
            for issue_type, suggestion in detected_issues:
                response_parts.append(f"\n**{issue_type.replace('_', ' ').title()}**")
                response_parts.append(f"→ {suggestion}")
        
        # 4. Suggest next steps
        response_parts.append("\n\n🔧 Recommended Actions:")
        response_parts.append("1. Review the stack trace for the failing function")
        response_parts.append("2. Set a breakpoint at the crash location")
        response_parts.append("3. Inspect variable states before the crash")
        
        # 5. Offer to load related files
        if crash_logs:
            log_file = crash_logs[-1].target
            response_parts.append(f"\n📂 Would you like me to analyze: {log_file}?")
            actions_taken.append("Offered to analyze crash log")
        
        # Build final response
        final_response = "\n".join(response_parts)
        execution_time = time.time() - start_time
        
        self._update_metrics(execution_time)
        
        return ExpertResponse(
            success=True,
            response=final_response,
            actions_taken=actions_taken,
            confidence=0.85 if detected_issues else 0.6,
            execution_time=execution_time,
            metadata={
                'issues_detected': len(detected_issues),
                'crash_logs_found': len(crash_logs),
                'debug_events': len(debug_events)
            }
        )
    
    def can_handle(self, task: str, context: Dict) -> float:
        """Determine if this expert can handle debugging tasks"""
        task_lower = task.lower()
        
        # High confidence keywords
        high_confidence = ['debug', 'crash', 'bug', 'error', 'exception', 'segfault']
        if any(kw in task_lower for kw in high_confidence):
            return 0.9
        
        # Medium confidence keywords
        medium_confidence = ['fix', 'problem', 'issue', 'not working', 'broken']
        if any(kw in task_lower for kw in medium_confidence):
            return 0.6
        
        # Check context for debugging signals
        if context.get('recent_crashes', 0) > 0:
            return 0.7
        
        return 0.1  # Low confidence otherwise


class FileOperationsExpert(ExpertAgent):
    """
    File Operations Expert - Specializes in:
    - Finding files quickly
    - Organizing project structures
    - Analyzing file dependencies
    - Cleaning up temp files
    """
    
    def __init__(self, model_path: Optional[str] = None):
        super().__init__("FileOperationsExpert", model_path)
    
    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        system_events: List[SystemEvent]
    ) -> ExpertResponse:
        """Execute file operation task"""
        start_time = time.time()
        
        logger.info(f"📁 File Operations Expert executing: {task[:100]}...")
        
        actions_taken = []
        response = "File operations expert: Task received"
        
        # Analyze recent file access patterns
        file_events = [e for e in system_events if e.event_type == 'file']
        
        if file_events:
            # Group by directory
            directories = {}
            for event in file_events:
                dir_path = str(Path(event.target).parent)
                if dir_path not in directories:
                    directories[dir_path] = []
                directories[dir_path].append(event.target)
            
            actions_taken.append(f"Analyzed {len(file_events)} file events")
            actions_taken.append(f"Found {len(directories)} active directories")
            
            response = f"📊 File Activity Summary:\n"
            response += f"- {len(file_events)} file operations detected\n"
            response += f"- {len(directories)} directories accessed\n\n"
            
            response += "📂 Most Active Directories:\n"
            for dir_path, files in sorted(directories.items(), 
                                         key=lambda x: len(x[1]), 
                                         reverse=True)[:3]:
                response += f"  • {dir_path} ({len(files)} files)\n"
        
        execution_time = time.time() - start_time
        self._update_metrics(execution_time)
        
        return ExpertResponse(
            success=True,
            response=response,
            actions_taken=actions_taken,
            confidence=0.75,
            execution_time=execution_time,
            metadata={'file_events_analyzed': len(file_events)}
        )
    
    def can_handle(self, task: str, context: Dict) -> float:
        """Determine if this expert can handle file tasks"""
        task_lower = task.lower()
        
        file_keywords = ['file', 'find', 'search', 'locate', 'organize', 'folder', 'directory']
        if any(kw in task_lower for kw in file_keywords):
            return 0.85
        
        return 0.1


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_experts():
        """Test expert agents"""
        
        # Create experts
        debug_expert = DebuggingExpert()
        file_expert = FileOperationsExpert()
        
        # Simulate debugging task
        task = "My application crashed with a null pointer exception in main.cpp"
        
        events = [
            SystemEvent(
                timestamp="2024-01-01T10:00:00",
                event_type="process",
                source="Kernel",
                operation="execute",
                target="C:\\Program Files\\Visual Studio\\devenv.exe",
                process_name="devenv.exe",
                user="dev",
                metadata={}
            ),
            SystemEvent(
                timestamp="2024-01-01T10:00:10",
                event_type="file",
                source="Kernel",
                operation="read",
                target="C:\\Projects\\App\\crash_2024-01-01.log",
                process_name="app.exe",
                user="dev",
                metadata={}
            )
        ]
        
        print("🧪 Testing Debugging Expert...\n")
        response = await debug_expert.execute(task, {}, events)
        
        print(f"Success: {response.success}")
        print(f"Confidence: {response.confidence:.2%}")
        print(f"Execution Time: {response.execution_time*1000:.1f}ms")
        print(f"\nResponse:\n{response.response}")
        print(f"\nActions Taken:")
        for action in response.actions_taken:
            print(f"  • {action}")
        
        # Stats
        print(f"\n📊 Expert Stats:")
        stats = debug_expert.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    asyncio.run(test_experts())