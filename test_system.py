"""
Test script for AgentOS
"""

import asyncio
import sys
from pathlib import Path

# Fix for PyLance - Add these paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "src/c_core"))

print(f"Project root: {PROJECT_ROOT}")
print(f"Python path includes:")
for p in sys.path[:3]:
    print(f"  - {p}")

# Now import - PyLance should recognize these
from c_core.base_expert import DebuggingExpert, FileOperationsExpert
from c_core.etw_monitor import SystemEvent
from c_core.master_router import MasterRouter, ExpertType


async def test_individual_components():
    """Test each component individually"""
    print("Testing Individual Components...")
    print("="*60)
    
    # 1. Test experts
    print("\n1. Testing Expert Agents:")
    print("-"*40)
    
    debug_expert = DebuggingExpert()
    file_expert = FileOperationsExpert()
    
    # Test can_handle methods
    test_queries = [
        ("debug", "My app crashed with null pointer"),
        ("file", "Find all Python files"),
        ("unknown", "What's the weather today")
    ]
    
    for expert_type, query in test_queries:
        debug_score = debug_expert.can_handle(query, {})
        file_score = file_expert.can_handle(query, {})
        print(f"Query: '{query}'")
        print(f"  DebuggingExpert confidence: {debug_score:.2%}")
        print(f"  FileOperationsExpert confidence: {file_score:.2%}")
        print()
    
    # 2. Test master router
    print("\n2. Testing Master Router:")
    print("-"*40)
    
    router = MasterRouter()
    
    # Create test events
    test_events = [
        SystemEvent(
            timestamp="2024-01-01T10:00:00",
            event_type="file",
            source="test",
            operation="read",
            target="/home/user/projects/test.py",
            process_name="python.exe",
            user="user",
            metadata={}
        )
    ]
    
    # Test routing decisions
    test_routes = [
        ("debug query", "My app is crashing with segmentation fault"),
        ("file query", "I need to find all .log files"),
        ("general query", "What can you help me with?")
    ]
    
    for route_name, query in test_routes:
        decision = await router.route(test_events, query, {})
        print(f"{route_name}: '{query}'")
        print(f"  → Expert: {decision.expert.value}")
        print(f"  → Confidence: {decision.confidence:.2%}")
        print(f"  → Reasoning: {decision.reasoning}")
        print()
    
    # 3. Test expert execution
    print("\n3. Testing Expert Execution:")
    print("-"*40)
    
    # Test debugging expert
    debug_task = "Application crashed with memory leak"
    debug_response = await debug_expert.execute(debug_task, {}, test_events)
    
    print(f"Debugging task: '{debug_task}'")
    print(f"  Success: {debug_response.success}")
    print(f"  Confidence: {debug_response.confidence:.2%}")
    print(f"  Time: {debug_response.execution_time*1000:.1f}ms")
    print(f"  Actions taken: {debug_response.actions_taken}")
    
    # Test file expert
    file_task = "Show me file activity"
    file_response = await file_expert.execute(file_task, {}, test_events)
    
    print(f"\nFile task: '{file_task}'")
    print(f"  Success: {file_response.success}")
    print(f"  Confidence: {file_response.confidence:.2%}")
    print(f"  Time: {file_response.execution_time*1000:.1f}ms")
    
    # 4. Check stats
    print("\n4. Component Statistics:")
    print("-"*40)
    
    print("DebuggingExpert stats:")
    for key, value in debug_expert.get_stats().items():
        print(f"  {key}: {value}")
    
    print("\nFileOperationsExpert stats:")
    for key, value in file_expert.get_stats().items():
        print(f"  {key}: {value}")
    
    print("\nMasterRouter stats:")
    for key, value in router.get_stats().items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print(" All component tests completed!")


async def test_integration():
    """Test the full integration"""
    print("\n Testing Full System Integration...")
    print("="*60)
    
    try:
        # FIXED: Import AgentOS correctly
        try:
            # First try importing from src.main
            from src.main import AgentOS
            print("✅ Imported AgentOS from src.main")
        except ImportError:
            # If that fails, add src to path and try again
            import sys
            from pathlib import Path
            src_path = str(Path(__file__).parent / "src")
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            from main import AgentOS
            print("Imported AgentOS from main (with path adjustment)")
        
        # Create AgentOS instance
        print("1. Creating AgentOS instance...")
        agent_os = AgentOS()
        print(" AgentOS instance created")
        
        # Test initialization
        print("2. Initializing AgentOS...")
        await agent_os.initialize()
        print(" AgentOS initialized successfully")
        
        # Check components
        print("\n3. Checking components:")
        print(f"   ETW Monitor: {'✅ Present' if agent_os.etw_monitor else '❌ Missing'}")
        print(f"   Master Router: {'✅ Present' if agent_os.master_router else '❌ Missing'}")
        print(f"   Experts loaded: {len(agent_os.experts)}")
        
        # Show which experts are loaded
        if agent_os.experts:
            print("   Loaded experts:")
            for expert_type, expert in agent_os.experts.items():
                print(f"     • {expert_type.value}: {expert.name}")
        
        # Test a simple query
        print("\n4. Testing query processing...")
        try:
            result = await agent_os.process_user_query("Test query for debugging")
            print(f"   Query processed: {'✅ Success' if result.get('success') else '❌ Failed'}")
            if result.get('expert'):
                print(f"   Expert used: {result['expert']}")
            if result.get('response'):
                print(f"   Response preview: {result['response'][:100]}...")
        except Exception as query_error:
            print(f" Query processing error: {query_error}")
        
        # Test another query type
        print("\n5. Testing file operation query...")
        try:
            result = await agent_os.process_user_query("Find files in my project")
            print(f"   File query processed: {'✅ Success' if result.get('success') else '❌ Failed'}")
            if result.get('expert'):
                print(f"   Expert used: {result['expert']}")
        except Exception as file_error:
            print(f" File query error: {file_error}")
        
        # Show stats
        print("\n6. Checking system stats...")
        try:
            if hasattr(agent_os, '_show_stats'):
                agent_os._show_stats()
            elif hasattr(agent_os, 'master_router') and agent_os.master_router:
                stats = agent_os.master_router.get_stats()
                print(f"   Router stats: {stats}")
        except Exception as stats_error:
            print(f"Stats error: {stats_error}")
        
        # Cleanup
        print("\n7. Cleaning up...")
        await agent_os.stop()
        print("System cleanup complete")
        
    except ImportError as e:
        print(f"Import failed: {e}")
        print("\n Make sure:")
        print("   1. You're running from project root (where src/ directory is)")
        print("   2. main.py exists in src/ directory")
        print("   3. main.py contains 'class AgentOS:' definition")
        print(f"   Current directory: {Path(__file__).parent}")
        
        # Debug: List files
        import os
        print("\nFiles in current directory:")
        for item in os.listdir('.'):
            print(f"   - {item}")
        
        if os.path.exists('src'):
            print("\nFiles in src/ directory:")
            for item in os.listdir('src'):
                print(f"   - {item}")
        
    except Exception as e:
        print(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Integration test completed!")


def check_system_health():
    """Check system dependencies and setup"""
    print("\nSystem Health Check...")
    print("="*60)
    
    issues = []
    
    # Check Python version
    import platform
    py_version = platform.python_version()
    print(f"Python version: {py_version}")
    
    # Check required packages
    required_packages = ['loguru', 'psutil', 'watchdog']
    for package in required_packages:
        try:
            __import__(package)
            print(f"{package}: Installed")
        except ImportError:
            issues.append(f"Missing package: {package}")
            print(f"{package}: Missing")
    
    # Check directory structure
    required_dirs = ['logs', 'models', 'build']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"Directory: {dir_name}/")
        else:
            issues.append(f"Missing directory: {dir_name}/")
            print(f"Directory: {dir_name}/ (missing)")
    
    # Check source files
    required_files = [
        'src/c_core/__init__.py',
        'src/c_core/base_expert.py',
        'src/c_core/etw_monitor.py',
        'src/c_core/master_router.py',
        'src/c_core/c_bridge.py',
        'src/main.py'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"File: {file_path}")
        else:
            issues.append(f"Missing file: {file_path}")
            print(f"File: {file_path} (missing)")
    
    # Report issues
    if issues:
        print(f"\nFound {len(issues)} issues:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("\nAll system checks passed!")
    
    print("\n" + "="*60)
    return len(issues) == 0


async def main():
    """Run all tests"""
    print("🚀 AgentOS System Diagnostics")
    print("="*60)
    
    # 1. System health check
    if not check_system_health():
        print("\n❌ System health check failed. Please fix issues above.")
        return
    
    # 2. Test individual components
    await test_individual_components()
    
    # 3. Test integration
    await test_integration()
    
    print("\n" + "="*60)
    print("🎉 All tests completed successfully!")
    print("\nNext steps:")
    print("1. Run the full system: python src/main.py")
    print("2. Try interactive mode commands")
    print("3. Add more expert agents")
    print("4. Implement episodic memory")


if __name__ == "__main__":
    asyncio.run(main())