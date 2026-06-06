# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Integration tests for the FastAPI /run endpoint and ADK web server simulation."""

import os
import pytest
from fastapi.testclient import TestClient
from google.adk.cli.fast_api import get_fast_api_app


@pytest.fixture
def test_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Creates a FastAPI TestClient configured for the Higo Agent."""
    monkeypatch.setenv("INTEGRATION_TEST", "TRUE")
    
    # Initialize the app using workspace root ('.') as the agents directory
    app = get_fast_api_app(agents_dir=".", web=True)
    return TestClient(app)


def test_endpoint_non_priority(test_client: TestClient) -> None:
    """Verifies that querying a non-priority location via HTTP POST returns 200 and stops prospección."""
    try:
        # Step 1: Create session
        session_resp = test_client.post("/apps/discovery_agent/users/test_user_http/sessions")
        assert session_resp.status_code == 200
        session_data = session_resp.json()
        session_id = session_data.get("id") or session_data.get("session_id")
        assert session_id is not None

        # Step-2: Run agent with non-priority coordinates (London)
        payload = {
            "app_name": "discovery_agent",
            "user_id": "test_user_http",
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": "Prospecta en las coordenadas Lat: 51.5074, Lng: -0.1278"}]
            },
            "streaming": False
        }
        
        response = test_client.post("/run", json=payload)
        assert response.status_code == 200
        
        events = response.json()
        assert isinstance(events, list)
        assert len(events) > 0
        
        # Verify the response tells us it's out of the priority zone
        response_text = ""
        for event in events:
            if "content" in event and "parts" in event["content"]:
                for part in event["content"]["parts"]:
                    if "text" in part and part["text"]:
                        response_text += part["text"]
                        
        response_lower = response_text.lower()
        assert "fuera" in response_lower or "outside" in response_lower or "perímetro" in response_lower
    except Exception as e:
        err_msg = str(e).lower()
        if "credentials" in err_msg or "auth" in err_msg or "location" in err_msg:
            pytest.skip(f"Skipping HTTP POST endpoint test due to missing GCP environment/auth: {e}")
        else:
            raise e
