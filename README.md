# OneTwenty 🩸

**India's Unified, AI-Powered Diabetes Management Platform**

> One platform. Every CGM. Every insight. Every patient.

---

## The Problem

India has **101 million diabetics** — the highest in the world — with **50 lakh+ CGM users** growing 2x yearly. Every CGM brand (Libre, Dexcom, Medtronic) locks data into its own app. Switching sensors means losing your data, history, and insights. Doctors receive mismatched PDFs, and families can't easily monitor loved ones.

## The Solution

OneTwenty unifies glucose data from **all CGM brands** into a single multi-tenant platform with AI-powered insights, real-time family sharing, and a dedicated doctor portal — all at ₹99/month.

---

## Features & Codebase

### 📱 Patient PWA (`frontend/`)
Built with **Vite + Vanilla JS** for a lightweight, installable PWA.
- **Real-time glucose chart** — D3.js-powered graphs with trend arrows (`src/enhanced-chart.js`, `src/simple-chart.js`)
- **WebSocket live sync** — instant updates from backend (`src/websocket.js`)
- **Nightscout-compatible UI** — full renderer, care portal, bolus calculator (`src/nightscout/`)
- **AI treatment logging** — natural language input: *"Had 2 rotis, took 4 units, walked 3 km"*
- Profile management, settings, and subdomain-based auth (`src/profile.js`, `src/nightscout/hashauth.js`)

### 🖥️ Backend (`backend_python/`)
Layered **FastAPI** architecture with clean separation of concerns:
- **API Layer** — versioned REST endpoints + dependency injection (`app/api/v1/`, `app/api/deps.py`)
- **Services** — business logic for auth, entries, and tenants (`app/services/`)
- **Repositories** — data access for PostgreSQL & MongoDB (`app/repositories/`)
- **WebSocket** — tenant-scoped real-time broadcast to all connected clients (`app/websocket/`)
- **Schemas** — Pydantic models for request/response validation (`app/schemas/`)
- **Core** — config, security, and middleware (`app/core/`, `app/middleware/`)

### 👨‍👩‍👧 Family & Caregivers
- **Glucose Clock** — ambient display that glows green/orange/red, polls `/api/v1/entries/current`
- Smart high/low alerts via SMS & push

### 🏥 Doctor Portal
- Multi-patient live dashboard with cross-brand unified history
- Managed via `app/api/v1/` doctor endpoints and `app/repositories/`

---

## Architecture

![OneTwenty System Architecture](./architecture.png)

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **Frontend** | Vanilla JS (ES6+), Vite, D3.js |
| **Databases** | PostgreSQL 15, MongoDB 6.0, Redis |
| **Auth** | JWT + API Secrets + Subdomain-based |
| **Real-time** | WebSockets |
| **AI/ML** | AWS Bedrock (Agentic AI), SageMaker |
| **Infra** | AWS (EC2, RDS, S3, CloudFront), Docker |
| **CI/CD** | GitHub Actions |

---

## Project Structure

```
OneTwenty/
├── backend_python/     # FastAPI backend (API, WebSockets, Auth)
├── frontend/           # Vite + Vanilla JS PWA
├── requirements.md     # Detailed product requirements (16 user stories)
├── README.md           # This file
└── design.md           # System design & architecture document
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15
- MongoDB 6.0

### Backend Setup

```bash
cd backend_python
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
# Configure environment variables (DB connections, secrets)
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## Documentation

- **[requirements.md](./requirements.md)** — Full product requirements with 16 detailed user stories covering CGM integration, AI logging, doctor portal, family sharing, voice assistants, and more.
- **[design.md](./design.md)** — Complete system design document including architecture diagrams, database schema, authentication flows, real-time data pipeline, scalability strategy, and deployment architecture.

---

## Roadmap

| Phase | Timeline | Milestone |
|---|---|---|
| **MVP** | Current | Multi-tenant backend + PWA + Real-time sync |
| **Phase 2** | 2 weeks | AI Chat (Bedrock) + Built-in CGM uploaders |
| **Phase 3** | 2 weeks | Alexa/Google Home + ABDM + Multi-language |

---

## License

This project is proprietary. All rights reserved.

---

*Built with purpose. Built from scratch. Built for Bharat.* 🇮🇳
