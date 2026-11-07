# Integration with LangGraph - Complete Orchestration Guide

This document explains how the RFM-LDE Multiagent system integrates with LangGraph for multi-agent orchestration.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      AWS Lambda HTTP Request                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   lambda_handler()   │
                  │  - Validate API key  │
                  │  - Parse JSON state  │
                  │  - Call supervisor   │
                  └──────────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────────┐
        │    Supervisor Agent (LangGraph Graph)      │
        ├────────────────────────────────────────────┤
        │  1. INIT_TURN → Clear results, increment   │
        │  2. SUPERVISOR_DECISION → LLM routing      │
        │  3. EXECUTE_SPECIALISTS → Call 1+ agents   │
        │  4. AGGREGATE_RESULTS → Collect outputs    │
        │  5. RESPONDER → Format response            │
        └────────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │   AADD      │   │   BONOS     │   │   GGW       │
    │ Specialist  │   │ Specialist  │   │ Specialist  │
    │  (async)    │   │  (async)    │   │  (async)    │
    └─────────────┘   └─────────────┘   └─────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────────┐
        │         Response Aggregation               │
        │    - Merge specialist results              │
        │    - Format for client                     │
        │    - Add metadata (latency, timestamp)     │
        └────────────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Lambda HTTP Response │
                  │  {"respuesta": "...", │
                  │   "pasos": [...]}    │
                  └──────────────────────┘
```

---

## LangGraph Workflow Structure

### Node Definitions

#### 1. INIT_TURN Node
**Purpose:** Initialize turn state

```python
def init_turn(state):
    """Reset results, increment step counter"""
    state["resultados"] = {}
    state["pasos"] = state.get("pasos", 0) + 1
    state["paso_actual"] = "init_turn"
    return state
```

**State Changes:**
- `resultados` cleared (fresh start for this turn)
- `pasos` incremented (for loop detection)
- `paso_actual` set for logging

---

#### 2. SUPERVISOR_DECISION Node
**Purpose:** LLM routing decision

```python
async def supervisor_decision(state):
    """Use Claude to decide which specialists to call"""
    user_message = state["historial"][-1]["content"]
    
    # Prompt Claude with:
    # - User message
    # - Current cluster/quintile
    # - Conversation history
    
    # Claude returns:
    # {
    #   "cluster": 0-3,
    #   "quintil": 1-5,
    #   "specialists_needed": ["aadd", "bonos"],
    #   "needs_clarification": false
    # }
```

**LLM Prompt Flow:**
1. Get user message from `historial[-1]`
2. Send to Claude with system prompt (see `prompts/supervisor.md`)
3. Claude returns JSON with decision
4. Save to `state["decision"]`

**Decision Output Schema:**
```python
@dataclass
class DecisionSupervisor(BaseModel):
    cluster: Optional[int]  # 0-3 or None
    quintil: Optional[int]  # 1-5 or None
    specialists_needed: List[str]  # aadd, bonos, etc.
    needs_clarification: bool
    clarification_question: Optional[str]
```

---

#### 3. EXECUTE_SPECIALISTS Node
**Purpose:** Call each specialist in parallel

```python
async def execute_specialists(state):
    """Call required specialists with asyncio"""
    specialists_needed = state["decision"]["specialists_needed"]
    results = {}
    
    # Could use asyncio.gather() for parallelization:
    # tasks = [
    #     specialist.consultar_apuestas_aadd(...),
    #     specialist.consultar_bonos(...),
    # ]
    # results = await asyncio.gather(*tasks)
    
    state["resultados"] = results
    return state
```

**Specialist Calling Pattern:**

Each specialist is called with:
- `cluster`: From `state["grupo"]["cluster"]`
- `quintil`: From `state["grupo"]["quintil"]`
- `periodo`: From `state["periodo"]`
- Optional filters: `liga`, `estado`, etc.

**Example Calls:**
```python
# AADD specialist
result = await aadd_specialist.consultar_apuestas_aadd(
    cluster=state["grupo"]["cluster"],
    quintil=state["grupo"]["quintil"],
    periodo=state["periodo"],
    liga="Premier League"  # optional
)

# Bonos specialist
result = await bonos_specialist.consultar_bonos(
    cluster=state["grupo"]["cluster"],
    quintil=state["grupo"]["quintil"],
    periodo=state["periodo"]
)
```

---

#### 4. AGGREGATE_RESULTS Node
**Purpose:** Combine specialist outputs

```python
def aggregate_results(state):
    """Merge results from all specialists"""
    # All results stored in state["resultados"]
    # Format for responder node
    return state
```

**Results Structure:**
```python
state["resultados"] = {
    "aadd": {
        "total_apuestas": 4527,
        "volumen_total": 125480.50,
        ...
    },
    "bonos": {
        "total_bonos_asignados": 2847,
        "tasa_activacion": 67.5,
        ...
    }
}
```

---

#### 5. RESPONDER Node
**Purpose:** Format final response

```python
def responder(state):
    """Generate natural language response"""
    results = state["resultados"]
    
    # Build response text from results
    response_parts = []
    if "aadd" in results:
        response_parts.append(f"AADD: {results['aadd']['total_apuestas']} apuestas")
    if "bonos" in results:
        response_parts.append(f"Bonos: {results['bonos']['total_bonos_asignados']}")
    
    state["respuesta"] = " | ".join(response_parts)
    return state
```

---

## State Management

### State Structure (Pydantic Models)

```python
# Main conversation state
{
    "historial": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    
    "grupo": {
        "cluster": 0,           # 0-3 or None
        "quintil": 3,           # 1-5 or None
        "run_date": "2026-11-06",
        "subgrupo_producto": None
    },
    
    "periodo": {
        "type": "relative",
        "value": "last_week"
    },
    
    # Results (cleared at turn start)
    "resultados": {
        "aadd": {...},
        "bonos": {...}
    },
    
    # Metadata
    "pasos": 1,
    "paso_actual": "responder",
    "timestamp": "2026-11-06T15:30:00Z"
}
```

### State Persistence

**In Lambda (Stateless):**
- Client sends full state each request
- Lambda processes request
- Returns updated state to client
- Client maintains state for next request

**In Local/Stateful Mode:**
- Use LangGraph's `MemorySaver`:
```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# Later runs with same thread_id recall context
output = graph.invoke(state, config={"configurable": {"thread_id": "user-123"}})
```

---

## Async/Await Patterns

### Async Specialists

All specialists use async methods for non-blocking I/O:

```python
class AaddSpecialist:
    async def consultar_apuestas_aadd(
        self,
        cluster: int,
        quintil: int,
        periodo: Dict[str, str]
    ) -> Dict[str, Any]:
        """Async method using await"""
        # Await Athena query
        results = await self.athena_client.execute_query(query)
        return results
```

### Running Async in Lambda

Lambda handler is synchronous, but can run async code:

```python
def lambda_handler(event, context):
    # Get event loop
    loop = asyncio.get_event_loop()
    
    # Run async supervisor
    result = loop.run_until_complete(supervisor.invoke(state))
    
    return format_response(result)
```

---

## Error Handling & Resilience

### Try/Except Pattern

Each specialist wraps calls in try/except:

```python
async def consultar_apuestas_aadd(self, ...):
    try:
        result = await self.athena_client.execute_query(...)
        return result
    except Exception as e:
        self.logger.error(f"Error: {str(e)}")
        return {"error": str(e), "total_apuestas": 0}
```

### Supervisor Resilience

If a specialist fails, supervisor continues with others:

```python
for spec_name in specialists_needed:
    try:
        result = await specialist.do_work(...)
        results[spec_name] = result
    except Exception as e:
        logger.error(f"Specialist {spec_name} failed: {e}")
        results[spec_name] = {"error": str(e)}
```

---

## Integration Points

### With Athena (Data)

Specialists query Athena for player cluster data:

```python
# In specialist __init__
self.athena_client = boto3.client('athena')

# In query method
response = await self.athena_client.execute_query(
    QueryString=sql_query,
    QueryExecutionContext={'Database': 'dwh_raw_pe'},
    ResultConfiguration={'OutputLocation': 's3://dlk-olimpo/athena-results/'}
)
```

### With S3 (Cache)

Cache cluster profiles in S3 for fast access:

```python
# Grafico specialist reads from S3
s3 = boto3.client('s3')
profile = s3.get_object(
    Bucket='dlk-olimpo',
    Key=f'rfm_lde/v3/profiles/cluster_{cluster}.json'
)
```

### With Anthropic API (LLM)

Supervisor uses Claude for routing decisions:

```python
from anthropic import Anthropic

client = Anthropic(api_key=settings.anthropic_api_key)

response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=1024,
    system=supervisor_system_prompt,
    messages=[{"role": "user", "content": decision_prompt}]
)
```

---

## Request/Response Flow

### Request Example

```bash
POST /lambda-url HTTP/1.1
X-API-Key: sk-...

{
  "historial": [
    {"role": "user", "content": "Tell me about AADD in cluster 0"}
  ],
  "estado": {
    "grupo": {
      "cluster": 0,
      "quintil": null,
      "run_date": "2026-11-06"
    },
    "periodo": {
      "type": "relative",
      "value": "last_week"
    }
  }
}
```

### Processing Flow

1. **lambda_handler** validates API key
2. **Supervisor.invoke()** starts LangGraph
3. **INIT_TURN** clears results
4. **SUPERVISOR_DECISION** calls Claude (decision: call ["aadd"])
5. **EXECUTE_SPECIALISTS** calls `aadd.consultar_apuestas_aadd()`
6. **RESPONDER** formats output
7. **Response** returned to client

### Response Example

```json
{
  "statusCode": 200,
  "body": {
    "respuesta": "En AADD cluster 0: 4527 apuestas, S/ 125,480.50 volumen total",
    "grupo": {
      "cluster": 0,
      "quintil": null,
      "run_date": "2026-11-06"
    },
    "pasos": ["init_turn", "supervisor_decision", "execute_specialists", "responder"],
    "timestamp": "2026-11-06T15:30:00Z",
    "latency_ms": 1250
  }
}
```

---

## Performance Optimization

### Caching

**Lambda Caching:**
```python
# Global instances cached across invocations
_supervisor = None
_llm_client = None

def get_supervisor():
    global _supervisor
    if _supervisor is None:
        _supervisor = Supervisor(...)  # Initialize once
    return _supervisor
```

**Warm Starts:** First invocation is ~2s, subsequent are ~500ms

### Parallelization

**Parallel Specialist Calls:**
```python
import asyncio

tasks = [
    aadd_specialist.consultar_apuestas_aadd(...),
    bonos_specialist.consultar_bonos(...),
    ventas_ggw_specialist.consultar_ventas_ggw(...)
]

results = await asyncio.gather(*tasks)
```

**Result:** 3 sequential calls (3s) → 3 parallel calls (1s)

---

## Deployment

### Deploy to AWS Lambda

```bash
# 1. Package
cd src/lambdas/rfm_lde_multiagente
pip install -r requirements.txt -t package/
cp -r ../../agents package/src/

# 2. Zip
cd package && zip -r ../lambda_function.zip .

# 3. Deploy
aws lambda update-function-code \
  --function-name rfm-lde-multiagente \
  --zip-file fileb://lambda_function.zip
```

### Environment Variables

Set in Lambda configuration:
- `ANTHROPIC_API_KEY` - Claude API key
- `AWS_REGION` - us-east-1
- `LAMBDA_API_KEY` - API key for requests
- `ENVIRONMENT` - production|staging|development

---

**Last Updated:** 2026-11-06  
**Version:** 2.0  
**Status:** Production
