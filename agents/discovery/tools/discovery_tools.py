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
"""Semantic discovery tools for the Higo Agent ecosystem.

Provides tools for Google Places search, geolocation perimeter checks,
and Firestore lead management in Colombia's target pilot sectors.
"""

import json
import logging
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Setup basic logger
logger = logging.getLogger(__name__)

# Plus Code base 20 alphabet
OLC_ALPHABET = "23456789CFGHJMPQRVWX"

# Target priority quadrants for pilot zones in Colombia, Australia, and USA
PRIORITY_SECTORS = {
    # Colombia (Bogotá/Medellín)
    "67M7XW22": "Bogotá - Chapinero",
    "67M7WW88": "Bogotá - Teusaquillo",
    "67J3WW88": "Medellín - El Poblado",
    # Australia (Sydney)
    "4RRH4C22": "Sydney - Darlinghurst",
    # USA (Miami / New York)
    "76QXMX22": "Miami - Brickell",
    "87G8P222": "New York - Manhattan",
}

# Pre-populated high-quality mock data for sandbox testing without API keys
MOCK_LEADS_DATABASE = [
    {
        "place_id": "ch_pet_001",
        "name": "Veterinaria & Pet Shop Huellitas Chapinero",
        "plus_code": "67M7XW22+H5",
        "address": "Calle 60 #9-23, Bogotá, Colombia",
        "phone": "+57 312 3456789",
        "lat": 4.6438,
        "lng": -74.0628,
        "category": "Veterinary & Pet Shop",
    },
    {
        "place_id": "ch_pet_002",
        "name": "El Palacio de las Mascotas",
        "plus_code": "67M7XW22+J8",
        "address": "Carrera 13 #58-40, Bogotá, Colombia",
        "phone": "+57 300 9876543",
        "lat": 4.6450,
        "lng": -74.0640,
        "category": "Pet Shop",
    },
    {
        "place_id": "te_vet_001",
        "name": "Clínica Veterinaria San Martín",
        "plus_code": "67M7WW88+A1",
        "address": "Diagonal 40 #16-22, Bogotá, Colombia",
        "phone": "+57 310 1112223",
        "lat": 4.6295,
        "lng": -74.0750,
        "category": "Veterinary Clinic",
    },
    {
        "place_id": "med_pet_001",
        "name": "Poblado Pet Care & Grooming",
        "plus_code": "67J3WW88+F2",
        "address": "Calle 10 #34-12, Medellín, Colombia",
        "phone": "+57 315 7654321",
        "lat": 6.2083,
        "lng": -75.5678,
        "category": "Pet Shop & Grooming",
    }
]

from openlocationcode import openlocationcode as olc

def encode_lat_lng_to_plus8(lat: float, lng: float) -> str:
    """Encodes latitude and longitude coordinates into an 8-character Plus Code (Open Location Code).
    
    Args:
        lat: Latitude of the coordinate.
        lng: Longitude of the coordinate.
        
    Returns:
        An 8-character Plus Code without the '+' sign.
    """
    code = olc.encode(lat, lng, 8)
    return code.replace("+", "")



def google_places_search(plus8_code: str, iso3: Optional[str] = None) -> Dict[str, Any]:
    """Searches for pet-related businesses within the 270m² sector of an 8-character Plus Code.
    
    This tool automates discovery by finding target businesses (pet shops, clinics, grooming salons)
    to facilitate the onboarding process into the Higo VIP/OP ecosystem.
    
    Args:
        plus8_code: The 8-character Plus Code of the sector to search (e.g., "67M7XW22" or "67M7XW22+").
            Must contain exactly 8 OLC characters (excluding any optional '+' characters).
        iso3: Optional 3-letter country ISO code (e.g., "USA", "AUS", "COL") to adapt query keywords.
            
    Returns:
        A structured dictionary indicating success or failure:
        {
            "status": "success" | "error",
            "data": [
                {
                    "place_id": str,
                    "name": str,
                    "plus_code": str,
                    "address": str,
                    "phone": Optional[str],
                    "lat": float,
                    "lng": float,
                    "category": str
                },
                ...
            ],
            "message": str
        }
    """
    # Normalize Plus Code
    cleaned_code = plus8_code.replace("+", "").strip().upper()
    
    # Validation
    if len(cleaned_code) != 8 or any(c not in OLC_ALPHABET for c in cleaned_code):
        return {
            "status": "error",
            "data": [],
            "message": (
                f"Invalid Plus Code format: '{plus8_code}'. "
                f"Must be exactly 8 characters from the OLC alphabet: {OLC_ALPHABET}"
            )
        }

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        # Sandbox / Fallback Mode: return mock pet shops in that sector
        logger.info("GOOGLE_MAPS_API_KEY not found. Operating in sandbox fallback mode.")
        matching_mock_leads = [
            lead for lead in MOCK_LEADS_DATABASE
            if lead["plus_code"].startswith(cleaned_code)
        ]
        
        # If no specific matches found, return a fallback mock list matching the quadrant
        if not matching_mock_leads:
            # Generate a custom sandbox shop for the requested quadrant so the agent can continue
            matching_mock_leads = [
                {
                    "place_id": f"sandbox_pet_{cleaned_code.lower()}",
                    "name": f"Pet Shop El Trébol - Sector {cleaned_code}",
                    "plus_code": f"{cleaned_code}+F1",
                    "address": f"Calle de Pruebas {cleaned_code}, Colombia",
                    "phone": "+57 300 0000000",
                    "lat": 4.6438,  # Default center lat
                    "lng": -74.0628, # Default center lng
                    "category": "Pet Shop",
                }
            ]
            message_suffix = " (Generated generic sandbox result)"
        else:
            message_suffix = ""

        return {
            "status": "success",
            "data": matching_mock_leads,
            "message": f"Successfully retrieved {len(matching_mock_leads)} leads from sandbox database for sector {cleaned_code}{message_suffix}."
        }

    # Real API Integration via traditional text search
    try:
        # Determine keywords based on country language to prevent zero results in US/Australia
        is_english_speaking = iso3.upper() in ("USA", "AUS", "GBR", "CAN") if iso3 else False
        if is_english_speaking:
            keywords = "pet shop OR veterinary OR vet OR animal clinic"
        else:
            keywords = "pet shop OR veterinaria OR peluqueria canina OR tienda de mascotas"

        query = f"{keywords} in plus code {cleaned_code}"
        params = {
            "query": query,
            "key": api_key
        }
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "HigoAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
        if res_data.get("status") not in ("OK", "ZERO_RESULTS"):
            return {
                "status": "error",
                "data": [],
                "message": f"Google Places API error: {res_data.get('status')} - {res_data.get('error_message', 'No details')}"
            }
            
        results = res_data.get("results", [])
        structured_data = []
        
        for r in results:
            # Try to get plus_code from results
            place_plus_code = r.get("plus_code", {}).get("global_code", f"{cleaned_code}+")
            location = r.get("geometry", {}).get("location", {})
            
            structured_data.append({
                "place_id": r.get("place_id"),
                "name": r.get("name"),
                "plus_code": place_plus_code,
                "address": r.get("formatted_address", ""),
                "phone": r.get("formatted_phone_number", None),  # Might require Places Details call if None
                "lat": location.get("lat", 0.0),
                "lng": location.get("lng", 0.0),
                "category": "Pet Shop" if "pet" in str(r.get("types")).lower() else "Veterinary",
            })
            
        return {
            "status": "success",
            "data": structured_data,
            "message": f"Successfully found {len(structured_data)} businesses near {cleaned_code} using Google Places API."
        }
        
    except Exception as e:
        logger.error(f"Error querying Places API: {str(e)}")
        return {
            "status": "error",
            "data": [],
            "message": f"Failed to execute Google Places search: {str(e)}"
        }


def geo_perimeter_check(lat: float, lng: float) -> Dict[str, Any]:
    """Checks if a given coordinate is within the Higo prioritary 270m² Plus Code pilot perimeter.
    
    This ensures that commercial prospecting remains within the designated high-value zones
    of Bogotá or Medellín to focus onboarding operations efficiently.
    
    Args:
        lat: Latitude of the target location.
        lng: Longitude of the target location.
        
    Returns:
        A structured dictionary indicating verification status:
        {
            "status": "success" | "error",
            "data": {
                "is_priority": bool,
                "plus8_code": str,
                "sector_name": str
            },
            "message": str
        }
    """
    try:
        plus8_code = encode_lat_lng_to_plus8(lat, lng)
        sector_name = PRIORITY_SECTORS.get(plus8_code)
        
        if sector_name:
            is_priority = True
            message = f"Coordinates ({lat}, {lng}) fall inside priority sector: {sector_name} ({plus8_code})."
        else:
            is_priority = False
            # Check for generic Colombia pilot city prefix match
            if plus8_code.startswith("67M7") or plus8_code.startswith("67M8"):
                sector_name = "Bogotá - Fuera de sector prioritario"
            elif plus8_code.startswith("67J3") or plus8_code.startswith("67J4"):
                sector_name = "Medellín - Fuera de sector prioritario"
            else:
                sector_name = "Fuera de zona piloto (Colombia)"
            message = f"Coordinates ({lat}, {lng}) are outside the prioritized perimeter. Sector: {sector_name} ({plus8_code})."
            
        return {
            "status": "success",
            "data": {
                "is_priority": is_priority,
                "plus8_code": plus8_code,
                "sector_name": sector_name
            },
            "message": message
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "message": f"Error performing geo perimeter check: {str(e)}"
        }


def encode_geohash(latitude: float, longitude: float, precision: int = 10) -> str:
    """Calculates a Geohash string for the given coordinates (identical to Dart's implementation)."""
    const_base32 = "0123456789bcdefghjkmnpqrstuvwxyz"
    is_even = True
    lat = [-90.0, 90.0]
    lon = [-180.0, 180.0]
    bit = 0
    ch = 0
    geohash = ""

    while len(geohash) < precision:
        if is_even:
            mid = (lon[0] + lon[1]) / 2.0
            if longitude > mid:
                ch |= 1 << (4 - bit)
                lon[0] = mid
            else:
                lon[1] = mid
        else:
            mid = (lat[0] + lat[1]) / 2.0
            if latitude > mid:
                ch |= 1 << (4 - bit)
                lat[0] = mid
            else:
                lat[1] = mid

        is_even = not is_even
        if bit < 4:
            bit += 1
        else:
            geohash += const_base32[ch]
            bit = 0
            ch = 0
    return geohash


def firestore_lead_save(shop_data: Dict[str, Any], phone_code: str) -> Dict[str, Any]:
    """Saves or updates a prospected business lead in the database under the target country division.
    
    Creates an individual document under '/Ope/{phone_code}/Ag/Discovery/leads/{place_id}'
    using a data schema compatible with Higo Core's BusinessModel (Dart). Also increments
    the execution metrics document for the discovery agent.
    
    Args:
        shop_data: A dictionary containing the raw lead details from Google Places:
            - "place_id": str (required, unique identifier)
            - "name": str (required, business name)
            - "plus_code": str (required, full Plus Code)
            - "address": str (optional)
            - "phone": str (optional)
            - "lat": float (optional)
            - "lng": float (optional)
            - "category": str (optional)
            - "schedule": dict (optional)
            - "offerings": list (optional)
        phone_code: The country phone code prefix with '+' sign (e.g. "+57", "+1").
            
    Returns:
        A structured dictionary indicating success or failure:
        {
            "status": "success" | "error",
            "data": Dict[str, Any],
            "message": str
        }
    """
    # Validation
    required_keys = ["place_id", "name", "plus_code"]
    missing = [k for k in required_keys if k not in shop_data or not shop_data[k]]
    if missing:
        return {
            "status": "error",
            "data": {},
            "message": f"Failed to save lead: Missing required fields: {', '.join(missing)}."
        }

    # Format the lead as a Dart BusinessModel (Higo Core compatible)
    now_str = datetime.now(timezone.utc).isoformat()
    lat = float(shop_data.get("lat", 0.0))
    lng = float(shop_data.get("lng", 0.0))
    plus8_origin = shop_data["plus_code"][:8]

    # Map the phone contact structure compatible with PhoneContact class
    raw_phone = shop_data.get("phone")
    phones_list = []
    if raw_phone:
        phones_list.append({
            "countryCode": phone_code,
            "number": str(raw_phone).replace(phone_code, "").replace(" ", "").strip(),
            "hasWhatsApp": True,  # Default assumption for commercial leads
            "hasTelegram": False
        })

    business_model_data = {
        "id": shop_data["place_id"],
        "businessName": shop_data["name"],
        "phones": phones_list,
        "email": shop_data.get("email"),
        "fullAddress": shop_data.get("address", ""),
        "plusCode": shop_data["plus_code"],
        "latitude": lat,
        "longitude": lng,
        "schedule": shop_data.get("schedule"),
        "createdAt": now_str,
        "geohash": encode_geohash(lat, lng),
        "offerings": shop_data.get("offerings", [shop_data.get("category", "Pet Shop").lower()]),
        "status": "prospectado",
        "impact": [plus8_origin]
    }

    # Attempt to use Firestore
    try:
        from google.cloud import firestore
        # Initialize Firestore client (runs inside Vertex AI Agent Engine or with GCP credentials)
        db = firestore.Client()
        
        # 1. Save Lead: /Ope/{phone_code}/Ag/Discovery/leads/{place_id}
        doc_ref = db.collection("Ope").document(phone_code) \
                    .collection("Ag").document("Discovery") \
                    .collection("leads").document(business_model_data["id"])
        
        doc_snapshot = doc_ref.get()
        is_new = not doc_snapshot.exists
        
        if is_new:
            business_model_data["created_at"] = now_str
        else:
            existing_data = doc_snapshot.to_dict() or {}
            business_model_data["created_at"] = existing_data.get("created_at", now_str)
            
        doc_ref.set(business_model_data, merge=True)
        
        # 2. Increment atomic execution stats: /Ope/{phone_code}/Ag/Discovery
        agent_ref = db.collection("Ope").document(phone_code) \
                      .collection("Ag").document("Discovery")
                      
        agent_ref.set({
            "executions": firestore.Increment(1),
            "last_run": firestore.SERVER_TIMESTAMP,
            "last_plus8_run": plus8_origin
        }, merge=True)
        
        operation = "created" if is_new else "updated"
        return {
            "status": "success",
            "data": business_model_data,
            "message": f"Successfully {operation} lead '{business_model_data['businessName']}' in /Ope/{phone_code}/Ag/Discovery/leads."
        }
    except Exception as firestore_err:
        # Log Firestore issue and fallback to local JSON file
        logger.warning(
            f"Firestore Client unavailable or error encountered: {str(firestore_err)}. "
            "Falling back to local file sandbox."
        )
        
        # Local JSON fallback implementation
        try:
            # Establish file path relative to workspace root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            workspace_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
            local_db_path = os.path.join(workspace_root, "leads_sandbox.json")
            
            # Load existing database
            database: Dict[str, Any] = {}
            if os.path.exists(local_db_path):
                try:
                    with open(local_db_path, "r", encoding="utf-8") as f:
                        database = json.load(f)
                except Exception as read_err:
                    logger.error(f"Failed to read local sandbox db: {str(read_err)}")
                    database = {}
            
            place_id = business_model_data["id"]
            
            # Simulate country key grouping locally
            country_key = f"{phone_code}/Ag/Discovery/leads"
            if country_key not in database:
                database[country_key] = {}
                
            is_new = place_id not in database[country_key]
            
            if is_new:
                business_model_data["created_at"] = now_str
            else:
                business_model_data["created_at"] = database[country_key][place_id].get(
                    "created_at", now_str
                )
                
            database[country_key][place_id] = business_model_data
            
            # Simulate executions counter locally
            stats_key = f"{phone_code}/Ag/Discovery/stats"
            if stats_key not in database:
                database[stats_key] = {"executions": 0}
            database[stats_key]["executions"] += 1
            database[stats_key]["last_run"] = now_str
            database[stats_key]["last_plus8_run"] = plus8_origin
            
            # Write back
            with open(local_db_path, "w", encoding="utf-8") as f:
                json.dump(database, f, indent=2, ensure_ascii=False)
                
            operation = "created" if is_new else "updated"
            return {
                "status": "success",
                "data": business_model_data,
                "message": (
                    f"Successfully {operation} lead '{business_model_data['businessName']}' in local sandbox database. "
                    f"Path: {local_db_path}"
                )
            }
        except Exception as local_err:
            return {
                "status": "error",
                "data": {},
                "message": f"Failed to save lead to both Firestore and local database. Error: {str(local_err)}"
            }
