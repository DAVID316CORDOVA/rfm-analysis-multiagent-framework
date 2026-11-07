"""
Example Usage of RFM-LDE Multiagent

This script demonstrates how to interact with the multiagent system
for analyzing player clusters, churn risk, and behavioral patterns.

Examples included:
1. Query cluster overview
2. Get AADD betting statistics
3. Export player list
4. Multi-turn conversation
"""

import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Example 1: Initialize conversation state
def create_initial_state():
    """
    Create initial conversation state for a new session.

    Returns:
        Dictionary with empty history and default group/period
    """
    return {
        "historial": [],
        "estado": {
            "grupo": {
                "cluster": 0,
                "quintil": None,
                "run_date": "2026-11-06",
                "subgrupo_producto": None
            },
            "periodo": {
                "type": "relative",
                "value": "last_week"
            }
        }
    }


# Example 2: Single turn interaction
async def single_turn_query(user_message: str):
    """
    Send a single question to the multiagent and get response.

    Args:
        user_message: User's question in Spanish
    """
    logger.info(f"User: {user_message}")

    # In production, this would call the Lambda endpoint
    # response = requests.post(lambda_url, json=state, headers={"X-API-Key": api_key})

    # Mock response for demonstration
    mock_response = {
        "respuesta": f"Analyzing {user_message}...",
        "grupo": {"cluster": 0, "quintil": None, "run_date": "2026-11-06"},
        "pasos": ["supervisor", "aadd", "responder"],
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Assistant: {mock_response['respuesta']}")
    return mock_response


# Example 3: Multi-turn conversation
async def multi_turn_conversation():
    """
    Demonstrate multi-turn conversation maintaining context.

    Shows how the agent remembers cluster selection across turns.
    """
    state = create_initial_state()

    # Turn 1: Ask about cluster 0
    state["historial"].append({
        "role": "user",
        "content": "Cuéntame sobre los jugadores nuevos"
    })
    logger.info("Turn 1: Asking about new players")

    # Mock turn 1 response
    state["historial"].append({
        "role": "assistant",
        "content": "En cluster 0 (Jugadores Nuevos) hay 31,200 jugadores activos en la última semana."
    })

    # Turn 2: Follow-up question (cluster context persists)
    state["historial"].append({
        "role": "user",
        "content": "¿Cuál es la liga con mayor volumen?"
    })
    logger.info("Turn 2: Asking about top league (context: cluster 0)")

    # Mock turn 2 response
    state["historial"].append({
        "role": "assistant",
        "content": "En cluster 0, Premier League lidera con S/ 34,500 en apuestas."
    })

    logger.info("✅ Multi-turn conversation completed with persistent context")
    return state


# Example 4: Export request
async def request_export():
    """
    Request data export (CSV/JSON format).

    Shows how to get player lists for external analysis.
    """
    state = create_initial_state()
    state["grupo"]["cluster"] = 2
    state["grupo"]["quintil"] = 5

    state["historial"].append({
        "role": "user",
        "content": "Exporta jugadores de cluster 2, quintil 5 a CSV"
    })

    logger.info("Requesting CSV export for cluster 2, quintile 5")

    # Mock export response
    mock_response = {
        "respuesta": "Exportando 8,420 jugadores...",
        "artefacto": {
            "tipo": "csv",
            "contenido": "player_id,cluster,quintil,ggw_28d,deposits_count,withdrawals_count\n1001,2,5,150.50,3,1\n1002,2,5,225.00,4,2\n...",
            "tamano_bytes": 524000
        }
    }

    logger.info(f"✅ Export ready: {mock_response['artefacto']['tamano_bytes']} bytes")
    return mock_response


# Example 5: Filter by product segment
async def filter_by_product():
    """
    Query specific product segment (AADD vs Gaming vs Sports).

    Shows how to narrow down analysis to specific product lines.
    """
    state = create_initial_state()
    state["grupo"]["cluster"] = 1
    state["grupo"]["subgrupo_producto"] = "AADD"  # Only hybrid product players

    state["historial"].append({
        "role": "user",
        "content": "¿Cuál es el churn de AADD en cluster 1?"
    })

    logger.info("Querying AADD churn for cluster 1")

    mock_response = {
        "respuesta": "En cluster 1 (AADD), el churn semanal es 58% con 12,400 jugadores activos.",
        "grupo": state["grupo"]
    }

    logger.info(f"✅ Churn analysis: {mock_response['respuesta']}")
    return mock_response


# Example 6: Change time period
async def change_time_period():
    """
    Query with different time ranges (relative or absolute).

    Shows flexibility in historical analysis.
    """
    state = create_initial_state()

    # Relative period: last month
    state["periodo"]["value"] = "last_month"

    state["historial"].append({
        "role": "user",
        "content": "¿Cómo fue el mes pasado?"
    })

    logger.info("Querying data for last month")

    mock_response = {
        "respuesta": "En el último mes, cluster 0 creció 12% en volumen total."
    }

    logger.info(f"✅ {mock_response['respuesta']}")

    # Absolute period: specific date range
    state["periodo"]["type"] = "absolute"
    state["periodo"]["value"] = "2026-10-01:2026-10-31"

    state["historial"].append({
        "role": "user",
        "content": "Análisis del mes de octubre específicamente"
    })

    logger.info("Querying specific date range (Oct 1-31, 2026)")

    return state


async def main():
    """
    Run all usage examples.
    """
    logger.info("=" * 60)
    logger.info("RFM-LDE Multiagent - Usage Examples")
    logger.info("=" * 60)

    # Example 1
    logger.info("\n1️⃣ Creating initial state...")
    state = create_initial_state()
    logger.info(f"State: {json.dumps(state, indent=2)}")

    # Example 2
    logger.info("\n2️⃣ Single turn query...")
    await single_turn_query("Cuéntame sobre el cluster 0")

    # Example 3
    logger.info("\n3️⃣ Multi-turn conversation...")
    await multi_turn_conversation()

    # Example 4
    logger.info("\n4️⃣ Requesting export...")
    await request_export()

    # Example 5
    logger.info("\n5️⃣ Filtering by product...")
    await filter_by_product()

    # Example 6
    logger.info("\n6️⃣ Changing time period...")
    await change_time_period()

    logger.info("\n" + "=" * 60)
    logger.info("✅ All examples completed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
