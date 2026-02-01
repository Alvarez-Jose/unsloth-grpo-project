#!/usr/bin/env python3
"""
Fix main.py by replacing it with correct AgentOS code
"""

from pathlib import Path
import shutil

# Paths
PROJECT_ROOT = Path(__file__).parent
MAIN_PY = PROJECT_ROOT / "src" / "main.py"
MASTER_ROUTER_PY = PROJECT_ROOT / "src" / "c_core" / "master_router.py"

print("🔧 Fixing main.py...")
print(f"Project: {PROJECT_ROOT}")
print(f"Current main.py: {MAIN_PY}")
print(f"Current main.py size: {MAIN_PY.stat().st_size if MAIN_PY.exists() else 'Missing'} bytes")

# Check if main.py is actually master_router.py
if MAIN_PY.exists():
    with open(MAIN_PY, 'r') as f:
        content = f.read()
    
    if 'class MasterRouter' in content and 'class AgentOS' not in content:
        print("❌ main.py contains MasterRouter code instead of AgentOS")
        
        # Backup the wrong file
        backup_path = PROJECT_ROOT / "src" / "main.py.backup"
        shutil.copy2(MAIN_PY, backup_path)
        print(f"📁 Backed up to: {backup_path}")
        
        # Write correct AgentOS code
        agentos_code = '''"""
This is the central coordination system that:
1. Monitors system events via ETW
2. Routes tasks to appropriate experts via Master Router
3. Executes expert agents
4. Manages episodic memory (future)
5. Handles speculative execution (future)
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict
import signal

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from c_core.etw_monitor import ETWEventMonitor, SystemEvent
from c_core.master_router import MasterRouter, ExpertType
from c_core.base_expert import DebuggingExpert, FileOperationsExpert


class AgentOS:
    """ 
    Coordinates between:
    - ETW event monitoring (kernel-level awareness)
    - Master routing (intelligent task distribution)
    - Expert agents (specialized execution)
    - Episodic memory (cross-expert learning) - TODO
    """
    
    def __init__(self):
        self.etw_monitor: Optional[ETWEventMonitor] = None
        self.master_router: Optional[MasterRouter] = None
        self.experts: Dict[ExpertType, object] = {}
        self.is_running = False
        
        logger.info(" AgentOS initializing...")
        
        # Configure logger
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        logger.add(
            logs_dir / "agent-os_{time}.log",
            rotation="100 MB",
            retention="7 days",
            level="DEBUG"
        )
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing components...")
        
        # 1. Initialize Master Router
        logger.info("Loading Master Router...")
        self.master_router = MasterRouter()
        
        # 2. Initialize Expert Agents
        logger.info("Loading Expert Agents...")
        self.experts = {
            ExpertType.DEBUGGING: DebuggingExpert(),
            ExpertType.FILE_OPERATIONS: FileOperationsExpert(),
        }
        
        logger.info("All components initialized")
    
    async def process_user_query(self, query: str):
        """Process explicit user query"""
        logger.info(f"👤 User query: {query}")
        
        # Create test events for now
        test_events = [
            SystemEvent(
                timestamp="2024-01-01T10:00:00",
                event_type="file",
                source="test",
                operation="read",
                target="/test/file.txt",
                process_name="test.exe",
                user="test",
                metadata={}
            )
        ]
        
        decision = await self.master_router.route(
            system_events=test_events,
            user_query=query,
            context={}
        )
        
        logger.info(f"Routed to {decision.expert.value} (confidence: {decision.confidence:.2%})")
        
        if decision.expert not in self.experts:
            return {
                'success': False,
                'message': f"Expert {decision.expert.value} not available yet"
            }
        
        expert = self.experts[decision.expert]
        response = await expert.execute(
            task=query,
            context={'user_initiated': True},
            system_events=test_events
        )
        
        print(f"\n{expert.name}: {response.response}")
        return {'success': True, 'expert': expert.name}
    
    async def run_interactive(self):
        """Run in interactive mode"""
        print("\n" + "="*60)
        print(" AgentOS Interactive Mode")
        print("="*60)
        print("Type 'quit' to exit\n")
        
        while True:
            query = input("You: ").strip()
            if query.lower() in ['quit', 'exit']:
                break
            await self.process_user_query(query)
    
    async def start(self):
        """Start the AgentOS system"""
        await self.initialize()
        self.is_running = True
        logger.info("AgentOS started")
    
    async def stop(self):
        """Stop the AgentOS system"""
        self.is_running = False
        logger.info("AgentOS stopped")


async def main():
    """Main entry point"""
    agent_os = AgentOS()
    await agent_os.start()
    await agent_os.run_interactive()
    await agent_os.stop()


if __name__ == "__main__":
    Path("logs").mkdir(exist_ok=True)
    asyncio.run(main())
'''
        
        with open(MAIN_PY, 'w') as f:
            f.write(agentos_code)
        
        print("✅ Fixed main.py with AgentOS code")
        print(f"New size: {MAIN_PY.stat().st_size} bytes")
        
    else:
        print("✅ main.py already contains AgentOS or different content")
else:
    print("❌ main.py doesn't exist")
    # Create it with AgentOS code
    # ... (similar to above)