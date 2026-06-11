![Higo Technology Animals](assets/empezar.webp)

# Higo Agent - Commerce Discovery & Pet Care

An agentic multi-agent system built using the **Google GenAI SDK (Gemini 2.5 Flash)** and **Google Cloud (Firestore, Places API)**. It automates B2B merchant prospecting and enhances user retention in the **Higo** pet care ecosystem.

Designed for the **Google for Startups AI Agents Challenge (Track 2 - OPTIMIZE)**.

---

## 🧠 System Architecture

The project consists of two specialized agents:

1. **Higo Discovery Agent (`higo_discovery_agent`):** An autonomous B2B expansion agent that prospects target locations, searches for local pet businesses (via Places API), fetches real contact info/opening hours (via Places Details API), normalizes the scheduling structure to match Higo Core's schemas (`HorarioWeekModelV2`), and saves leads atomically to Firestore.
2. **Care Tip Agent (`care_tip_agent`):** A consumer-focused agent that generates daily pet care tips based on pet parameters (breed, age, weight) and recommends local store products to drive B2B adoption.

---

## 📂 Project Structure

* `agents/discovery/agent.py`: Agent definition, ReAct system instructions, and tool registry.
* `agents/discovery/agent_engine_app.py`: FastAPI server wrapper for Cloud Engine deployment.
* `agents/discovery/tools/discovery_tools.py`: Tools for Places Search, Places Details querying, normalizations, and Firestore integration with local fallback database (`leads_sandbox.json`).
* `tests/`: Integration and unit tests.
* `pyproject.toml`: Dependency configuration.

---

## 🚀 How to Run

### Setup Environment
```bash
# Set up Google Application Default Credentials
gcloud auth application-default login

# Export your Maps API Key
export GOOGLE_MAPS_API_KEY="your-api-key"
```

### Install Dependencies & Run Tests

```bash
# Run unit tests (always run, sandbox mode works offline)
uv run pytest tests/unit

# Run integration tests (skipped automatically if auth is expired)
uv run pytest tests/integration
```

---

## 📊 Process Flowcharts

### 1. Higo Discovery Agent Flow (B2B Expansion)

```mermaid
graph TD
    %% Estilos
    classDef trigger fill:#e0e7ff,stroke:#4338ca,stroke-width:2px,color:#000;
    classDef process fill:#f8fafc,stroke:#64748b,stroke-width:1px,color:#000;
    classDef decision fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#000;
    classDef success fill:#dcfce7,stroke:#15803d,stroke-width:2px,color:#000;

    A[User downloads Higo VIP App]:::trigger --> B[User navigates to Community section in Home]:::process
    B --> C[Enable geolocation option]:::process
    C --> D[Cloud Function triggers with user location]:::process
    
    D --> E{Has this area been<br>discovered before?}:::decision
    
    E -- No --> F[Higo Discovery Agent invoked in background]:::process
    E -- Yes --> H[User receives local info, shops, and nearby pets]:::success
    
    F --> H
    H --> I[End of user-facing flow]:::success
    
    %% Trabajo asíncrono del agente
    F --> J[Agent queries Google Places API to find and extract leads]:::process
    J --> K[Agent saves new qualified leads to Firestore]:::success
```

### 2. Care Tip Agent Flow (B2C Engagement)

```mermaid
graph TD
    %% Estilos
    classDef trigger fill:#e0e7ff,stroke:#4338ca,stroke-width:2px,color:#000;
    classDef process fill:#f8fafc,stroke:#64748b,stroke-width:1px,color:#000;
    classDef decision fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#000;
    classDef success fill:#dcfce7,stroke:#15803d,stroke-width:2px,color:#000;

    A[User downloads Higo VIP App and opens Home]:::trigger --> B[Is the user<br>already registered?]:::decision
    
    B -- No --> C[User registers on the platform]:::process
    C --> D{Does the user have<br>registered pets?}:::decision
    
    B -- Yes --> D
    
    D -- No --> E[User registers pets: species, breed, gender, age]:::process
    E --> F[User taps button to get tip of the day]:::process
    
    D -- Yes --> F
    
    F --> G[Agent retrieves the standard daily care tip template]:::process
    G --> H[Gemini customizes tip details using specific pet metadata]:::process
    H --> I[User receives personalized Daily Care Tip]:::success
```

---

![Share with Higo](assets/share_with_higo_png.png)
