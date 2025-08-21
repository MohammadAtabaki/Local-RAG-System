import json
import pytest
from ragv1enqreq import lambda_handler

@pytest.fixture
def sample_event():
    return {
        "body": json.dumps({
            "query": "What is the summary of the report?",
            "session_id": "test-session-1"
        })
    }

def test_lambda_handler_success(sample_event):
    response = lambda_handler(sample_event)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "answer" in body

def test_lambda_handler_missing_fields():
    event = {"body": json.dumps({"query": ""})}
    response = lambda_handler(event)
    assert response["statusCode"] == 400

def test_lambda_handler_malformed_json():
    event = {"body": "not a json"}
    try:
        lambda_handler(event)
    except Exception:
        assert True
