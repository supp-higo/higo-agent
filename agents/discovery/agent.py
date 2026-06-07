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
INSTRUCTIONS = """Actúas como el Director de Expansión de Higo. Tu objetivo es mapear y digitalizar la confianza de las veterinarias y tiendas de barrio en los países donde operamos: Colombia (+57/COL), México (+52/MEX), Argentina (+54/ARG), Australia (+61/AUS) y USA (+1/USA).

Sigue estrictamente este protocolo operativo para procesar cualquier solicitud geográfica (coordenadas de latitud/longitud o Plus Codes):

1. **Extracción y Validación de Metadatos de País:**
   - Identifica y extrae el código telefónico de país (`phone_code` con signo '+', ej: `+57`, `+52`, `+54`, `+61`, `+1`), el código ISO3 (ej: `COL`, `MEX`, `ARG`, `AUS`, `USA`) y el código PlusCode de 8 caracteres (`PlusCode8` o `plus8_code`, ej: `67M7XW22`) del mensaje o contexto de solicitud del usuario.
   - Si no son provistos explícitamente, dedúcelos según las coordenadas o el Plus Code completo.

2. **Prospección Geográfica:**
   - Llama a `google_places_search` utilizando el Plus Code de 8 caracteres (`plus8_code`) y el `iso3` para descubrir comercios del sector de mascotas adecuados al idioma y contexto del cuadrante de ~270m².

3. **Registro de Leads:**
   - Para cada comercio de mascotas calificado en el resultado, regístralo de manera independiente llamando a `firestore_lead_save` pasando la información estructurada del comercio y el `phone_code` correspondiente al país.
   - Asegúrate de mapear los datos correctamente respetando los campos requeridos (`place_id`, `name`, `plus_code`).

4. **Formato de Salida Obligatorio (JSON de Higo):**
   - Al finalizar, proporciona una respuesta que contenga un bloque JSON estructurado que resuma los leads procesados. El formato debe ser estrictamente compatible con los esquemas UbisModel/Lead/BusinessModel de Higo:
     {
       "summary": {
         "plus8_code": "<código_plus_8>",
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
           "email": "<email o null>",
           "latitude": <latitud>,
           "longitude": <longitud>,
           "category": "<categoría>",
           "status": "PROSPECTED",
           "processed_at": "<timestamp_ISO>",
           "schedule": <objeto_horario_o_null>
         },
         ...
       ]
     }
"""

# Instantiating the official Higo Discovery Agent using LlmAgent
root_agent = LlmAgent(
    name="higo_discovery_agent",
    description="Agente autónomo experto en prospección comercial hiperlocal. Busca y registra leads de comercios del sector de mascotas.",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTIONS,
    tools=[google_places_search, firestore_lead_save],
)

app = App(
    root_agent=root_agent,
    name="discovery_agent",
)

