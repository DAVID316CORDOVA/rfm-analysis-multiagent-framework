"""
Test suite for RFM-LDE Multiagent

Includes:
- Unit tests for each specialist agent
- Integration tests for multi-agent flows
- State management tests
- Mock Athena/Kambi responses
"""

import pytest
import os

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"


@pytest.fixture
def mock_athena_client():
    """Mock Athena client for testing"""
    class MockAthena:
        async def execute_query(self, query):
            return {"status": "SUCCEEDED", "rows": []}
    return MockAthena()


@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        "AWS_REGION": "us-east-1",
        "ATHENA_DATABASE": "dwh_raw_pe",
        "ENVIRONMENT": "testing",
    }
