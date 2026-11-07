# Development Guide

Complete guide for developers contributing to RFM-LDE Multiagent.

## Architecture Overview

```
src/
├── agents/
│   ├── supervisor.py          # LLM decision engine (routes to specialists)
│   ├── especialistas/          # 7 specialist agents (single-responsibility)
│   │   ├── aadd.py
│   │   ├── bonos.py
│   │   ├── depositos_retiros.py
│   │   ├── exportar.py
│   │   ├── grafico.py
│   │   ├── metodologia.py
│   │   └── ventas_ggw.py
│   ├── herramientas/           # Athena queries & data tools
│   ├── prompts/                # LLM prompt templates
│   ├── utils/                  # Utility functions
│   └── estado.py               # State management
├── lambdas/
│   └── rfm_lde_multiagente/
│       ├── lambda_function.py  # AWS Lambda entry point
│       └── tools_athena/       # Athena integration
├── models/                      # Model loading & inference
└── config.py                    # Configuration management

tests/
├── unit/                        # Unit tests (fast, isolated)
├── integration/                 # Integration tests (require AWS)
└── fixtures/                    # Test data & mocks
```

## Design Patterns

### 1. Single Responsibility Principle

Each specialist agent handles ONE domain:
- `aadd.py` → Sports betting only
- `bonos.py` → Bonuses only
- `depositos_retiros.py` → Financial flows only

This makes testing, maintenance, and extension simple.

### 2. Async/Await Throughout

All I/O operations are async:
```python
async def consultar_apuestas_aadd(...) -> Dict[str, Any]:
    # All network calls are awaited
    results = await self.athena_client.execute_query(query)
    return results
```

### 3. State Persistence Without Coupling

State object travels through the LangGraph but specialists don't modify it:
```python
# Specialist receives state, returns results
results = specialist.do_work(cluster=state.grupo.cluster)
# Supervisor merges results back into state
state.resultados["aadd"] = results
```

### 4. Dependency Injection

Specialists receive clients (Athena, etc.) as constructor arguments:
```python
specialist = AaddSpecialist(athena_client=client)
```

This enables easy mocking in tests.

## Adding a New Specialist

### Step 1: Create the file

```bash
touch src/agents/especialistas/nuevo_especialista.py
```

### Step 2: Implement the class

```python
from typing import Any, Dict

class NuevoEspecialista:
    """Handle new domain area."""
    
    def __init__(self, athena_client=None):
        self.athena_client = athena_client
    
    async def consultar_nueva_metrica(
        self,
        cluster: int,
        quintil: int,
        periodo: Dict[str, str]
    ) -> Dict[str, Any]:
        """Query new metric for cluster."""
        # Implementation here
        return {"metric": 123}
```

### Step 3: Add tests

```bash
touch tests/unit/test_nuevo_especialista.py
```

```python
@pytest.mark.asyncio
async def test_consultar_nueva_metrica(specialist):
    result = await specialist.consultar_nueva_metrica(0, 3, {"type": "relative", "value": "last_week"})
    assert "metric" in result
```

### Step 4: Update supervisor routing

Edit `src/agents/prompts/supervisor.md` to include the new specialist in decision logic.

### Step 5: Register in __init__.py

```python
# src/agents/especialistas/__init__.py
from .nuevo_especialista import NuevoEspecialista
```

---

## Testing Strategy

### Unit Tests (Fast, No AWS)

Test individual specialists with mocked Athena:

```bash
pytest tests/unit -v
# ~2 seconds to run
```

**What to test:**
- Input validation
- Response format
- Error handling
- Edge cases

### Integration Tests (Require AWS)

Test full flows with real Athena:

```bash
pytest tests/integration -v
# ~30 seconds (requires AWS credentials)
```

**What to test:**
- Multi-specialist coordination
- State persistence
- Real Athena queries

### Fixtures

Mock data in `tests/fixtures/`:

```python
# tests/fixtures/mock_responses.py
MOCK_AADD_RESPONSE = {
    "total_apuestas": 4527,
    "volumen_total": 125480.50,
}
```

---

## Code Quality Standards

### Style Guide

- Follow PEP 8
- Max line length: 100 characters
- Use type hints for all functions

```python
async def do_something(
    cluster: int,
    periodo: Dict[str, str]
) -> Dict[str, Any]:
    """Do something with type hints."""
    pass
```

### Pre-commit Checks

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test

# Generate coverage
make test-cov
```

### Documentation

All public functions need docstrings:

```python
async def consultar_apuestas_aadd(
    self,
    cluster: int,
    quintil: int,
    periodo: Dict[str, str],
    liga: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query AADD bets for cluster.
    
    Args:
        cluster: Cluster ID (0-3)
        quintil: Quintile ID (1-5)
        periodo: Time period {"type": "relative"|"absolute", "value": "..."}
        liga: Optional league filter
        
    Returns:
        Dictionary with total_apuestas, volumen_total, num_jugadores
        
    Raises:
        ValueError: If cluster/quintil out of range
        AthenaException: If query fails
    """
```

---

## Common Tasks

### Debug a Specialist Query

```python
# tests/integration/test_debug.py
import logging
logging.basicConfig(level=logging.DEBUG)

async def test_debug_aadd():
    specialist = AaddSpecialist(athena_client=real_client)
    result = await specialist.consultar_apuestas_aadd(0, 3, {"type": "relative", "value": "last_week"})
    print(f"Result: {result}")
```

### Profile Performance

```bash
python -m cProfile -s cumtime src/lambdas/rfm_lde_multiagente/servidor_local.py
```

### Update Athena Queries

Edit `src/agents/herramientas/queries.py`:

```python
QUERY_APUESTAS = """
SELECT cluster, quintil, COUNT(*) as total
FROM rfm_lde_v3_modelados_semanal
WHERE cluster = {cluster}
GROUP BY cluster, quintil
"""
```

---

## Deployment Checklist

Before merging to main:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Code is formatted: `make format && make lint`
- [ ] Coverage > 80%: `make test-cov`
- [ ] Documentation is updated
- [ ] No hardcoded credentials
- [ ] No debug logging left in
- [ ] API contract is unchanged (or documented)

---

## Troubleshooting

### Tests fail with "No such table"

Athena table may have changed. Update query:

```bash
# Query Athena directly
aws athena start-query-execution \
  --query-string "SHOW TABLES FROM dwh_raw_pe" \
  --result-configuration OutputLocation=s3://dlk-olimpo/athena-results/
```

### Coverage drops below threshold

Missing test for a new function:

```bash
make test-cov  # Shows which lines aren't covered
```

### Performance regression

Profile the slow function:

```bash
python -m cProfile -s cumulative -m pytest tests/integration/test_slow.py
```

---

## Contributing

1. **Create feature branch:** `git checkout -b feature/new-specialist`
2. **Write tests first:** `tests/unit/test_new.py`
3. **Implement feature:** `src/agents/especialistas/new.py`
4. **Run checks:** `make test && make lint`
5. **Create MR:** Push and create merge request
6. **Code review:** Wait for approval
7. **Merge:** Squash commits if needed

---

**Last Updated:** 2026-11-06  
**Version:** 2.0  
**Status:** Active Development
