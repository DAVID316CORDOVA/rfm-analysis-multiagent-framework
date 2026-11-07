# RFM-LDE Multiagent API Specification

## Overview

RESTful API for conversational multi-turn interactions with the RFM-LDE clustering system.

**Endpoint:** AWS Lambda HTTP Function URL  
**Authentication:** API Key (header: `X-API-Key`)  
**Response Format:** JSON  
**Timeout:** 30 seconds  

---

## 1. Chat Endpoint

### POST `/` (Lambda Function URL)

Process a user message and return multiagent response with group context and specialist results.

#### Request

```json
{
  "historial": [
    {
      "role": "user",
      "content": "tell me about the new players"
    },
    {
      "role": "assistant",
      "content": "In cluster 0 (new players), we have..."
    }
  ],
  "estado": {
    "grupo": {
      "cluster": 0,
      "quintil": null,
      "run_date": "2026-11-06",
      "subgrupo_producto": null
    },
    "periodo": {
      "type": "relative",
      "value": "last_week"
    }
  }
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `historial` | Array | Yes | Message history (user + assistant turns) |
| `historial[].role` | String | Yes | "user" or "assistant" |
| `historial[].content` | String | Yes | Message text |
| `estado.grupo` | Object | Yes | Current cluster/quintile group |
| `estado.grupo.cluster` | Integer | No | 0-3 or null for all |
| `estado.grupo.quintil` | Integer | No | 1-5 or null for all |
| `estado.periodo` | Object | Yes | Time range for query |
| `estado.periodo.type` | String | Yes | "relative" or "absolute" |
| `estado.periodo.value` | String | Yes | e.g., "last_week" or "2026-10-01:2026-11-06" |

#### Response

```json
{
  "respuesta": "In cluster 0, there are 31,200 new players. In the last week...",
  "grupo": {
    "cluster": 0,
    "quintil": null,
    "run_date": "2026-11-06",
    "subgrupo_producto": null
  },
  "pasos": ["supervisor", "grafico", "responder"],
  "artefacto": {
    "tipo": "chart_svg",
    "contenido": "<svg>...</svg>"
  },
  "timestamp": "2026-11-06T15:30:00Z"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `respuesta` | String | Natural language response in Spanish |
| `grupo` | Object | Updated group context (for next request) |
| `pasos` | Array | Specialist agents called: aadd, bonos, depositos_retiros, etc. |
| `artefacto` | Object | Optional export (csv, json, chart_svg) |
| `timestamp` | String | ISO 8601 timestamp of response |

#### Error Response

```json
{
  "error": "Invalid cluster ID: 5",
  "error_code": "INVALID_PARAMETERS",
  "timestamp": "2026-11-06T15:30:00Z"
}
```

---

## 2. Specialist Endpoints (Internal)

These are called internally by the supervisor agent via LangGraph.

### AADD Specialist

**Tools:**
- `consultar_apuestas_aadd` — Total bets and volumes
- `listar_ligas` — Available leagues
- `rentabilidad_partidos_aadd` — Profitable/unprofitable matches

### Deposits/Withdrawals Specialist

**Tools:**
- `consultar_depositos_retiros` — Player financial flows

### GGW/Sales Specialist

**Tools:**
- `consultar_ventas_ggw` — Net sales, GGW (max 31 days)

### Export Specialist

**Tools:**
- `exportar_jugadores` — CSV/JSON export with live autoexclude filtering

### Graphics Specialist

**Tools:**
- `perfil_clusters` — Cluster profile visualization
- `dispersion_clusters` — Feature scatter plots
- `distribucion_clusters` — Value distribution by cluster

### Methodology Specialist

**Tools:**
- `metodologia` — Model training details
- `calidad_modelo` — Quality metrics (Spearman, Silhouette)

---

## 3. Authentication

Include API key in request headers:

```bash
curl -X POST https://your-lambda-url.lambda-url.us-east-1.on.aws \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## 4. Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `INVALID_PARAMETERS` | 400 | Cluster/quintile out of range or invalid period |
| `AMBIGUOUS_GROUP` | 400 | Multiple interpretations (need clarification) |
| `ATHENA_TIMEOUT` | 504 | Query exceeded 30-second timeout |
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `NOT_FOUND` | 404 | Cluster/data not found in latest segmentation |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## 5. Rate Limits

- **Max requests/minute:** 60 per API key
- **Max concurrent:** 10 per key
- **Max response time:** 30 seconds
- **Max output tokens:** 4,096

---

## 6. Example Flows

### Flow 1: Ask about new players

```python
import requests

api_url = "https://your-lambda-url.lambda-url.us-east-1.on.aws"
headers = {"X-API-Key": "your-api-key"}

# Initial request
response = requests.post(
    api_url,
    json={
        "historial": [{"role": "user", "content": "Tell me about new players"}],
        "estado": {
            "grupo": {"cluster": 0, "quintil": None, "run_date": "2026-11-06"},
            "periodo": {"type": "relative", "value": "last_week"}
        }
    },
    headers=headers
)

result = response.json()
print(result["respuesta"])
# Output: "In cluster 0 (New Players), there are..."

# Follow-up question
response2 = requests.post(
    api_url,
    json={
        "historial": result["historial"] + [
            {"role": "user", "content": "Which league has highest volume?"}
        ],
        "estado": result["estado"]  # Keep previous context
    },
    headers=headers
)
```

### Flow 2: Export player list

```python
response = requests.post(
    api_url,
    json={
        "historial": [
            {"role": "user", "content": "Export cluster 2, quintile 5 to CSV"}
        ],
        "estado": {
            "grupo": {"cluster": 2, "quintil": 5, ...},
            "periodo": {...}
        }
    },
    headers=headers
)

if response.json().get("artefacto"):
    artifact = response.json()["artefacto"]
    if artifact["tipo"] == "csv":
        print(f"CSV size: {len(artifact['contenido'])} bytes")
```

---

## 7. Data Retention & Caching

- **Cluster data:** Updated weekly (Monday 07:00 Lima)
- **Response cache:** 5 minutes per unique query
- **Athena queries:** Cached in S3 for 24 hours
- **Historical data:** Full 12-week window available

---

**API Version:** 2.0  
**Last Updated:** 2026-11-06  
**Status:** Production
