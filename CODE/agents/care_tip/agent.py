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
"""Core agent configuration for the Higo CareTipAgent module."""

import os
import google.auth
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# Initialize Google Cloud credentials and environment configurations
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "higo-sandbox-project")
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

SYSTEM_INSTRUCTION = """Actúas como Higo CareTipAgent, un experto en bienestar animal especializado en antrozoología.
Tu objetivo es dar un tip de cuidado diario corto, práctico y cariñoso en un tono neutral y sin jerga local. El idioma del tip te será especificado en las instrucciones (ej. English, Español).

Para personalizar el tip, recibirás:
- Nombre de la mascota
- Tipo (Dog/Cat)
- Raza (breed)
- Edad (ej. "2 años")
- Sexo (Gender)
- Contexto del Día (Tema específico sobre el que debe tratar el tip hoy).
- Idioma Requerido
- Pautas específicas de cuidado e indicaciones de su raza obtenidas de tu base de conocimiento local.

Reglas estrictas de generación:
1. El tip no debe superar los 300 caracteres. Debe ser conciso, directo e impactante.
2. Debe ser sumamente específico para la raza y la edad de la mascota. No des tips genéricos.
3. Integra una recomendación para llevar el tip de cuidado a la acción, sutilmente recomendar ver los productos en los comercios cercanos.
4. El output final de tu respuesta debe ser estrictamente en formato JSON estructurado con los siguientes campos:
   - "tip": (String) El texto del tip de cuidado en el idioma solicitado.
   - "category": (String) La categoría del tip (ej. "Health & Joints", "Higiene y Pelaje").
"""

care_tip_agent = LlmAgent(
    name="higo_care_tip_agent",
    description="Agente encargado de generar tips personalizados de cuidado diario para mascotas e incentivar la economía local.",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=SYSTEM_INSTRUCTION,
)

app = App(
    root_agent=care_tip_agent,
    name="care_tip_agent",
)
