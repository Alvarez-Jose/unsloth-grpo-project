"""
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
from typing import Optional
import signal

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from etw_monitor import ETWEventMonitor, SystemEvent
from master_router import MasterRouter, ExpertType
from experts.base_expert import DebuggingExpert, FileOperationsExpert


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
        self.experts = {}
        self.is_running = False
        
        logger.info(" AgentOS initializing...")
        
        # Configure logger
        logger.add(
            "logs/agent-os_{time}.log",
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
            # Add more experts here as you build them
        }
        
        # 3. Initialize ETW Monitor with callback
        logger.info("Starting ETW Event Monitor...")
        self.etw_monitor = ETWEventMonitor(
            event_callback=self._on_system_event
        )
        
        logger.info("All components initialized")
    
    def _on_system_event(self, event: SystemEvent):
        """
        Callback when interesting system events detected
        
        This is where the magic happens - we predict what the user
        might need based on system events and proactively prepare.
        """
        logger.debug(f"System event: {event.event_type} - {event.target}")
        
        # Example: Auto-trigger debugging expert when crash detected
        if 'crash' in event.target.lower() or 'error' in event.target.lower():
            logger.info(" Crash/error detected - auto-triggering debugging expert")
            asyncio.create_task(self._auto_assist_debugging(event))
    
    async def _auto_assist_debugging(self, trigger_event: SystemEvent):
        """
        Automatically assist with debugging when crash detected
        
        This is an example of proactive agent behavior.
        """
        logger.info(" Proactive debugging assistance activated")
        
        # Get recent context
        recent_events = self.etw_monitor.get_recent_events(20)
        
        # Route to appropriate expert
        decision = await self.master_router.route(
            system_events=recent_events,
            user_query=f"Analyze crash: {trigger_event.target}",
            context={'auto_triggered': True}
        )
        
        # Execute expert
        if decision.expert in self.experts:
            expert = self.experts[decision.expert]
            response = await expert.execute(
                task=f"Analyze crash log: {trigger_event.target}",
                context={'auto_triggered': True},
                system_events=recent_events
            )
            
            logger.info(f" Auto-assist complete: {response.success}")
            logger.info(f"Expert response: {response.response[:200]}...")
    
    async def process_user_query(self, query: str):
        """
        Process explicit user query
        
        This is the main entry point for user-initiated tasks.
        """
        logger.info(f"👤 User query: {query}")
        
        # Get system context
        recent_events = self.etw_monitor.get_recent_events(50)
        
        # Route to expert
        decision = await self.master_router.route(
            system_events=recent_events,
            user_query=query,
            context={}
        )
        
        logger.info(
            f"Routed to {decision.expert.value} "
            f"(confidence: {decision.confidence:.2%})"
        )
        
        # Get the expert
        if decision.expert not in self.experts:
            logger.warning(f"Expert {decision.expert.value} not implemented yet")
            return {
                'success': False,
                'message': f"Expert {decision.expert.value} not available yet"
            }
        
        expert = self.experts[decision.expert]
        
        # Execute
        logger.info(f"⚡ Executing {expert.name}...")
        response = await expert.execute(
            task=query,
            context={'user_initiated': True},
            system_events=recent_events
        )
        
        # Log results
        logger.info(f"Task completed in {response.execution_time*1000:.1f}ms")
        logger.info(f"Confidence: {response.confidence:.2%}")
        
        # Display to user
        print("\n" + "="*60)
        print(f" {expert.name} Response:")
        print("="*60)
        print(response.response)
        print("\n" + "-"*60)
        print(f" Metrics:")
        print(f"  • Execution time: {response.execution_time*1000:.1f}ms")
        print(f"  • Confidence: {response.confidence:.2%}")
        print(f"  • Actions taken: {len(response.actions_taken)}")
        for action in response.actions_taken:
            print(f"    - {action}")
        print("="*60 + "\n")
        
        return {
            'success': response.success,
            'expert': expert.name,
            'response': response.response,
            'metrics': {
                'execution_time_ms': response.execution_time * 1000,
                'confidence': response.confidence
            }
        }
    
    async def run_interactive(self):
        """Run in interactive mode - accept user queries"""
        print("\n" + "="*60)
        print(" AgentOS Interactive Mode")
        print("="*60)
        print("\nCommands:")
        print("  • Type your query to get AI assistance")
        print("  • 'stats' - Show system statistics")
        print("  • 'events' - Show recent system events")
        print("  • 'quit' - Exit")
        print("\n" + "="*60 + "\n")
        
        while self.is_running:
            try:
                # Get user input
                query = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: input("You: ")
                )
                
                query = query.strip()
                
                if not query:
                    continue
                
                # Handle commands
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Shutting down...")
                    break
                
                elif query.lower() == 'stats':
                    self._show_stats()
                    continue
                
                elif query.lower() == 'events':
                    self._show_recent_events()
                    continue
                
                # Process as agent query
                await self.process_user_query(query)
            
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                print(f"❌ Error: {e}")
    
    def _show_stats(self):
        """Display system statistics"""
        print("\n" + "="*60)
        print(" AgentOS Statistics")
        print("="*60)
        
        # Router stats
        router_stats = self.master_router.get_stats()
        print("\n Master Router:")
        for key, value in router_stats.items():
            print(f"  • {key}: {value}")
        
        # Expert stats
        print("\n Expert Agents:")
        for expert_type, expert in self.experts.items():
            stats = expert.get_stats()
            print(f"\n  {expert_type.value}:")
            for key, value in stats.items():
                print(f"    • {key}: {value}")
        
        print("="*60 + "\n")
    
    def _show_recent_events(self):
        """Display recent system events"""
        print("\n" + "="*60)
        print(" Recent System Events")
        print("="*60)
        
        events = self.etw_monitor.get_recent_events(10)
        
        if not events:
            print("No events recorded yet")
        else:
            for i, event in enumerate(events, 1):
                print(f"\n{i}. {event.event_type.upper()} - {event.operation}")
                print(f"   Target: {event.target}")
                print(f"   Process: {event.process_name}")
                print(f"   Time: {event.timestamp}")
        
        print("\n" + "="*60 + "\n")
    
    async def start(self):
        """Start the AgentOS system"""
        await self.initialize()
        
        self.is_running = True
        
        # Start ETW monitoring in background
        self.etw_monitor.start()
        
        logger.info(" AgentOS started successfully")
        logger.info("Monitoring system events and ready for queries")
    
    async def stop(self):
        """Stop the AgentOS system"""
        logger.info("Stopping AgentOS...")
        
        self.is_running = False
        
        if self.etw_monitor:
            self.etw_monitor.stop()
        
        logger.info("AgentOS stopped")


async def main():
    """Main entry point"""
    # Create AgentOS instance
    agent_os = AgentOS()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print("\nReceived interrupt signal")
        asyncio.create_task(agent_os.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start system
    await agent_os.start()
    
    # Run interactive mode
    await agent_os.run_interactive()
    
    # Cleanup
    await agent_os.stop()


if __name__ == "__main__":
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Run
    asyncio.run(main())