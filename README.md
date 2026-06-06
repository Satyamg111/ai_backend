# Multi-Agent RAG Backend

A high-performance, production-ready FastAPI backend implementing a stateful, LangGraph-based Retrieval-Augmented Generation (RAG) agent workflow. Designed primarily as an interactive portfolio/resume assistant, this backend integrates dynamic LLM prompting, vector-based semantic search, and comprehensive usage analytics.

---

## 🚀 Key Features

*   **Stateful Agent Workflows**: Built using **LangGraph** to model the retrieve-and-generate cycle as a clean, deterministic graph, enabling multi-agent expansion.
*   **Vector Search & RAG**: Integrates **ChromaDB** for local persistent vector storage, enabling semantic context retrieval from uploaded resume documents.
*   **Dynamic Prompt Management**: System prompts are managed in **Supabase** and can be updated on-the-fly via admin endpoints. Implements a thread-safe local cache with a 5-minute Time-To-Live (TTL) to minimize DB queries.
*   **Real-time SSE Streaming**: Supports Server-Sent Events (SSE) via a custom streaming service, sending real-time tokens to the frontend while logging token usage metrics.
*   **Telemetry & Analytics Logging**: Automatically logs details of every chat interaction (latency, status, input/output token usage, user message length, IP) to Supabase.
*   **Analytics Dashboard**: A sleek, built-in HTML dashboard (`/analytics/dashboard`) protected by admin authentication to monitor metrics (total messages, unique sessions, success rates, latency, and tokens) and view recent interactions.
*   **Dynamic PDF Resume Parsing**: Automatically parses multiple uploaded PDF files, splits the text into chunks using recursive character splitting, cleans old vector indices and files in the upload directory, and embeds the new documents in ChromaDB in a single batch.
*   **Robust Administration Security**: Secures writing and reading configurations using header-based `X-Admin-Key` verification.

---

## 🛠 Tech Stack

*   **Core Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
*   **LLM Orchestration**: [LangChain](https://www.langchain.com/) & [LangGraph](https://langchain-ai.github.io/langgraph/)
*   **Vector Database**: [ChromaDB](https://www.trychroma.com/)
*   **Relational Database & Auth**: [Supabase](https://supabase.com/) (PostgreSQL)
*   **LLM Provider**: [OpenRouter API](https://openrouter.ai/) (supporting various open-source models)
*   **PDF Extraction**: [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/en/latest/)

---

## 📂 Project Structure

```text
├── app/
│   ├── agents/            # Agent interface layer (e.g., ResumeAgent)
│   ├── api/               # API routers and path declarations
│   │   ├── routes/        # Router endpoints (chat, uploads, analytics, config)
│   │   └── router.py      # Main API router combining all routes
│   ├── auth/              # Admin verification headers
│   ├── data/              # Uploaded raw documents storage
│   ├── db/                # DB clients (Chroma, Supabase client initialization)
│   ├── graphs/            # LangGraph states, nodes, and compiled graphs
│   ├── llm/               # OpenRouter LLM initialization
│   ├── models/            # Pydantic schemas for request validation
│   ├── services/          # Business logic (ConfigService, UsageTracker, StreamService)
│   ├── config.py          # Configuration definitions
│   └── main.py            # FastAPI App initialization & CORS middleware
├── chroma_db/             # Local Chroma DB persistent files (gitignored)
├── Dockerfile             # Production container definitions
├── render.yaml            # Render deployment blueprint configuration
├── requirements.txt       # Python library dependencies
└── runtime.txt            # Python environment specification
```

---

## ⚙️ Installation & Local Setup

### 1. Prerequisites
Ensure you have **Python 3.11** installed.

### 2. Clone and Setup Environment
Navigate to the project root directory and create a virtual environment:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (based on the template below):

```env
# OpenRouter Configuration
OPENROUTER_API_KEY="your-openrouter-api-key"
OPENAI_MODEL="openrouter/free" # Or any other OpenRouter supported model identifier
OPENAI_BASE_URL="https://openrouter.ai/api/v1"

# Supabase Configuration
SUPABASE_URL="https://your-supabase-project.supabase.co"
SUPABASE_KEY="your-supabase-anon-or-service-key"

# Admin Access Credentials
ADMIN_API_KEY="your-super-secure-admin-key"
```

---

## 🚀 Running the App

### Running Locally
To launch the development server with hot-reload enabled:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 10000
```
The API documentation will be available at [http://localhost:10000/docs](http://localhost:10000/docs).

### Running with Docker
Build and run the application in a docker container:

```bash
# Build the Docker image
docker build -t ai-agent-backend .

# Run the container
docker run -p 10000:10000 --env-file .env ai-agent-backend
```

---

## 🌐 API Endpoint Reference

### 1. Chat Endpoints

#### 💬 Standard Chat (`POST /chat`)
Submits a message and returns the full assistant response synchronously.

*   **Headers**: `Content-Type: application/json`
*   **Body**:
    ```json
    {
      "agent": "resume",
      "message": "What is Satyam's experience in Python?",
      "session_id": "optional-uuid-for-chat-history"
    }
    ```
*   **Response**:
    ```json
    {
      "success": true,
      "response": "Satyam has extensive experience building systems using Python..."
    }
    ```

#### 📡 Streaming Chat (`POST /chat/stream`)
Submits a message and streams the response back token-by-token using Server-Sent Events (SSE).

*   **Headers**: `Content-Type: application/json`
*   **Body**: Same as standard chat.
*   **Response format**: `text/event-stream` (streams chunks formatted as `data: token\n\n`).

---

### 2. Admin Config Endpoints
*All admin endpoints require the header `X-Admin-Key: <your-admin-key>`.*

*   **`GET /config/agents`**: Lists all agents that have stored system prompts in the database.
*   **`GET /config/prompt?agent=resume`**: Fetches the currently cached/active prompt template for a specific agent.
*   **`PUT /config/prompt?agent=resume`**: Updates the active system prompt for an agent.
    *   **Body**: `{"prompt": "Your new system instructions here."}`
*   **`DELETE /config/prompt?agent=resume`**: Resets an agent's prompt back to its default built-in setting.

---

### 3. File Upload Endpoint
*Requires the header `X-Admin-Key: <your-admin-key>`.*

*   **`POST /upload/resume`**: Accepts single or multiple PDF files via form-data.
    *   **Form Params**:
        *   `file`: (Optional, backward-compatible) A single PDF file.
        *   `files`: (Optional) Multiple PDF files.
    *   **Behavior**: Clears existing vector embeddings and files in the upload directory, processes all uploaded PDF documents from both parameters, parses the text from each, splits them, and stores the newly compiled set of embeddings in ChromaDB in a single batch.

---

### 4. Analytics & Dashboard

*   **`GET /analytics/dashboard`**: Interactive web dashboard. Log in with the `ADMIN_API_KEY` to view total queries, latency profiles, success rates, active sessions, and paginated logs.
*   **`GET /analytics/summary`**: Returns total message counts, unique sessions, average response times, success rates, and token aggregates. *(Requires admin key header)*
*   **`GET /analytics/recent`**: Returns raw log streams from Supabase. *(Requires admin key header)*
*   **`GET /analytics/daily`**: Returns daily usage aggregations (average latency, error rates, counts). *(Requires admin key header)*

---

## ☁️ Deployment (Render Blueprint)
This project includes a `render.yaml` specification for zero-config deployments to Render.com. The blueprint defines:
*   A Python Web Service.
*   Required environment variable bindings for Supabase and OpenRouter.
*   Start command configurations.
