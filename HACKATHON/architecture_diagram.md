# Higo Agent Ecosystem Architecture & Process Flow

This document outlines the architectural blueprint and process flows of the **Higo Agent** ecosystem. It is designed to provide external stakeholders, challenge judges, and developers with a clear understanding of how the system operates under the hood without exposing sensitive credentials or proprietary backend configurations.

---

## 🏗️ Ecosystem Architecture

The Higo Agent ecosystem is structured into five distinct, decoupled layers. This design ensures high availability, security, and scalability by separating client applications, server execution environments, AI orchestration, tool integration, and data storage.

```mermaid
graph LR
    %% Estilos de la Arquitectura
    classDef client fill:#e0e7ff,stroke:#4338ca,stroke-width:2px,color:#000;
    classDef runtime fill:#f1f5f9,stroke:#64748b,stroke-width:2px,color:#000;
    classDef ai fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#000;
    classDef mcp fill:#faf5ff,stroke:#8b5cf6,stroke-width:2px,color:#000;
    classDef data fill:#dcfce7,stroke:#15803d,stroke-width:2px,color:#000;

    %% CAPA DE CLIENTE
    subgraph Capa_Cliente [Client / UI Layer]
        A[Higo VIP App - Flutter]:::client
        B[Higo Op App - Flutter]:::client
    end

    %% CAPA DE RUNTIME
    subgraph Capa_Runtime [Server Infrastructure]
        C[Vertex AI Agent Engine / Cloud Run]:::runtime
        D[FastAPI Backend Wrapper]:::runtime
    end

    %% CAPA AGÉNTICA
    subgraph Capa_IA [AI Brain - Google ADK]
        E[ADK LimAgent Orchestrator]:::ai
        F[Gemini 2.5 Flash LLM]:::ai
    end

    %% CAPA DE CONECTORES
    subgraph Capa_Conectores [Tool Abstraction]
        G[Model Context Protocol - MCP]:::mcp
    end

    %% CAPA DE DATOS Y APIS
    subgraph Capa_Datos [External Tools & Persistence]
        H[Google Places API Tool]:::data
        I[Cloud Firestore Database]:::data
    end

    %% CONEXIONES E INTERACCIONES
    A & B <-->|HTTP / Firebase SDK| C
    C <--> D
    D <--> E
    E <-->|Inference / Tool Calling| F
    E <--> G
    G <-->|Geographic Grounding| H
    G <-->|Read / Write Leads| I
```

### Layer Breakdown

1. **Client / UI Layer (Flutter):**
   * **Higo VIP (B2C):** The customer-facing application where pet parents manage daily care, share photos, and interact with the community.
   * **Higo Op (B2B):** The dashboard used by local pet shops to manage inventory, catalog products, and receive localized orders without paying commissions.

2. **Server Infrastructure (Vertex AI & FastAPI):**
   * High-availability, serverless runtimes hosting our microservices.
   * FastAPI acts as a lightweight wrapper to handle requests, manage endpoint routing, and forward operations to the agentic core.

3. **AI Brain (Google ADK & Gemini):**
   * **ADK LimAgent Orchestrator:** Implements ReAct (Reason + Action) loop logic, system instructions, and tool registries.
   * **Gemini 2.5 Flash:** Selected as the primary LLM because of its industry-leading latency, token efficiency, and robust tool-calling accuracy.

4. **Tool Abstraction (MCP):**
   * Implements the **Model Context Protocol (MCP)** to establish standardized, decoupled access vectors. This allows the agents to query external databases and services safely without hardcoding integration logic.

5. **External Tools & Data (Places API & Firestore):**
   * **Google Places API:** Performs geographical grounding to search, identify, and verify local pet merchants in real-time.
   * **Cloud Firestore:** The central persistent storage containing user geo-states, basic pet profiles, and validated B2B leads.

---

## 🔄 Unified Process Flowchart

The following diagram illustrates how B2B prospecting (Higo Discovery Agent) and B2C engagement (Care Tip Agent) run in parallel, triggered by user actions within the mobile app.

```mermaid
graph TD
    %% Estilos
    classDef trigger fill:#e0e7ff,stroke:#4338ca,stroke-width:2px,color:#000;
    classDef process fill:#f8fafc,stroke:#64748b,stroke-width:1px,color:#000;
    classDef decision fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#000;
    classDef success fill:#dcfce7,stroke:#15803d,stroke-width:2px,color:#000;

    %% Entrada Principal
    Start([User opens Higo VIP App]):::trigger --> ActionCheck{Which action is performed?}:::decision
    
    %% Rama B2B: Discovery Flow
    ActionCheck -- Accesses Community Feed --> B1[Enable geolocation tracking]:::process
    B1 --> B2[Trigger background function with location coordinates]:::process
    B2 --> B3{Has this zone<br>been discovered before?}:::decision
    B3 -- No --> B4[Invoke Higo Discovery Agent in background]:::process
    B3 -- Yes --> B5[User receives info on nearby shops, pet community, and events]:::success
    B4 --> B6[Agent queries Google Places API to search & extract target pet stores]:::process
    B6 --> B7[Agent structures and saves new qualified leads to Firestore]:::success
    B7 --> B5
    
    %% Rama B2C: Engagement Flow
    ActionCheck -- Views Home / Tip of the Day --> C1{Is the user<br>already registered?}:::decision
    C1 -- No --> C2[User signs up on the platform]:::process
    C2 --> C3{Do they have<br>registered pets?}:::decision
    C1 -- Yes --> C3
    C3 -- No --> C4[Register pet details: species, breed, gender, age]:::process
    C4 --> C5[Tap button to request daily pet tip]:::process
    C3 -- Yes --> C5
    C5 --> C6[Agent retrieves the standard daily care tip template]:::process
    C6 --> C7[Gemini customizes tip details using specific pet metadata]:::process
    C7 --> C8[User receives personalized Daily Care Tip]:::success
```

### Process Integration

* **B2B Expansion Loop:** As users explore the app locally, they trigger the geolocation checks. The system automatically launches the **Discovery Agent** to build a comprehensive directory of neighborhood pet shops.
* **B2C Engagement Loop:** Once the local catalog grows, the **Care Tip Agent** can recommend local shops and specific products dynamically inside the personalized tips, closing the B2B2C loop by driving users to neighborhood stores.
