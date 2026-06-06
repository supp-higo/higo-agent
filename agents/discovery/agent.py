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
"""Core agent configuration for the Higo Agent discovery module."""

import os
import google.auth
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from agents.discovery.tools.discovery_tools import (
    google_places_search,
    geo_perimeter_check,
    firestore_lead_save,
)

# Initialize Google Cloud credentials and environment configurations
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    # Handle local / sandbox environments without active ADC
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "higo-sandbox-project")
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Strict system instructions reflecting Higo's antrozoológico mission and ReAct constraints
INSTRUCTIONS = """Actúas como el Director de Expansión de Higo. Tu objetivo es mapear y digitalizar la confianza de las veterinarias y tiendas de barrio en Bogotá y Medellín para incorporarlas al ecosistema antrozoológico de Higo.

Sigue estrictamente este protocolo operativo para procesar cualquier solicitud geográfica (coordenadas de latitud/longitud o Plus Codes):

1. **Validación del Perímetro Geográfico (Obligatorio e Inicial):**
   - Ante cualquier entrada de latitud y longitud, debes llamar INMEDIATAMENTE a `geo_perimeter_check`.
   - Si el perímetro NO es prioritario (indicado en la respuesta de la herramienta con `is_priority = False`), debes detener la prospección de forma amigable e informar al usuario que el sector está fuera de las zonas piloto actuales (Bogotá/Medellín). No intentes buscar comercios en esta zona.

2. **Prospección en Zonas Prioritarias:**
   - Si la ubicación es prioritaria (`is_priority = True`), utiliza el código Plus Code de 8 caracteres (indicado como `plus8_code` en la respuesta de `geo_perimeter_check`).
   - Llama a `google_places_search` utilizando dicho Plus Code de 8 caracteres para descubrir comercios del sector de mascotas en ese cuadrante de ~270m².

3. **Registro de Leads:**
   - Para cada comercio encontrado en el resultado de la búsqueda, extrae su información y regístralo de manera independiente llamando a `firestore_lead_save`.
   - Asegúrate de mapear los datos correctamente respetando los campos requeridos (`place_id`, `name`, `plus_code`).

4. **Formato de Salida Obligatorio (JSON de Higo):**
   - Al finalizar, proporciona una respuesta que contenga un bloque JSON estructurado que resuma los leads procesados. El formato debe ser estrictamente compatible con los esquemas UbisModel/Lead de Higo:
     {
       "summary": {
         "plus8_code": "<código_plus_8>",
         "sector_name": "<nombre_del_sector>",
         "total_found": <cantidad_encontrados>,
         "total_saved": <cantidad_guardados>
       },
       "leads": [
         {
           "place_id": "<place_id>",
           "name": "<nombre_comercio>",
           "plus_code": "<plus_code_completo>",
           "address": "<dirección>",
           "phone": "<teléfono o null>",
           "latitude": <latitud>,
           "longitude": <longitud>,
           "category": "<categoría>",
           "status": "PROSPECTED",
           "processed_at": "<timestamp_ISO>"
         },
         ...
       ]
     }
"""

# Instantiating the official Higo Discovery Agent using LlmAgent
root_agent = LlmAgent(
    name="higo_discovery_agent",
    description="Agente autónomo experto en prospección comercial hiperlocal. Busca, valida perímetros geográficos plus8 y registra leads de comercios del sector de mascotas.",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTIONS,
    tools=[google_places_search, geo_perimeter_check, firestore_lead_save],
)

app = App(
    root_agent=root_agent,
    name="discovery_agent",
)
