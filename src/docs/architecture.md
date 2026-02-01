# Cortex Architecture

> Deep dive into the novel hierarchical AI agent architecture

## Table of Contents

1. [Overview](#overview)
2. [Novel Contributions](#novel-contributions)
3. [System Components](#system-components)
4. [Data Flow](#data-flow)
5. [Performance Characteristics](#performance-characteristics)
6. [Future Enhancements](#future-enhancements)

---

## Overview

Cortex implements a **hierarchical Mixture of Experts (MoE) architecture** with kernel-level context awareness. Unlike cloud-based agents or single-model systems, Cortex:

- Runs **100% locally** (privacy-first)
- Uses **kernel-level event monitoring** for predictive context
- Employs **specialized expert models** coordinated by a small master router
- Implements **speculative execution** for low-latency responses
- Shares knowledge through **episodic memory pooling**

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    KERNEL LAYER (C/C++)                         │
│  ┌──────────────┐   ┌───────────────┐   ┌──────────────┐      │
│  │ ETW Consumer │   │  Minifilter   │   │ WFP Callout  │      │
│  │ (File/Proc)  │   │ (Filesystem)  │   │  (Network)   │      │
│  └──────┬───────┘   └───────┬───────┘   └──────┬───────┘      │
└─────────┼───────────────────┼───────────────────┼──────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
          ┌───────────────────▼────────────────────┐
          │   Event Correlation Engine             │
          │   • Pattern detection                  │
          │   • Intent prediction                  │
          │   • Context aggregation                │
          └───────────────────┬────────────────────┘
                              │
          ┌───────────────────▼────────────────────┐
          │      Master Router (Phi-2 3B)          │
          │   • Route to appropriate expert        │
          │   • Learn from routing history         │
          │   • Trigger speculative execution      │
          └───────────────────┬────────────────────┘
                              │
          ┌───────────────────▼────────────────────┐
          │     Speculative Executor               │
          │  ┌──────────┐  ┌──────────┐  ┌──────┐ │
          │  │ Expert 1 │  │ Expert 2 │  │ Exp3 │ │
          │  │ (3-7B)   │  │ (3-7B)   │  │(3-7B)│ │
          │  │  [NPU]   │  │  [NPU]   │  │ [NPU]│ │
          │  └────┬─────┘  └────┬─────┘  └───┬──┘ │
          └───────┼─────────────┼────────────┼─────┘
                  │             │            │
          ┌───────┴─────────────┴────────────┴─────┐
          │        Episodic Memory Layer            │
          │  ┌─────────┐ ┌─────────┐ ┌──────────┐ │
          │  │ Vector  │ │  Graph  │ │Time-     │ │
          │  │   DB    │ │   DB    │ │Series DB │ │
          │  │(Chroma) │ │ (Neo4j) │ │(DuckDB)  │ │
          │  └─────────┘ └─────────┘ └──────────┘ │
          └─────────────────────────────────────────┘
```

---

## Novel Contributions

### 1. Kernel-Level Context Injection

**What makes it novel:**
- Most agents operate in userland with no visibility into system internals
- Cortex hooks directly into Windows kernel via ETW and minifilters
- Predicts user intent BEFORE they articulate it

**Implementation:**

```c
// Minifilter captures file operations
FLT_PREOP_CALLBACK_STATUS PreFileCreate(
    PFLT_CALLBACK_DATA Data,
    PCFLT_RELATED_OBJECTS FltObjects,
    PVOID *CompletionContext
) {
    // Detect: User is opening a .cpp file
    // Action: Pre-load relevant documentation and recent crash logs
    // Benefit: Zero-latency assistance
    
    SendToUserMode(Data->Iopb->TargetFileObject->FileName);
    return FLT_PREOP_SUCCESS_NO_CALLBACK;
}
```

**Advantage over existing systems:**
- Microsoft's Agent Workspaces: Runs in separate VMs, no kernel visibility
- Cloud agents: Network latency + no local system context
- Single-model systems: Can't predict, only react

### 2. Hierarchical MoE with Memory Pooling

**What makes it novel:**
- Traditional MoE: Experts are isolated, no cross-learning
- Cortex MoE: Experts share episodic memory

**How it works:**

```python
class EpisodicMemory:
    def record_episode(self, expert_id, task, outcome):
        # Store: "When debugging, user often needs file search next"
        self.graph.add_edge(
            source=expert_id,
            target="likely_next_expert",
            weight=confidence
        )
        
        # Later, when debugging expert runs:
        likely_next = self.graph.get_neighbors(expert_id)
        # Pre-load file search expert speculatively
```

**Real-world scenario:**

1. User opens Visual Studio → File expert activates
2. User opens `main.cpp` → Code expert learns "after opening IDE, user edits main.cpp"
3. Next time IDE opens → Code expert speculatively loads main.cpp context
4. **User experiences zero latency** because context is pre-loaded

### 3. Speculative Multi-Agent Execution

**What makes it novel:**
- Inspired by CPU speculative execution and LLM speculative decoding
- Applied to multi-agent systems at OS level

**How it works:**

```python
# Master detects debugging session starting
master.detect_pattern("debugging_session_start")

# Speculatively execute 3 experts in parallel on NPU
futures = [
    npu.execute(debugging_expert),  # Most likely
    npu.execute(file_expert),       # Second likely
    npu.execute(doc_expert),        # Third likely
]

# Wait for user action
user_action = await wait_for_user()

# Validate which speculation was correct
correct_expert = master.validate(user_action, futures)

# Discard others, commit correct one
# Update speculation weights for learning
```

**Performance gain:**
- Traditional: Wait for user action → Route → Execute → Respond (500ms+)
- Speculative: Pre-execute → User acts → Immediate response (<50ms)

### 4. Personal Federated Learning

**What makes it novel:**
- Federated learning typically for privacy across users
- Cortex uses it for multi-device personal learning

**Architecture:**

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Laptop   │────▶│ Desktop  │◀────│  Phone   │
│ (Device1)│     │(Hub/Sync)│     │(Device3) │
└──────────┘     └──────────┘     └──────────┘
     │                 │                │
     │  Model Updates  │  Model Updates │
     │  (not raw data) │                │
     └─────────────────┴────────────────┘
                       │
            ┌──────────▼──────────┐
            │  Aggregated Model   │
            │  "Your-AI-Profile"  │
            └─────────────────────┘
```

**Example:**
- Learn on laptop: "User debugs C++ every morning"
- Sync to desktop: Desktop pre-loads C++ tools in morning
- All data stays on your devices

---

## System Components

### Kernel Layer

#### ETW Consumer (Event Tracing for Windows)

**Purpose:** Real-time system event capture

**Monitored Events:**
- File I/O (create, read, write, delete)
- Process lifecycle (start, stop)
- Registry modifications
- Network connections
- Disk I/O patterns

**Performance:**
- Overhead: <1% CPU
- Latency: <5ms from event to agent

**Code Location:** `kernel/etw-consumer/`

#### Minifilter Driver

**Purpose:** File system interception

**Capabilities:**
- Pre-operation callbacks (before file access)
- Post-operation callbacks (after file access)
- Context injection to user-mode agents

**Safety:**
- Runs in kernel mode (dangerous!)
- Extensive error handling required
- Fail-safe: System continues even if driver crashes

**Development Status:** 🟡 Planned (Week 5-8)

**Code Location:** `kernel/minifilter/`

#### WFP Callout (Windows Filtering Platform)

**Purpose:** Network traffic monitoring

**Use Cases:**
- Detect documentation site access
- Predict API lookup needs
- Monitor development server traffic

**Development Status:** 🔴 Future (Week 9+)

**Code Location:** `kernel/wfp-callout/`

---

### Core Layer (Python)

#### Event Correlation Engine

**Purpose:** Transform raw kernel events into actionable context

**Responsibilities:**
1. **Event Buffering**: Keep last 1000 events in memory
2. **Pattern Detection**: Identify behavioral patterns
3. **Intent Prediction**: Guess what user wants to do next
4. **Context Aggregation**: Build rich context for master router

**Key Patterns Detected:**
- Debugging sessions
- Code reviews
- Documentation searches
- File organization tasks
- System troubleshooting

**Code Location:** `core/etw_monitor.py`

#### Master Router

**Purpose:** Intelligent routing to expert agents

**Model:** Phi-2 3B (1.6GB quantized)

**Routing Strategy:**
```python
def route(system_events, user_query):
    # 1. Analyze system events
    context = analyze_events(system_events)
    
    # 2. Build routing prompt
    prompt = build_prompt(context, user_query)
    
    # 3. LLM predicts best expert
    expert = model.predict(prompt)
    
    # 4. Get alternative experts for speculation
    alternatives = model.predict_alternatives(prompt)
    
    return expert, alternatives
```

**Learning Mechanism:**
- Tracks routing history
- Learns user preferences over time
- Adapts to usage patterns

**Code Location:** `core/master_router.py`

#### Expert Agents

Each expert is a 3-7B parameter model specialized for specific domains.

**Current Experts:**

1. **DebuggingExpert**
   - Model: DeepSeek-Coder 6.7B
   - Specializes in: Crash analysis, stack trace interpretation, bug fixing
   - Knowledge: Common crash patterns, debugging workflows

2. **FileOperationsExpert**
   - Model: CodeLlama 7B
   - Specializes in: File search, organization, dependency analysis
   - Knowledge: File system patterns, project structures

3. **CodeAnalysisExpert** (Planned)
   - Model: CodeLlama 13B
   - Specializes in: Code review, refactoring, best practices

4. **DocumentationExpert** (Planned)
   - Model: Mistral 7B
   - Specializes in: API documentation, tutorials, how-to guides

5. **SystemAdminExpert** (Planned)
   - Model: Llama 2 7B
   - Specializes in: System config, performance tuning, troubleshooting

**Code Location:** `core/experts/`

#### Episodic Memory Layer

**Purpose:** Cross-expert knowledge sharing and learning

**Three-Database Architecture:**

1. **Vector Database (ChromaDB)**
   - Stores: Semantic embeddings of past tasks
   - Used for: Similarity search ("find similar past tasks")
   - Size: ~1GB for 100k episodes

2. **Graph Database (Neo4j)**
   - Stores: Relationships between tasks, experts, outcomes
   - Used for: Pattern discovery ("what typically follows debugging?")
   - Queries: Cypher

3. **Time-Series Database (DuckDB)**
   - Stores: Temporal patterns, usage analytics
   - Used for: Trend analysis ("user debugs more on Mondays")
   - Queries: SQL

**Memory Structure:**

```python
@dataclass
class Episode:
    timestamp: datetime
    trigger_event: SystemEvent
    expert_used: ExpertType
    task: str
    outcome: ExpertResponse
    user_feedback: Optional[float]  # 0.0-1.0
    context: Dict
```

**Learning Example:**

```python
# Episode 1: User debugs → needs file search
memory.record(
    expert="debugging",
    outcome="success",
    next_task="file_search"
)

# Episode 2-10: Same pattern repeats

# Memory learns: debugging → 80% probability → file_search
# Future: When debugging starts, pre-load file search expert
```

**Development Status:** 🟡 Basic implementation (Week 9-12)

**Code Location:** `core/memory/`

---

## Data Flow

### Scenario: User Starts Debugging Session

```
1. USER ACTION: Opens Visual Studio
   └─▶ [Kernel] Minifilter detects devenv.exe start
       └─▶ [Core] ETW Monitor captures process event
           └─▶ [Core] Event Correlation detects "debugging_session_start"
               └─▶ [Core] Master Router triggered
                   ├─▶ Analyzes recent 50 system events
                   ├─▶ Checks episodic memory for similar past sessions
                   └─▶ Routes to DebuggingExpert (confidence: 0.9)
                       ├─▶ Speculatively launches FileExpert (NPU)
                       └─▶ Speculatively launches DocExpert (NPU)

2. USER ACTION: Opens main.cpp
   └─▶ [Kernel] File access detected
       └─▶ [Core] DebuggingExpert analyzes file content
           ├─▶ Scans for recent crash patterns
           ├─▶ Loads related crash logs from memory
           └─▶ Prepares suggestions
               └─▶ [UI] Displays proactive assistance:
                   "Detected null pointer crash in main.cpp:45"
                   "Suggestion: Add null check before line 45"

3. USER VALIDATES: Accepts suggestion
   └─▶ [Core] Memory records successful episode
       └─▶ Updates graph: debugging → main.cpp → null_check
           └─▶ Learning: Next time user opens main.cpp, suggest null checks

4. LATER: User opens main.cpp again
   └─▶ [Core] Memory recalls past episode
       └─▶ [Core] Speculatively pre-loads null check suggestions
           └─▶ [UI] Instant response (<50ms latency)
```

### Data Flow Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    USER ACTIVITY                         │
└────────────┬─────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────┐
│ KERNEL EVENTS (ETW + Minifilter)                       │
│ • File: opened main.cpp                                 │
│ • Process: devenv.exe started                           │
│ • Network: docs.microsoft.com accessed                  │
└────────────┬───────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────┐
│ EVENT CORRELATION                                       │
│ Pattern: debugging_session (confidence: 0.95)           │
│ Intent: analyze_crash                                   │
│ Context: {recent_crashes: 3, files: [main.cpp, ...]}   │
└────────────┬───────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────┐
│ MASTER ROUTER (Phi-2 3B)                                │
│ Decision: route_to(DebuggingExpert)                     │
│ Alternatives: [FileExpert, DocExpert]                   │
│ Trigger: speculative_execution([FileExpert, DocExpert]) │
└────────────┬───────────────────────────────────────────┘
             │
             ├────────────┬────────────┬────────────────┐
             ▼            ▼            ▼                │
┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  Debugging  │  │    File     │  │     Doc     │     │
│   Expert    │  │   Expert    │  │   Expert    │     │
│   [GPU]     │  │   [NPU]     │  │   [NPU]     │     │
│  EXECUTED   │  │ SPECULATIVE │  │ SPECULATIVE │     │
└─────┬───────┘  └─────┬───────┘  └─────┬───────┘     │
      │                │                │              │
      │                │                │              │
      └────────────────┴────────────────┴──────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│ EPISODIC MEMORY                                         │
│ Record: expert=debugging, task=analyze_crash            │
│ Learn: debugging → often_needs → file_search            │
│ Store: vector_embedding, graph_relationship, timestamp  │
└────────────┬───────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────┐
│ USER RESPONSE                                           │
│ • Debugging suggestions displayed                       │
│ • Speculative results ready if user switches tasks      │
│ • Latency: <100ms                                       │
└────────────────────────────────────────────────────────┘
```

---

## Performance Characteristics

### Latency Targets

| Operation | Target | Current | Status |
|-----------|--------|---------|--------|
| Event capture (kernel → userland) | <5ms | TBD | 🟡 |
| Event correlation | <10ms | TBD | 🟡 |
| Master routing decision | <50ms | TBD | 🟡 |
| Expert execution | <500ms | TBD | 🟡 |
| **End-to-end (event → response)** | **<100ms** | **TBD** | **🟡** |
| Speculative hit | <20ms | TBD | 🔴 |

### Resource Usage

| Component | CPU | RAM | GPU/NPU | Disk |
|-----------|-----|-----|---------|------|
| ETW Monitor | <1% | 50MB | - | - |
| Master Router | 2-5% | 2GB | 20% | - |
| Expert (idle) | <1% | 1GB | - | - |
| Expert (active) | 20-40% | 3-5GB | 60% | - |
| Memory Layer | 1-2% | 500MB | - | 1GB |
| **Total (idle)** | **<5%** | **<4GB** | **<5%** | **~12GB** |
| **Total (active)** | **~50%** | **~10GB** | **~80%** | **~12GB** |

### Throughput

- **Concurrent queries**: 1-3 (limited by GPU memory)
- **Events/second**: Up to 10,000 (ETW can handle more if needed)
- **Memory episodes**: Up to 1 million (before needing cleanup)

---

## Future Enhancements

### Phase 2 (Weeks 17-24)

- **Quantum-Inspired Routing**: Probabilistic superposition of experts
- **Federated Learning**: Multi-device synchronization
- **Advanced Memory**: Reinforcement learning from user feedback

### Phase 3 (Months 3-6)

- **Voice Interface**: Natural language queries
- **Desktop UI**: Visual dashboard for agent activity
- **Plugin System**: Third-party experts

### Research Directions

- **Neural Architecture Search**: Auto-optimize expert selection
- **Continual Learning**: Experts improve without full retraining
- **Explainability**: Visualize why routing decisions were made

---

## References

- [Windows ETW Documentation](https://docs.microsoft.com/en-us/windows/win32/etw/about-event-tracing)
- [Minifilter Drivers](https://docs.microsoft.com/en-us/windows-hardware/drivers/ifs/filter-manager-concepts)
- [Mixture of Experts](https://arxiv.org/abs/1701.06538)
- [Speculative Decoding](https://arxiv.org/abs/2211.17192)

---

**Status**: Living document - Updated as architecture evolves