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
"""CLI Runner script for Higo CareTipAgent."""

import sys
import os
import json
import re

# Add the parent directory of 'agents' to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.care_tip.agent import care_tip_agent

def clean_json_response(text: str) -> str:
    """Removes markdown code block delimiters and whitespaces to extract pure JSON."""
    cleaned = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
    if match:
        return match.group(1).strip()
    return cleaned

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing pet details JSON argument."}))
        sys.exit(1)
        
    try:
        pet_details = json.loads(sys.argv[1])
    except Exception as e:
        print(json.dumps({"error": f"Failed to parse input JSON: {e}"}))
        sys.exit(1)
        
    name = pet_details.get("name", "Mascota")
    pet_type = pet_details.get("type", "Dog")
    breed = pet_details.get("breed", "Mixed-breed")
    age = pet_details.get("age", "2 años")
    gender = pet_details.get("gender", "Male")
    daily_context = pet_details.get("daily_context", "Cuidado y bienestar general de la mascota.")
    language = pet_details.get("language", "en")
    
    # Load guidelines from local memory bank
    guidelines_file = "dog_breed_guidelines.json" if pet_type == "Dog" else "cat_breed_guidelines.json"
    guidelines_path = os.path.join(current_dir, "memory", guidelines_file)
    
    breed_guidelines = {}
    if os.path.exists(guidelines_path):
        try:
            with open(guidelines_path, "r", encoding="utf-8") as f:
                all_guidelines = json.load(f)
                breed_guidelines = all_guidelines.get(breed, all_guidelines.get("default", {}))
        except Exception as e:
            # Fallback silently if reading file fails
            pass
            
    prompt = f"""Generá el tip para la siguiente mascota:
Nombre: {name}
Tipo: {pet_type}
Raza: {breed}
Edad: {age}
Género: {gender}
Contexto del Día: {daily_context}
Idioma Requerido: {language} (Tono neutral, sin jerga local)

Pautas específicas de su raza y comportamiento:
{json.dumps(breed_guidelines, indent=2, ensure_ascii=False)}
"""
    
    try:
        # Run agent
        response = care_tip_agent.run(prompt)
        # Extract response text
        response_text = ""
        if hasattr(response, "content") and response.content:
            if hasattr(response.content, "parts") and response.content.parts:
                response_text = "".join(part.text for part in response.content.parts if hasattr(part, "text") and part.text)
        elif isinstance(response, str):
            response_text = response
            
        json_output = clean_json_response(response_text)
        # Validate output is valid JSON
        json.loads(json_output)
        print(json_output)
    except Exception as e:
        print(json.dumps({
            "error": f"Agent execution failed: {e}",
            "tip": f"¡Cuidá mucho a {name}! Recordá alimentarlo bien y sacarlo a pasear.",
            "category": "Cuidado General",
            "recommendedProducts": []
        }))

if __name__ == "__main__":
    main()
