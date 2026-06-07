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
"""Integration tests for the Higo Discovery Agent."""

import json
import os
import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.discovery.agent import root_agent


def test_agent_initialization() -> None:
    """Verifies that the agent is correctly initialized with the proper name, model, and instructions."""
    assert root_agent.name == "higo_discovery_agent"
    assert root_agent.model.model == "gemini-2.5-flash"
    assert "Director de Expansión de Higo" in root_agent.instruction
    assert len(root_agent.tools) == 2


def test_agent_run_global() -> None:
    """Tests the agent's response when given a location (e.g. London)."""
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text="Por favor prospecta en la ubicación Lat: 51.5074, Lng: -0.1278, PlusCode8: 9C3XGV22, ISO3: GBR, phone_code: +44."
        )]
    )

    try:
        events = list(
            runner.run(
                new_message=message,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )
        assert len(events) > 0

        # Collect response text
        response_text = ""
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text

        # The agent should successfully prospect and return structured JSON
        response_lower = response_text.lower()
        assert "summary" in response_lower or "leads" in response_lower or "pet" in response_lower
    except Exception as e:
        # If credentials are not present, skip execution failures gracefully
        err_msg = str(e).lower()
        if "credentials" in err_msg or "api key" in err_msg or "auth" in err_msg or "location" in err_msg:
            pytest.skip(f"Skipping model execution integration test due to missing GCP environment/auth: {e}")
        else:
            raise e


def test_agent_run_priority() -> None:
    """Tests the agent's complete ReAct loop when given a coordinate (e.g. Bogotá Chapinero)."""
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    # Bogotá Chapinero pilot sector coordinates
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text="Prospecta la zona en las coordenadas Lat: 3.95125, Lng: -74.09875, PlusCode8: 67M7XW22, ISO3: COL, phone_code: +57 y registra las veterinarias."
        )]
    )

    try:
        events = list(
            runner.run(
                new_message=message,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )
        assert len(events) > 0

        response_text = ""
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text

        # The agent should find mock pet shops (like Huellitas) and return structured JSON
        response_lower = response_text.lower()
        assert "summary" in response_lower or "leads" in response_lower or "pet" in response_lower
    except Exception as e:
        err_msg = str(e).lower()
        if "credentials" in err_msg or "api key" in err_msg or "auth" in err_msg or "location" in err_msg:
            pytest.skip(f"Skipping model execution integration test due to missing GCP environment/auth: {e}")
        else:
            raise e
