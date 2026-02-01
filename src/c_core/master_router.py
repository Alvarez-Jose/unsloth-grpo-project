"""
Master Router - Intelligent routing layer for expert selection
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time

from loguru import logger
from c_core.etw_monitor import SystemEvent


class ExpertType(Enum):
    """Available expert agents"""
    DEBUGGING = "DebuggingExpert"
    FILE_OPERATIONS = "FileOperationsExpert"
    UNKNOWN = "unknown"


@dataclass
class RoutingDecision:
    """Result of routing decision"""
    expert: ExpertType
    confidence: float
    reasoning: str
    speculative_experts: List[ExpertType]
    timestamp: float
    context_used: Dict[str, Any]


class MasterRouter:
    """Simple router that selects which expert to use"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.total_routings = 0
        self.routing_history: List[RoutingDecision] = []
        logger.info("Master Router initialized")
    
    async def route(
        self,
        system_events: List[SystemEvent],
        user_query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Decide which expert should handle the task
        """
        self.total_routings += 1
        
        # Simple rule-based routing
        reasoning = "Rule-based routing"
        alternatives = []
        
        # Check user query first
        if user_query:
            query_lower = user_query.lower()
            
            if any(word in query_lower for word in ['debug', 'crash', 'error', 'bug', 'fix']):
                expert = ExpertType.DEBUGGING
                confidence = 0.9
                reasoning = f"Query contains debugging keywords: '{user_query[:50]}...'"
                alternatives = [ExpertType.FILE_OPERATIONS]
            
            elif any(word in query_lower for word in ['file', 'find', 'search', 'locate', 'folder']):
                expert = ExpertType.FILE_OPERATIONS
                confidence = 0.85
                reasoning = f"Query contains file operation keywords: '{user_query[:50]}...'"
                alternatives = [ExpertType.DEBUGGING]
            
            else:
                # Default to debugging expert
                expert = ExpertType.DEBUGGING
                confidence = 0.5
                reasoning = "Default routing to debugging expert"
        
        else:
            # No query, analyze system events
            file_events = [e for e in system_events if e.event_type == 'file']
            debug_events = [e for e in system_events if e.is_debugging_session()]
            
            if debug_events:
                expert = ExpertType.DEBUGGING
                confidence = 0.8
                reasoning = f"Detected {len(debug_events)} debugging events"
            elif file_events:
                expert = ExpertType.FILE_OPERATIONS
                confidence = 0.7
                reasoning = f"Detected {len(file_events)} file events"
            else:
                expert = ExpertType.DEBUGGING
                confidence = 0.5
                reasoning = "No specific pattern detected"
        
        decision = RoutingDecision(
            expert=expert,
            confidence=confidence,
            reasoning=reasoning,
            speculative_experts=alternatives,
            timestamp=time.time(),
            context_used={'events_count': len(system_events)}
        )
        
        self.routing_history.append(decision)
        if len(self.routing_history) > 100:
            self.routing_history.pop(0)
        
        logger.info(f"Routed to {expert.value} (confidence: {confidence:.2%})")
        return decision
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        expert_dist = {}
        for decision in self.routing_history[-50:]:
            expert = decision.expert.value
            expert_dist[expert] = expert_dist.get(expert, 0) + 1
        
        return {
            'total_routings': self.total_routings,
            'recent_decisions': len(self.routing_history),
            'expert_distribution': expert_dist
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_router():
        """Test the master router"""
        router = MasterRouter()
        
        # Test events
        events = [
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
        
        # Test with query
        decision = await router.route(
            system_events=events,
            user_query="Help me debug this crash error"
        )
        
        print(f"Expert: {decision.expert.value}")
        print(f"Confidence: {decision.confidence:.2%}")
        print(f"Reasoning: {decision.reasoning}")
        
        # Show stats
        print(f"\nStats: {router.get_stats()}")
    
    asyncio.run(test_router())