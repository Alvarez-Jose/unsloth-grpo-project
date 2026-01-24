

import pytest
import sys
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from etw_monitor import SystemEvent, ETWEventMonitor
from master_router import MasterRouter, ExpertType, RoutingDecision
from experts.base_expert import DebuggingExpert, FileOperationsExpert


class TestSystemEvent:
    """Test SystemEvent data class"""
    
    def test_system_event_creation(self):
        """Test creating a system event"""
        event = SystemEvent(
            timestamp="2024-01-01T10:00:00",
            event_type="file",
            source="Kernel-File",
            operation="read",
            target="C:\\test.txt",
            process_name="test.exe",
            user="testuser",
            metadata={}
        )
        
        assert event.event_type == "file"
        assert event.operation == "read"
        assert event.process_name == "test.exe"
    
    def test_is_developer_activity(self):
        """Test developer activity detection"""
        dev_event = SystemEvent(
            timestamp="2024-01-01T10:00:00",
            event_type="file",
            source="Kernel-File",
            operation="read",
            target="C:\\projects\\main.cpp",
            process_name="devenv.exe",
            user="developer",
            metadata={}
        )
        
        assert dev_event.is_developer_activity()
    
    def test_is_debugging_session(self):
        """Test debugging session detection"""
        debug_event = SystemEvent(
            timestamp="2024-01-01T10:00:00",
            event_type="process",
            source="Kernel-Process",
            operation="execute",
            target="C:\\Program Files\\Visual Studio\\devenv.exe",
            process_name="devenv.exe",
            user="developer",
            metadata={}
        )
        
        assert debug_event.is_debugging_session()


class TestMasterRouter:
    """Test Master Router functionality"""
    
    @pytest.mark.asyncio
    async def test_router_initialization(self):
        """Test that router initializes without crashing"""
        router = MasterRouter()
        assert router is not None
        assert router.total_routings == 0
    
    @pytest.mark.asyncio
    async def test_rule_based_routing_debugging(self):
        """Test rule-based routing for debugging tasks"""
        router = MasterRouter()
        
        # Create debugging scenario
        events = [
            SystemEvent(
                timestamp="2024-01-01T10:00:00",
                event_type="process",
                source="Kernel",
                operation="execute",
                target="devenv.exe",
                process_name="devenv.exe",
                user="dev",
                metadata={}
            )
        ]
        
        decision = await router.route(
            system_events=events,
            user_query="Help me debug a crash"
        )
        
        assert isinstance(decision, RoutingDecision)
        assert decision.expert == ExpertType.DEBUGGING
        assert decision.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_routing_with_no_events(self):
        """Test routing with empty event list"""
        router = MasterRouter()
        
        decision = await router.route(
            system_events=[],
            user_query="Find my files"
        )
        
        assert isinstance(decision, RoutingDecision)
        # Should still make a decision even with no events


class TestDebuggingExpert:
    """Test Debugging Expert agent"""
    
    @pytest.mark.asyncio
    async def test_expert_initialization(self):
        """Test expert initializes correctly"""
        expert = DebuggingExpert()
        assert expert.name == "DebuggingExpert"
        assert expert.execution_count == 0
    
    @pytest.mark.asyncio
    async def test_can_handle_debug_query(self):
        """Test expert correctly identifies debugging tasks"""
        expert = DebuggingExpert()
        
        confidence = expert.can_handle(
            "Help me debug a null pointer exception",
            {}
        )
        
        assert confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_execute_null_pointer_task(self):
        """Test expert execution with null pointer crash"""
        expert = DebuggingExpert()
        
        events = [
            SystemEvent(
                timestamp="2024-01-01T10:00:00",
                event_type="file",
                source="Kernel",
                operation="read",
                target="C:\\logs\\crash.log",
                process_name="app.exe",
                user="dev",
                metadata={}
            )
        ]
        
        response = await expert.execute(
            task="App crashed with null pointer exception",
            context={},
            system_events=events
        )
        
        assert response.success
        assert response.confidence > 0.0
        assert len(response.actions_taken) > 0
        assert "null" in response.response.lower() or "pointer" in response.response.lower()


class TestFileOperationsExpert:
    """Test File Operations Expert agent"""
    
    @pytest.mark.asyncio
    async def test_can_handle_file_query(self):
        """Test expert identifies file operation tasks"""
        expert = FileOperationsExpert()
        
        confidence = expert.can_handle(
            "Find all Python files in my project",
            {}
        )
        
        assert confidence > 0.7
    
    @pytest.mark.asyncio
    async def test_execute_file_search(self):
        """Test expert execution with file events"""
        expert = FileOperationsExpert()
        
        events = [
            SystemEvent(
                timestamp="2024-01-01T10:00:00",
                event_type="file",
                source="Kernel",
                operation="read",
                target="C:\\projects\\file1.py",
                process_name="explorer.exe",
                user="dev",
                metadata={}
            ),
            SystemEvent(
                timestamp="2024-01-01T10:00:01",
                event_type="file",
                source="Kernel",
                operation="read",
                target="C:\\projects\\file2.py",
                process_name="explorer.exe",
                user="dev",
                metadata={}
            )
        ]
        
        response = await expert.execute(
            task="Organize my project files",
            context={},
            system_events=events
        )
        
        assert response.success
        assert len(response.actions_taken) > 0


class TestIntegration:
    """Integration tests for the full system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_debugging_workflow(self):
        """Test complete workflow from events to expert response"""
        # 1. Create router
        router = MasterRouter()
        
        # 2. Create events simulating debugging session
        events = [
            SystemEvent(
                timestamp="2024-01-01T10:00:00",
                event_type="process",
                source="Kernel",
                operation="execute",
                target="devenv.exe",
                process_name="devenv.exe",
                user="dev",
                metadata={}
            ),
            SystemEvent(
                timestamp="2024-01-01T10:00:05",
                event_type="file",
                source="Kernel",
                operation="read",
                target="C:\\crash.log",
                process_name="devenv.exe",
                user="dev",
                metadata={}
            )
        ]
        
        # 3. Route to expert
        decision = await router.route(
            system_events=events,
            user_query="Analyze this crash"
        )
        
        assert decision.expert == ExpertType.DEBUGGING
        
        # 4. Execute expert
        expert = DebuggingExpert()
        response = await expert.execute(
            task="Analyze crash in application",
            context={},
            system_events=events
        )
        
        # 5. Verify response
        assert response.success
        assert response.execution_time > 0
        assert len(response.actions_taken) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])