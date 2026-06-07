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
"""Unit tests for Higo Agent discovery tools."""

import os
import json
import pytest
from agents.discovery.tools.discovery_tools import (
    encode_lat_lng_to_plus8,
    google_places_search,
    firestore_lead_save,
)

def test_encode_lat_lng_to_plus8() -> None:
    # Bogotá coordinates: ~4.6438, -74.0628
    code = encode_lat_lng_to_plus8(4.6438, -74.0628)
    assert len(code) == 8
    assert code.startswith("67P7")

def test_google_places_search_sandbox() -> None:
    # Ensure maps key is not present/mocked for sandbox test
    orig_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if "GOOGLE_MAPS_API_KEY" in os.environ:
        del os.environ["GOOGLE_MAPS_API_KEY"]
    try:
        res = google_places_search("67M7XW22")
        assert res["status"] == "success"
        assert len(res["data"]) > 0
        assert res["data"][0]["place_id"] == "ch_pet_001"
        assert res["data"][0]["email"] == "huellitas@chapinero.com"
        assert "semana" in res["data"][0]["schedule"]
        assert len(res["data"][0]["schedule"]["semana"]) == 7
    finally:
        if orig_key:
            os.environ["GOOGLE_MAPS_API_KEY"] = orig_key

def test_firestore_lead_save_sandbox(tmp_path) -> None:
    # We will test local json fallback
    lead = {
        "place_id": "test_shop_999",
        "name": "Test Pet Shop",
        "plus_code": "67M7XW22+A1",
        "address": "Calle Falsa 123",
        "phone": "+57 300 1234567",
        "lat": 4.6438,
        "lng": -74.0628,
        "category": "Pet Shop"
    }
    
    # We can mock/force the local file fallback by ensuring firestore module import falls back
    # or just run it. If Firestore isn't authenticated/installed, it falls back to local file.
    res = firestore_lead_save(lead, "+57")
    assert res["status"] == "success"
    assert res["data"]["id"] == "test_shop_999"
    assert "created_at" in res["data"]
    
    # Clean up test output if local sandbox database was created
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    local_db_path = os.path.join(workspace_root, "leads_sandbox.json")
    if os.path.exists(local_db_path):
        try:
            os.remove(local_db_path)
        except Exception:
            pass
