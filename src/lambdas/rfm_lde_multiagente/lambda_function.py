"""
AWS Lambda Entry Point for RFM-LDE Multiagent

Handles:
- HTTP requests from client
- Authentication (API key validation)
- State management
- Invokes supervisor agent
- Returns JSON response

This is the production entry point for the multiagent system.
"""

import json
import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict

import boto3
from anthropic import Anthropic

# Import agent components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from agents.supervisor import Supervisor
from agents.estado import EstadoGrafo, GrupoDefinicion, Periodo
from agents.especialistas.aadd import AaddSpecialist
from agents.especialistas.bonos import BonosSpecialist
from config import get_settings

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global instances (cached across Lambda invocations)
_supervisor = None
_llm_client = None


def get_llm_client():
    """Get or create Anthropic client (cached)"""
    global _llm_client
    if _llm_client is None:
        settings = get_settings()
        _llm_client = Anthropic(api_key=settings.anthropic_api_key)
    return _llm_client


def get_supervisor():
    """
    Get or create supervisor instance (cached).

    Caching across Lambda invocations saves initialization time.
    """
    global _supervisor
    if _supervisor is None:
        settings = get_settings()
        llm_client = get_llm_client()

        # Initialize specialists
        athena_client = boto3.client('athena', region_name=settings.aws_region)

        specialists = {
            "aadd": AaddSpecialist(athena_client=athena_client),
            "bonos": BonosSpecialist(athena_client=athena_client),
            # Other specialists would be initialized here
        }

        # Create supervisor
        _supervisor = Supervisor(llm_client=llm_client, specialists=specialists)
        logger.info("Supervisor initialized")

    return _supervisor


def validate_api_key(event: Dict[str, Any]) -> bool:
    """
    Validate API key from request headers.

    Args:
        event: Lambda event with headers

    Returns:
        True if valid, False otherwise
    """
    settings = get_settings()

    # Get key from headers
    headers = event.get("headers", {})
    api_key = headers.get("x-api-key") or headers.get("X-API-Key")

    if not api_key:
        logger.warning("Missing API key")
        return False

    # In production, verify against secret manager
    # valid = verify_api_key_in_secrets(api_key)
    # For now, simple comparison
    expected_key = os.environ.get("LAMBDA_API_KEY", settings.lambda_api_key)

    if api_key != expected_key:
        logger.warning(f"Invalid API key: {api_key[:10]}...")
        return False

    return True


def parse_request_body(body: str) -> Dict[str, Any]:
    """
    Parse and validate request body.

    Args:
        body: JSON string from Lambda event

    Returns:
        Parsed request data

    Raises:
        ValueError: If JSON invalid or missing required fields
    """
    try:
        data = json.loads(body) if isinstance(body, str) else body
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)}")

    # Validate required fields
    if "historial" not in data:
        raise ValueError("Missing 'historial' field")

    if "estado" not in data:
        raise ValueError("Missing 'estado' field")

    return data


def lambda_handler(event, context):
    """
    Main Lambda handler.

    Expected event structure:
    {
        "body": {
            "historial": [...],
            "estado": {...}
        },
        "headers": {
            "x-api-key": "..."
        }
    }

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        JSON response with statusCode, body
    """
    start_time = datetime.now()

    try:
        # Log request
        logger.info(f"Request from {event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')}")

        # 1. Validate API key
        if not validate_api_key(event):
            return {
                "statusCode": 401,
                "body": json.dumps({
                    "error": "Unauthorized",
                    "error_code": "INVALID_API_KEY",
                    "timestamp": datetime.now().isoformat()
                })
            }

        # 2. Parse request body
        try:
            body = event.get("body", "{}")
            if isinstance(body, str):
                body = json.loads(body)
            request_data = parse_request_body(body)
        except ValueError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": str(e),
                    "error_code": "INVALID_REQUEST",
                    "timestamp": datetime.now().isoformat()
                })
            }

        # 3. Reconstruct state
        historial = request_data.get("historial", [])
        estado_data = request_data.get("estado", {})

        state = {
            "historial": historial,
            "grupo": estado_data.get("grupo", {"cluster": None, "quintil": None}),
            "periodo": estado_data.get("periodo", {"type": "relative", "value": "last_week"}),
            "pasos": 0,
        }

        logger.info(f"State: cluster={state['grupo'].get('cluster')}, messages={len(historial)}")

        # 4. Get supervisor and invoke
        supervisor = get_supervisor()

        # Run supervisor (async)
        loop = asyncio.get_event_loop()
        result_state = loop.run_until_complete(supervisor.invoke(state))

        # 5. Format response
        response_body = {
            "respuesta": result_state.get("respuesta", "Sin respuesta"),
            "grupo": result_state.get("grupo", state["grupo"]),
            "pasos": result_state.get("pasos", []),
            "timestamp": datetime.now().isoformat(),
            "latency_ms": (datetime.now() - start_time).total_seconds() * 1000
        }

        logger.info(f"Success: {response_body['latency_ms']:.0f}ms, pasos={result_state.get('pasos', 0)}")

        return {
            "statusCode": 200,
            "body": json.dumps(response_body),
            "headers": {"Content-Type": "application/json"}
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "timestamp": datetime.now().isoformat(),
                "message": str(e) if os.environ.get("DEBUG") else None
            }),
            "headers": {"Content-Type": "application/json"}
        }


# Local testing (when running outside Lambda)
if __name__ == "__main__":
    # Mock event
    test_event = {
        "headers": {"x-api-key": "test-key"},
        "requestContext": {"identity": {"sourceIp": "127.0.0.1"}},
        "body": json.dumps({
            "historial": [{"role": "user", "content": "Cuéntame sobre AADD"}],
            "estado": {
                "grupo": {"cluster": 0, "quintil": 3},
                "periodo": {"type": "relative", "value": "last_week"}
            }
        })
    }

    # Mock context
    class MockContext:
        aws_request_id = "test-123"

    # Set environment
    os.environ["LAMBDA_API_KEY"] = "test-key"
    os.environ["DEBUG"] = "true"

    # Call handler
    response = lambda_handler(test_event, MockContext())
    print(json.dumps(json.loads(response["body"]), indent=2))
