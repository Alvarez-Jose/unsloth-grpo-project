"""
Master Router - Intelligent routing layer for expert selection

The master model is a small (1-3B parameter) model that learns to:
1. Analyze system events and user queries
2. Route tasks to specialized expert agents
3. Learn from routing decisions over time
4. Coordinate speculative execution

This is the "brain" of the hierarchical MoE architecture.
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time
from pathlib import Path

try:
    from llama_cpp import Llama
except ImportError:
    print("llama-cpp-python not installed. Run: pip install llama-cpp-python")
    exit(1)

from loguru import logger
from etw_monitor import SystemEvent


class ExpertType(Enum):
    """Available expert agents"""
    FILE_OPERATIONS = "file_operations"
    CODE_ANALYSIS = "code_analysis"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    SYSTEM_ADMIN = "system_admin"
    UNKNOWN = "unknown"


@dataclass
class RoutingDecision:
    """Result of routing decision"""
    expert: ExpertType
    confidence: float
    reasoning: str
    speculative_experts: List[ExpertType]  # Alternative experts to run speculatively
    timestamp: float
    context_used: Dict


class MasterRouter:
    """
    Master routing model that selects which expert to activate
    
    Uses a small, fast model (Phi-2 3B) to make routing decisions
    based on system events and user context.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Args:
            model_path: Path to GGUF model file (defaults to Phi-2)
        """
        self.model_path = model_path or self._get_default_model()
        self.model: Optional[Llama] = None
        self.routing_history: List[RoutingDecision] = []
        
        # Performance tracking
        self.total_routings = 0
        self.average_latency = 0.0
        
        logger.info(f"Initializing Master Router with model: {self.model_path}")
        self._load_model()
    
    def _get_default_model(self) -> str:
        """Get default model path"""
        models_dir = Path(__file__).parent.parent / "models"
        models_dir.mkdir(exist_ok=True)
        
        # Look for Phi-2 model
        default_model = models_dir / "phi-2.Q4_K_M.gguf"
        
        if not default_model.exists():
            logger.warning(f"Model not found at {default_model}")
            logger.info("Download with: python scripts/download_models.py")
        
        return str(default_model)
    
    def _load_model(self):
        """Load the routing model"""
        if not Path(self.model_path).exists():
            logger.error(f"Model file not found: {self.model_path}")
            logger.info("Using fallback rule-based routing")
            return
        
        try:
            logger.info("Loading master routing model...")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=2048,  # Context window
                n_threads=4,  # CPU threads
                n_gpu_layers=35,  # Offload layers to GPU if available
                verbose=False
            )
            logger.info("✅ Master router model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.info("Falling back to rule-based routing")
    
    async def route(
        self,
        system_events: List[SystemEvent],
        user_query: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> RoutingDecision:
        """
        Main routing function - decides which expert to activate
        
        Args:
            system_events: Recent system events from ETW monitor
            user_query: Optional explicit user query
            context: Additional context (memory, user preferences, etc.)
        
        Returns:
            RoutingDecision with expert selection and confidence
        """
        start_time = time.time()
        
        # Build routing prompt
        prompt = self._build_routing_prompt(system_events, user_query, context)
        
        # Get routing decision
        if self.model:
            decision = await self._model_based_routing(prompt, system_events)
        else:
            decision = self._rule_based_routing(system_events, user_query)
        
        # Track performance
        latency = time.time() - start_time
        self._update_metrics(latency)
        
        # Store decision
        self.routing_history.append(decision)
        if len(self.routing_history) > 1000:
            self.routing_history.pop(0)
        
        logger.info(
            f" Routed to {decision.expert.value} "
            f"(confidence: {decision.confidence:.2f}, "
            f"latency: {latency*1000:.1f}ms)"
        )
        
        return decision
    
    def _build_routing_prompt(
        self,
        system_events: List[SystemEvent],
        user_query: Optional[str],
        context: Optional[Dict]
    ) -> str:
        """Build prompt for routing decision"""
        
        # Summarize recent events
        event_summary = self._summarize_events(system_events)
        
        prompt = f"""You are a routing expert for an AI agent system. Analyze the context and decide which expert agent should handle this task.

Available Experts:
1. file_operations - File management, search, organization
2. code_analysis - Code review, refactoring, analysis
3. debugging - Bug investigation, crash analysis, debugging assistance
4. documentation - Finding docs, explaining APIs, tutorials
5. system_admin - System configuration, performance, troubleshooting

Recent System Events:
{event_summary}
"""
        
        if user_query:
            prompt += f"\nUser Query: {user_query}\n"
        
        if context:
            prompt += f"\nAdditional Context: {json.dumps(context, indent=2)}\n"
        
        prompt += """
Respond with ONLY a JSON object:
{
    "expert": "expert_name",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "alternatives": ["expert1", "expert2"]
}
"""
        
        return prompt
    
    def _summarize_events(self, events: List[SystemEvent]) -> str:
        """Summarize system events for the prompt"""
        if not events:
            return "No recent events"
        
        summary_parts = []
        
        # Group by type
        by_type = {}
        for event in events[-10:]:  # Last 10 events
            event_type = event.event_type
            if event_type not in by_type:
                by_type[event_type] = []
            by_type[event_type].append(event)
        
        # Summarize each type
        for event_type, type_events in by_type.items():
            targets = [e.target for e in type_events[:3]]
            summary_parts.append(
                f"- {event_type}: {len(type_events)} events "
                f"(recent: {', '.join(targets)})"
            )
        
        return "\n".join(summary_parts)
    
    async def _model_based_routing(
        self,
        prompt: str,
        system_events: List[SystemEvent]
    ) -> RoutingDecision:
        """Use LLM to make routing decision"""
        try:
            # Generate routing decision
            response = self.model(
                prompt,
                max_tokens=200,
                temperature=0.1,  # Low temperature for consistent routing
                stop=["}", "\n\n"]
            )
            
            # Parse response
            response_text = response['choices'][0]['text']
            
            # Extract JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                decision_dict = json.loads(json_str)
                
                # Convert to RoutingDecision
                expert = ExpertType(decision_dict.get('expert', 'unknown'))
                confidence = float(decision_dict.get('confidence', 0.5))
                reasoning = decision_dict.get('reasoning', 'Model-based routing')
                alternatives = [
                    ExpertType(alt) for alt in decision_dict.get('alternatives', [])
                ]
                
                return RoutingDecision(
                    expert=expert,
                    confidence=confidence,
                    reasoning=reasoning,
                    speculative_experts=alternatives[:2],  # Top 2 alternatives
                    timestamp=time.time(),
                    context_used={'events_count': len(system_events)}
                )
        
        except Exception as e:
            logger.warning(f"Model routing failed: {e}, falling back to rules")
        
        # Fallback to rule-based
        return self._rule_based_routing(system_events, None)
    
    def _rule_based_routing(
        self,
        system_events: List[SystemEvent],
        user_query: Optional[str]
    ) -> RoutingDecision:
        """
        Fallback rule-based routing
        
        Uses heuristics when model is unavailable
        """
        expert = ExpertType.UNKNOWN
        confidence = 0.5
        reasoning = "Rule-based routing"
        alternatives = []
        
        # Analyze recent events
        recent = system_events[-10:] if system_events else []
        
        # Check for debugging pattern
        debug_count = sum(1 for e in recent if e.is_debugging_session())
        if debug_count >= 2:
            expert = ExpertType.DEBUGGING
            confidence = 0.8
            reasoning = "Detected debugging session from system events"
            alternatives = [ExpertType.CODE_ANALYSIS, ExpertType.DOCUMENTATION]
        
        # Check for file operations
        elif any(e.event_type == 'file' for e in recent):
            file_events = [e for e in recent if e.event_type == 'file']
            if len(file_events) >= 3:
                expert = ExpertType.FILE_OPERATIONS
                confidence = 0.7
                reasoning = "Multiple file operations detected"
                alternatives = [ExpertType.CODE_ANALYSIS]
        
        # Check for code analysis pattern
        elif any(any(ext in e.target for ext in ['.cpp', '.py', '.js', '.rs']) 
                 for e in recent):
            expert = ExpertType.CODE_ANALYSIS
            confidence = 0.75
            reasoning = "Source code files accessed"
            alternatives = [ExpertType.DEBUGGING, ExpertType.DOCUMENTATION]
        
        # User query analysis
        if user_query:
            query_lower = user_query.lower()
            
            if any(word in query_lower for word in ['debug', 'crash', 'error', 'bug']):
                expert = ExpertType.DEBUGGING
                confidence = 0.9
                reasoning = f"User query mentions debugging: '{user_query}'"
            
            elif any(word in query_lower for word in ['find', 'search', 'locate', 'file']):
                expert = ExpertType.FILE_OPERATIONS
                confidence = 0.85
                reasoning = f"User query about file operations: '{user_query}'"
            
            elif any(word in query_lower for word in ['docs', 'documentation', 'how to', 'api']):
                expert = ExpertType.DOCUMENTATION
                confidence = 0.9
                reasoning = f"User query about documentation: '{user_query}'"
        
        return RoutingDecision(
            expert=expert,
            confidence=confidence,
            reasoning=reasoning,
            speculative_experts=alternatives[:2],
            timestamp=time.time(),
            context_used={'events_count': len(system_events)}
        )
    
    def _update_metrics(self, latency: float):
        """Update performance metrics"""
        self.total_routings += 1
        
        # Exponential moving average for latency
        alpha = 0.1
        self.average_latency = (
            alpha * latency + (1 - alpha) * self.average_latency
        )
    
    def get_stats(self) -> Dict:
        """Get routing statistics"""
        return {
            'total_routings': self.total_routings,
            'average_latency_ms': self.average_latency * 1000,
            'recent_decisions': len(self.routing_history),
            'expert_distribution': self._get_expert_distribution()
        }
    
    def _get_expert_distribution(self) -> Dict[str, int]:
        """Get distribution of expert selections"""
        distribution = {}
        for decision in self.routing_history[-100:]:  # Last 100
            expert = decision.expert.value
            distribution[expert] = distribution.get(expert, 0) + 1
        return distribution


# Example usage
if __name__ == "__main__":
    async def test_routing():
        """Test the master router"""
        router = MasterRouter()
        
        # Simulate debugging session events
        events = [
            SystemEvent(
                timestamp="2024-01-01T10:00:00",
                event_type="process",
                source="Kernel-Process",
                operation="execute",
                target="C:\\Program Files\\Visual Studio\\devenv.exe",
                process_name="devenv.exe",
                user="developer",
                metadata={}
            ),
            SystemEvent(
                timestamp="2024-01-01T10:00:05",
                event_type="file",
                source="Kernel-File",
                operation="read",
                target="C:\\Projects\\MyApp\\main.cpp",
                process_name="devenv.exe",
                user="developer",
                metadata={}
            ),
            SystemEvent(
                timestamp="2024-01-01T10:00:10",
                event_type="file",
                source="Kernel-File",
                operation="read",
                target="C:\\Projects\\MyApp\\debug.log",
                process_name="devenv.exe",
                user="developer",
                metadata={}
            )
        ]
        
        # Test routing
        decision = await router.route(
            system_events=events,
            user_query="Help me debug this crash"
        )
        
        print(f"\n Routing Decision:")
        print(f"   Expert: {decision.expert.value}")
        print(f"   Confidence: {decision.confidence:.2%}")
        print(f"   Reasoning: {decision.reasoning}")
        print(f"   Speculative alternatives: {[e.value for e in decision.speculative_experts]}")
        
        # Show stats
        print(f"\n📊 Router Stats:")
        stats = router.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    # Run test
    asyncio.run(test_routing())