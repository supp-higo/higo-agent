import logging
import os
from typing import Any
import json

import vertexai
from dotenv import load_dotenv
from google.cloud import logging as google_cloud_logging
from fastapi import FastAPI, Request
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.care_tip.agent import care_tip_agent as higo_care_tip_agent
from agents.shared.telemetry import setup_telemetry
from agents.care_tip.run import clean_json_response

# Initialize Session Service for ADK runner
session_service = InMemorySessionService()

# Load environment variables from .env file at runtime
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Higo Care Tip Agent API")

# Setup telemetry and logging
vertexai.init()
setup_telemetry()
logging.basicConfig(level=logging.INFO)
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)

@app.post("/generate_care_tip")
async def generate_care_tip(request: Request):
    try:
        pet_details = await request.json()
    except Exception as e:
        return {"error": f"Invalid JSON payload: {e}"}

    name = pet_details.get("name", "Mascota")
    pet_type = pet_details.get("type", "Dog")
    breed = pet_details.get("breed", "Mixed-breed")
    age = pet_details.get("age", "2 años")
    gender = pet_details.get("gender", "Male")
    daily_context = pet_details.get("daily_context", "Cuidado y bienestar general de la mascota.")
    language = pet_details.get("language", "en")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    guidelines_file = "dog_breed_guidelines.json" if pet_type == "Dog" else "cat_breed_guidelines.json"
    guidelines_path = os.path.join(current_dir, "memory", guidelines_file)
    
    breed_guidelines = {}
    if os.path.exists(guidelines_path):
        try:
            with open(guidelines_path, "r", encoding="utf-8") as f:
                all_guidelines = json.load(f)
                breed_guidelines = all_guidelines.get(breed, all_guidelines.get("default", {}))
        except Exception:
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
        session = await session_service.create_session(user_id="anonymous", app_name="care_tip")
        runner = Runner(agent=higo_care_tip_agent, session_service=session_service, app_name="care_tip")
        content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        
        response_text = ""
        async for event in runner.run_async(user_id="anonymous", session_id=session.id, new_message=content):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
            
        json_output = clean_json_response(response_text)
        result_json = json.loads(json_output)
        
        try:
            from google.cloud import firestore
            from datetime import datetime
            db = firestore.Client()
            now = datetime.utcnow()
            month_str = now.strftime("%Y_%m")
            db.collection("Party").document("careTips").set(
                {f"{pet_type.lower()}_{month_str}": firestore.Increment(1)},
                merge=True
            )
        except Exception as e:
            logging.error(f"Failed to save metrics to Firestore: {e}")
            
        return result_json
    except Exception as e:
        return {
            "error": str(e),
            "tip": f"¡Cuidá mucho a {name}! Recordá alimentarlo bien y sacarlo a pasear.",
            "category": "Cuidado General",
            "recommendedProducts": [],
            "hasPromo": False
        }
