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
"""Session-wide setup and check for GCP authentication in integration tests."""

import pytest
import google.auth
from google.auth.transport.requests import Request


@pytest.fixture(scope="session", autouse=True)
def check_gcp_auth():
    """Checks if GCP credentials are available and valid, skipping tests if not."""
    try:
        credentials, _ = google.auth.default()
        credentials.refresh(Request())
    except Exception as e:
        pytest.skip(
            f"Skipping integration tests because GCP credentials are expired or unavailable: {e}"
        )
