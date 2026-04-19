# TAU2 Benchmark Framework: Comprehensive Exploration Report

**Date**: April 11, 2026
**Scope**: Deep exploration of tau2 benchmark structure, domains, evaluation framework, and runner

---

## Executive Summary

TAU2 is a comprehensive benchmark framework for evaluating AI agents in task-oriented conversational scenarios. It supports multiple domains (retail, airline, telecom, mock, clinical) with structured task definitions, agent-environment-user interactions via a turn-based orchestrator, and multi-faceted evaluation metrics.

### Key Findings:
- **Framework Type**: Agent-Environment-User (AEU) architecture with turn-based orchestration
- **Active Domains**: 5 production domains + 7 clinical specialty subdomains
- **Evaluation**: Multi-metric approach (action accuracy, communication, environment state, clinical-specific metrics)
- **Tasks**: JSON-based with structured user scenarios, evaluation criteria, and optional ground-truth actions
- **Tools**: Decorator-based toolkit system with READ/WRITE/THINK/GENERIC classifications
- **API**: Azure OpenAI for LLM agent inference

---

## 1. Overall Directory Structure

```
/home/ubuntu/agentmy/src/tau2/
├── agent/              # Agent implementations (LLMAgent, LLMSoloAgent, GymAgent)
├── data_model/         # Pydantic models for tasks, messages, simulations
├── domains/            # Domain definitions (retail, airline, telecom, clinical, mock)
├── environment/        # Core environment system (toolkit, tools, DB, environment runner)
├── evaluator/          # Evaluation metrics and scoring
├── metrics/            # Metrics calculation utilities
├── orchestrator/       # Turn-based message orchestration
├── user/               # User simulator implementations
├── gym/                # Gym-compatible interface
├── scripts/            # Utility scripts
├── utils/              # Helper utilities
├── api_service/        # API service components
├── registry.py         # Domain and task registration
├── cli.py              # CLI interface
├── run.py              # Main execution runner
└── config.py           # Configuration management

/home/ubuntu/agentmy/data/tau2/domains/
├── retail/             # E-commerce domain (products, orders, exchanges, returns)
├── airline/            # Flight booking domain
├── telecom/            # Telecom support domain
├── mock/               # Mock/test domain
└── clinical/           # Medical consultation domains
    ├── cardiology/
    ├── endocrinology/
    ├── gastroenterology/
    ├── nephrology/
    ├── neurology/
    ├── chinese_internal_medicine/
    ├── primekg/        # PrimeKG-based domain
    └── data_sources/
```

---

## 2. Domain Organization and Pattern

### Standard Domain Structure

Each domain follows a consistent pattern:

```
domains/<domain_name>/
├── __init__.py              # Domain package init
├── data_model.py            # Pydantic BaseModel data classes (inherits from DB)
├── tools.py                 # ToolKit class with @is_tool decorated methods
├── user_tools.py            # (Optional) User-side tools
├── environment.py           # get_environment(), get_tasks(), get_tasks_split()
├── utils.py                 # Domain-specific utilities
└── (optional) user_data_model.py  # User-facing data model

data/tau2/domains/<domain_name>/
├── db.json or db.toml              # Static database
├── user_db.json or user_db.toml    # (Optional) User database
├── tasks.json                      # All tasks for domain
├── split_tasks.json                # Train/test/base splits with task IDs
├── policy.md                       # Agent behavioral policy/instructions
└── (optional) policy_solo.md       # Solo mode policy variant
```

### Example: Retail Domain (Complete E2E)

**Data Model** (`data_model.py`):
- `Variant`: Product variant with options, availability, price
- `Product`: Product with variants
- `User`: User with name, address, email, payment methods, order history
- `Order`: Order with items, status, fulfillments, payments, exchanges, returns
- `RetailDB`: Container for products, users, orders

**Tools** (`tools.py`, via `RetailTools` class):
- `find_user_id_by_name_zip(first_name, last_name, zip)` [READ]
- `get_user_details(user_id)` [READ]
- `get_order_details(order_id)` [READ]
- `get_product_details(product_id)` [READ]
- `search_products(query, limit)` [READ]
- `process_refund(order_id, items, payment_method_id)` [WRITE]
- `exchange_delivered_order_items(order_id, item_ids, new_item_ids, payment_method_id)` [WRITE]
- `create_order(...)` [WRITE]

**Environment** (`environment.py`):
```python
def get_environment(db=None, solo_mode=False) -> Environment:
    if db is None:
        db = RetailDB.load(RETAIL_DB_PATH)
    tools = RetailTools(db)
    policy = load_file(RETAIL_POLICY_PATH)
    return Environment(domain_name="retail", policy=policy, tools=tools)

def get_tasks(task_split_name="base") -> list[Task]:
    tasks = load_file(RETAIL_TASK_SET_PATH)
    # Filter by split if specified
    if task_split_name:
        task_splits = get_tasks_split()
        tasks = [t for t in tasks if t.id in task_splits[task_split_name]]
    return tasks
```

**Task Structure** (JSON in `tasks.json`):
```json
{
  "id": "0",
  "description": {
    "purpose": null,
    "relevant_policies": null,
    "notes": null
  },
  "user_scenario": {
    "persona": null,
    "instructions": {
      "task_instructions": "You are detail-oriented...",
      "domain": "retail",
      "reason_for_call": "You received your order #W2378156 and wish to exchange...",
      "known_info": "You are Yusuf Rossi in zip code 19122.",
      "unknown_info": "You do not remember your email address."
    }
  },
  "initial_state": null,
  "evaluation_criteria": {
    "actions": [
      {
        "action_id": "0_0",
        "name": "find_user_id_by_name_zip",
        "arguments": {"first_name": "Yusuf", "last_name": "Rossi", "zip": "19122"},
        "info": null
      },
      ...
    ],
    "communicate_info": [],
    "nl_assertions": null
  }
}
```

**Task Splits** (in `split_tasks.json`):
```json
{
  "train": ["0", "1", "2", ...],
  "test": ["5", "9", "12", ...],
  "base": ["0", "1", "2", ..., "5", "9", "12", ...]  // combined train + test
}
```

---

## 3. How Tools Are Defined for a Domain

### Tool Definition Pattern

Tools are defined in a **ToolKit** class using the `@is_tool()` decorator:

```python
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool

class RetailTools(ToolKitBase):
    db: RetailDB

    def __init__(self, db: RetailDB):
        super().__init__(db)

    @is_tool(ToolType.READ)
    def get_user_details(self, user_id: str) -> User:
        """Get user details.

        Args:
            user_id: The user ID (e.g., 'sara_doe_496')

        Returns:
            User object with details

        Raises:
            ValueError: If user not found
        """
        if user_id not in self.db.users:
            raise ValueError("User not found")
        return self.db.users[user_id]

    @is_tool(ToolType.WRITE)
    def create_order(self, user_id: str, items: List[OrderItem], ...) -> Order:
        """Create a new order."""
        # Implementation...
        pass
```

### Tool Categories

Tools are classified by `ToolType`:
1. **READ**: Queries/retrieves data without state modification
2. **WRITE**: Modifies persistent state
3. **THINK**: Computational/reasoning tools
4. **GENERIC**: Other operations

### Tool Extraction and Invocation

The `ToolKitBase` metaclass automatically extracts decorated tools:
- `tools` property: Dict[str, Callable] of all tools
- `get_tools()`: Returns Dict[str, Tool] with full OpenAI schema
- `use_tool(tool_name, **kwargs)`: Execute a tool
- `has_tool(tool_name)`: Check if tool exists

### Tool Schema Generation

Each tool is converted to OpenAI-compatible schema:
```python
Tool(
    name="get_user_details",
    short_desc="Get user details by ID",
    long_desc="Retrieves full user profile including name, address, email, payment methods, and order history",
    params=BaseModel,  # Pydantic model with function parameters
    returns=BaseModel,  # Return type
    raises=[...],  # Possible exceptions
    examples=[],
    info={...}  # Additional metadata
)
```

---

## 4. Task and Scenario Structure

### Task Model (from `data_model/tasks.py`)

```python
class Task(BaseModel):
    id: str
    description: Description  # purpose, relevant_policies, notes
    user_scenario: UserScenario
        persona: str  # General user description
        instructions: StructuredUserInstructions or str
            domain: str
            reason_for_call: str
            known_info: str
            unknown_info: str
            task_instructions: str
    initial_state: Optional[InitializationData]  # Environment setup actions
    evaluation_criteria: Optional[EvaluationCriteria]  # Ground truth for eval
```

### Evaluation Criteria Structure

```python
class EvaluationCriteria(BaseModel):
    actions: List[Action]  # Expected tool calls with args
    communicate_info: List[str]  # Communication assertions
    nl_assertions: Optional[str]  # Natural language assertions
```

Each `Action`:
```python
class Action(BaseModel):
    action_id: str  # Unique ID within task
    requestor: str  # "assistant" or "user"
    name: str  # Tool name
    arguments: dict  # Expected arguments
    info: Optional[str]  # Explanation
    compare_args: Optional[List[str]]  # Which args to compare (all if None)
```

### Clinical Task Specifics

Clinical tasks extend standard tasks with medical context:

```json
{
  "id": "clinical_internal_medicine_0",
  "description": {
    "purpose": "Medical consultation - 高血压患者能吃党参吗？",
    "relevant_policies": null,
    "notes": "Real Chinese medical dialogue from 内科. Source: Chinese MedDialog Dataset."
  },
  "user_scenario": {
    "persona": "None-year-old None patient with 高血压患者能吃党参吗？",
    "instructions": {
      "domain": "internal_medicine",
      "reason_for_call": "高血压患者能吃党参吗？",
      "known_info": "医生开了什么降压药，但我记不清名字了...",
      "task_instructions": "You are a patient seeking medical advice..."
    }
  },
  "initial_state": {
    "initialization_actions": [
      {
        "env_type": "user",
        "func_name": "set_user_info",
        "arguments": {"name": "David Davis", "mrn": "MRN681805", ...}
      },
      {
        "env_type": "user",
        "func_name": "set_medical_persona",
        "arguments": {
          "age": null,
          "gender": null,
          "symptoms": ["高血压..."],
          "past_medical_history": [],
          "current_medications": [],
          "allergies": [],
          "lab_results": {},
          "vital_signs": {}
        }
      }
    ]
  }
}
```

---

## 5. Evaluation Metrics and Framework

### Evaluation Types (from `evaluator/evaluator.py`)

```python
class EvaluationType(str, Enum):
    ENV = "env"                          # Environment state changes
    COMMUNICATE = "communicate"          # Communication quality
    ACTION = "action"                    # Tool action correctness
    ALL = "all"                          # Combined: env + action + communicate
    NL_ASSERTIONS = "nl_assertions"      # Natural language assertions
    ALL_WITH_NL_ASSERTIONS = "all_with_nl_assertions"
    CLINICAL = "clinical"                # Clinical-specific evaluation
    ALL_WITH_CLINICAL = "all_with_clinical"
```

### Available Evaluators

1. **ActionEvaluator** (`evaluator_action.py`)
   - Compares agent tool calls against ground-truth actions
   - Argument matching (exact or by specified keys)
   - Scores: match%, partial match%, missed actions

2. **EnvironmentEvaluator** (`evaluator_env.py`)
   - Verifies environment state changes match expected outcomes
   - Executes actions and validates final state

3. **CommunicateEvaluator** (`evaluator_communicate.py`)
   - Evaluates user-agent communication quality
   - Fluency, coherence, safety

4. **ClinicalEvaluator** (`evaluator_clinical.py`)
   - Medical-specific evaluation
   - Diagnosis accuracy, medication appropriateness
   - Safety and ethical compliance

5. **ClinicalCapabilityEvaluator** (`evaluator_clinical_capability.py`)
   - Advanced clinical assessment with multiple modules
   - Modules: no_hallucination_diagnosis, medication_guidance, tool_selection, parameter_extraction, reasoning_chain, safety
   - Weighted scoring with customizable module enablement
   - LLM-based judgment with fallback to rule-based checks

6. **NLAssertionsEvaluator** (`evaluator_nl_assertions.py`)
   - Natural language assertion checking
   - Uses LLM to verify free-form success criteria

### Reward Info Structure

```python
class RewardInfo(BaseModel):
    reward: float  # Final score [0.0, 1.0]
    reward_basis: Optional[dict]  # Score breakdown
    info: dict  # Additional details and explanations
```

### Evaluation Execution Flow

```
evaluate_simulation(simulation, task, evaluation_type, solo_mode, domain)
  ├─ Check termination reason (must be AGENT_STOP or USER_STOP)
  ├─ Check if task has evaluation_criteria
  └─ Call appropriate evaluator based on evaluation_type:
      ├─ ENV → EnvironmentEvaluator.calculate_reward()
      ├─ ACTION → ActionEvaluator.calculate_reward()
      ├─ COMMUNICATE → CommunicateEvaluator.calculate_reward()
      ├─ CLINICAL → ClinicalEvaluator.calculate_reward()
      └─ ALL* → Combine multiple evaluators with weighted averaging
```

---

## 6. Benchmark Runner and Execution

### Main Runner (`run.py`)

**Key Functions:**

```python
def get_tasks(task_set_name, task_split_name=None, task_ids=None, num_tasks=None)
    → loads tasks from registry, filters by split/IDs, limits count

def run_one_task(task, config) → SimulationRun
    Creates orchestrator, runs agent-user-environment loop, returns results

def run_batch(tasks, config) → List[SimulationRun]
    Runs multiple tasks in parallel/sequential, aggregates results

def make_run_name(config) → str
    Generates run identifier from config
```

### Orchestrator (`orchestrator/orchestrator.py`)

The **Orchestrator** manages turn-based interactions between Agent, User, and Environment:

```
Orchestrator(
    domain: str,
    agent: BaseAgent,        # LLMAgent, LLMSoloAgent, GymAgent
    user: BaseUser,          # UserSimulator or DummyUser
    environment: Environment,  # Tools, policy, DB
    task: Task,
    max_steps: int = 100,
    max_errors: int = 10,
    solo_mode: bool = False,
    validate_communication: bool = False
)
```

**Communication Protocol:**

```
Agent (AssistantMessage)
  ├─ Text → User
  ├─ ToolCall(s) → Environment
  │   └─ ToolMessage (from Environment) → Agent

User (UserMessage)
  ├─ Text → Agent
  └─ ToolCall(s) → Environment
      └─ ToolMessage (from Environment) → User

Environment
  └─ Executes tool calls from agent/user, returns ToolMessage/MultiToolMessage

Termination Triggers:
  • Agent sends "###STOP###" signal
  • User sends "###STOP###" signal
  • max_steps reached
  • max_errors reached
  • Protocol violation detected (if validate_communication=True)
```

**Solo Mode** (for autonomous agents):
- Agent can ONLY make tool calls (no text to user)
- Exception: ###STOP### signal allowed
- User = DummyUser (no actual interaction)
- Environment is sole interaction target

### RunConfig Structure

```python
class RunConfig(BaseModel):
    domain: str                        # Domain to run
    task_set_name: str                # Task set identifier
    task_split_name: Optional[str]    # train/test/base split
    task_ids: Optional[List[str]]     # Specific task IDs to run
    agent_config: AgentConfig         # Agent setup
    user_config: UserConfig           # User simulator config
    evaluation_type: EvaluationType   # Evaluation method
    num_tasks: Optional[int]          # Limit task count
    max_parallel: int = 4             # Parallel execution workers
    seed: Optional[int]               # Random seed
    output_dir: str                   # Results directory
```

### Results Storage

Results saved to `output_dir` with structure:
```
<output_dir>/
├── run_results.json          # Aggregate results
├── <task_id>/
│   ├── simulation.json       # Full message history
│   ├── reward.json           # Evaluation scores
│   └── metadata.json         # Task metadata
├── metrics.csv               # Aggregated metrics
└── config.json               # Run configuration
```

---

## 7. Existing Clinical Healthcare Content

### Clinical Domains Implemented

1. **Cardiology** (`domains/clinical/cardiology/`)
   - **Data Model**: VitalSigns, CardiacTest, PatientRecord
   - **Tools**:
     - `assess_blood_pressure()` - BP classification (ACC/AHA guidelines)
     - `calculate_qtc()` - QTc calculation (Bazett's formula)
     - `interpret_heart_rate()` - HR assessment
     - `get_patient_by_mrn()` - Patient lookup
   - **Tasks**: Tasks in `/data/tau2/domains/clinical/cardiology/tasks.json`
   - **Policy**: `/data/tau2/domains/clinical/cardiology/policy.md`

2. **Endocrinology** (`domains/clinical/endocrinology/`)
   - **Data Model**: HormoneLevels, PatientRecord
   - **Focuses**: Diabetes, thyroid, hormonal disorders
   - **Lab Values**: Glucose, HbA1c, TSH, T4, T3, cortisol, insulin

3. **Gastroenterology** (`domains/clinical/gastroenterology/`)
   - **Focuses**: Digestive system, GI tract disorders

4. **Nephrology** (`domains/clinical/nephrology/`)
   - **Focuses**: Kidney disease, renal function assessment

5. **Neurology** (`domains/clinical/neurology/`)
   - **Focuses**: Nervous system, neurological conditions
   - **Policy Available**: `/data/tau2/domains/clinical/neurology/policy.md`

6. **Chinese Internal Medicine** (`domains/clinical/chinese_internal_medicine/`)
   - **Data Sources**: Real Chinese medical dialogues (MedDialog Dataset)
   - **Tasks**: Multiple versions available:
     - `tasks_realistic_v3.json` (latest)
     - `tasks_realistic.json`
     - `tasks_enhanced.json`
     - `tasks_with_agent_workflow.json`
   - **Examples**: High blood pressure + herbal medicine interactions, etc.
   - **Format**: Chinese text with English translations

### Clinical Data Source Infrastructure

**PrimeKG Integration** (`domains/clinical/primekg/`)
- Knowledge graph for medical entity relationships
- Disease-symptom mappings
- Used for task generation and context enrichment

**User Simulator for Clinical** (`clinical/user_simulator.py`)
```python
class ClinicalUserDB(BaseModel)
    """User database for clinical simulations"""

class ClinicalUserTools(ToolKitBase)
    """Tools available to patient users"""
    • set_user_info()
    • set_medical_persona()
    • report_symptoms()
    • ask_question()
```

**Clinical Task Initialization**
```python
class MedicalPersona(BaseModel):
    age: Optional[int]
    gender: Optional[str]
    symptoms: List[str]
    duration: Optional[str]
    severity: Optional[str]
    past_medical_history: List[str]
    current_medications: List[str]
    allergies: List[str]
    lab_results: Dict
    vital_signs: Dict
    smoking_status: Optional[str]
    alcohol_use: Optional[str]
```

### Clinical Evaluation Capabilities

**Clinical-Specific Metrics** (`evaluator/evaluator_clinical*.py`):
1. **Diagnosis Accuracy**: Evaluates diagnostic reasoning
2. **Medication Appropriateness**: Checks drug selection against guidelines
3. **Safety Compliance**: Ensures adherence to medical safety standards
4. **Hallucination Detection**: Prevents made-up medical facts
5. **Tool Selection Correctness**: Proper diagnostic/assessment tool usage
6. **Parameter Accuracy**: Correct parameter extraction for medical calculations

**Tool Categories** (`clinical/tool_categories.py`):
Organized by type:
- Diagnostic tools (labs, imaging, assessment)
- Therapeutic tools (prescribing, procedures)
- Communication tools (patient education)
- Safety tools (drug interactions, contraindications)

---

## 8. API Keys and Configuration

### Environment Configuration (`.env`)

```
AZURE_API_KEY=<azure-key>
AZURE_API_BASE=https://ilya-2751-resource.openai.azure.com
AZURE_API_VERSION=2024-12-01-preview
```

**Available API**:
- Azure OpenAI endpoint configured
- Supports GPT-4 and other OpenAI models
- Used for LLM agent inference and evaluation

### Configuration System

**CLI Interface** (`cli.py`):
```
$ python -m tau2 run --domain <domain> --task-set <task_set> \
    --agent-config <config> --evaluation-type <type>
```

**Supported Domains**:
- `retail`, `airline`, `telecom`, `mock`
- `clinical_cardiology`, `clinical_endocrinology`, `clinical_gastroenterology`
- `clinical_nephrology`, `clinical_neurology`, `clinical_chinese_internal_medicine`
- `primekg`

---

## 9. Core Data Models and Message Flow

### Message Types (`data_model/message.py`)

```python
class Message(BaseModel):
    role: str  # "user", "assistant", "environment"
    content: Optional[str]  # Text content
    tool_calls: Optional[List[ToolCall]]  # Tool invocations
    tool_call_id: Optional[str]  # Reference to parent tool call
    cost: float  # LLM cost

class AssistantMessage(Message):
    role = "assistant"
    # Can contain text OR tool_calls, not both

class UserMessage(Message):
    role = "user"
    # Can contain text OR tool_calls, not both

class ToolMessage(Message):
    role = "environment"
    # Always contains tool result

class MultiToolMessage(Message):
    role = "environment"
    # Wraps multiple ToolMessages for batch calls
```

### Simulation Run (`data_model/simulation.py`)

```python
class SimulationRun(BaseModel):
    id: str
    task_id: str
    domain: str
    messages: List[Message]  # Full interaction history
    termination_reason: TerminationReason  # How simulation ended
    num_steps: int
    timestamp: datetime
    metadata: dict
```

### Agent Types

1. **LLMAgent**: Standard agent with text+tool_call capability
2. **LLMSoloAgent**: Autonomous agent (tool calls only, no text to user)
3. **LLMGTAgent**: Goal-tracking variant
4. **GymAgent**: Gym-compatible interface for RL training

---

## 10. Key Integration Points for Development

### Registering a New Domain

1. Create domain structure under `domains/<domain_name>/`
2. Implement `get_environment()`, `get_tasks()`, `get_tasks_split()`
3. Add registrations in `registry.py`:
```python
from tau2.domains.custom.environment import get_environment as custom_get_environment
registry.register_domain(custom_get_environment, "custom")
registry.register_tasks(custom_get_tasks, "custom")
```

### Adding New Evaluation Metrics

1. Create evaluator class inheriting `EvaluatorBase`
2. Implement `calculate_reward(task, full_trajectory, **kwargs) → RewardInfo`
3. Add to `evaluator.py` evaluation type switch
4. Register in `EvaluationType` enum

### Clinical Domain Extension

1. Create new medical specialty under `domains/clinical/<specialty>/`
2. Define data models with medical fields (vital signs, lab results, medications, etc.)
3. Implement clinical tools with medical guidelines
4. Create tasks with realistic medical scenarios
5. Use `ClinicalEvaluator` or `ClinicalCapabilityEvaluator` for evaluation

---

## 11. Project Principles (from CLAUDE.md)

### Core Problems Identified
1. **Build Better User Persona**: Remove unrelated user info, focus on medically relevant patient details
2. **Improve Tools and Evaluation Quality**: Better classification of actions (suggestions vs. diagnosis vs. treatment) with domain-specific evaluation criteria
3. **Expand Data Sources**: Real clinical data, knowledge graphs (PrimeKG), disease-symptom mappings

### Data Integration Needs
- Clinical dialogues from real medical conversations
- PrimeKG for disease-symptom relationships
- Knowledge graphs for diagnostic support
- More diverse clinical scenarios

### Development Priorities
1. Task generation from knowledge graphs + LLM enrichment
2. Better evaluation metrics for clinical reasoning
3. More conversational turns with tool usage
4. Explicit evaluation criteria for different agent action types

---

## 12. Files and Paths Reference

### Critical Framework Files
- `src/tau2/run.py` - Main execution entry point
- `src/tau2/registry.py` - Domain/task registration
- `src/tau2/orchestrator/orchestrator.py` - Agent-user-env orchestration
- `src/tau2/environment/environment.py` - Environment base class
- `src/tau2/environment/toolkit.py` - ToolKit base and decorator system
- `src/tau2/evaluator/evaluator.py` - Main evaluation dispatcher

### Domain Template Files
- Each domain has: `environment.py`, `data_model.py`, `tools.py`, `utils.py`
- Data files: `db.json`, `tasks.json`, `split_tasks.json`, `policy.md`

### Clinical-Specific Files
- `src/tau2/domains/clinical/user_simulator.py` - Clinical user simulation
- `src/tau2/domains/clinical/tool_categories.py` - Medical tool organization
- `src/tau2/evaluator/evaluator_clinical*.py` - Clinical evaluation (4 files)
- Data: `/data/tau2/domains/clinical/<specialty>/tasks*.json` (multiple versions)

### Testing and Validation
- Tests organized under `tests/domain_tests/<domain_name>/`
- Run: `pytest tests/domain_tests/<domain_name>/`

---

## Appendix: Retail Domain Complete End-to-End Flow

### 1. Initialize
```python
from tau2.domains.retail.environment import get_environment, get_tasks

env = get_environment()  # Loads db.json with 100 products, 50 users, 1000 orders
tasks = get_tasks("base")  # Loads 114 retail tasks
```

### 2. Create Agent + User + Orchestrator
```python
from tau2.agent.llm_agent import LLMAgent
from tau2.user.user_simulator import UserSimulator
from tau2.orchestrator.orchestrator import Orchestrator

agent = LLMAgent(model="gpt-4", ...)
user = UserSimulator(scenario=task.user_scenario, ...)
orchestrator = Orchestrator(
    domain="retail",
    agent=agent,
    user=user,
    environment=env,
    task=task,
    max_steps=100
)
```

### 3. Run Simulation
```python
simulation = orchestrator.run()
# Returns SimulationRun with:
# - messages: [AssistantMessage, UserMessage, ToolMessage, ...]
# - termination_reason: AGENT_STOP or USER_STOP
# - num_steps: actual steps taken
```

### 4. Evaluate Results
```python
from tau2.evaluator.evaluator import evaluate_simulation, EvaluationType

reward_info = evaluate_simulation(
    simulation=simulation,
    task=task,
    evaluation_type=EvaluationType.ALL,  # Combines env+action+communicate
    solo_mode=False,
    domain="retail"
)
# Returns RewardInfo with:
# - reward: 0.85 (overall score)
# - reward_basis: {"env_score": 0.9, "action_score": 0.8, "communicate_score": 0.85}
# - info: {"notes": "All required actions performed correctly"}
```

### 5. Example Task Execution
**Task**: User wants to exchange keyboard + thermostat, but only if exact keyboard variant exists

**Expected Actions**:
1. `find_user_id_by_name_zip("Yusuf", "Rossi", "19122")` → "yusuf_rossi_496"
2. `get_order_details("#W2378156")` → Order with keyboard + thermostat
3. `get_product_details("1656367028")` → Check available keyboard options
4. `get_product_details("4896585277")` → Check thermostat options
5. `exchange_delivered_order_items(...)` → Execute exchange

**Evaluation**: Tool action matcher compares actual calls against ground truth, scoring match accuracy

---

**End of Report**

This exploration provides a solid foundation for understanding tau2's architecture, extending it for clinical domains, and developing new evaluation metrics aligned with the project's clinical benchmarking goals.
