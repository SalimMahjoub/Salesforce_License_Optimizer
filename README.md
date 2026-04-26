# 🏗️ Salesforce License Optimizer

> **"Le Chirurgien des Budgets Salesforce"**  
> Optimisation financière automatique des licences Salesforce  
> Stack: Python 3.12 + FastAPI + PostgreSQL + React + GPT-4

---

## 📋 Overview

Salesforce License Optimizer analyzes license usage patterns and identifies optimization opportunities that can save 20-40% on Salesforce licensing costs.

**Key Features:**
- Automated data collection from 5-6 Salesforce APIs
- AI-powered classification using scoring algorithms
- GPT-4 generated action plans for CFOs
- Real-time security monitoring
- ROI tracking with commission calculation

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SalesforceLicenseOptimizer
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

### 3. Start All Services

```bash
docker-compose up --build
```

This will start:
- **PostgreSQL** (port 5432)
- **Redis** (port 6379)
- **Backend API** (port 8000)

### 4. Verify Installation

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-29T..."
}
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SALESFORCE ORG                       │
│  User API │ LoginEvent API │ PermissionSet │ EventLog  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              PYTHON BACKEND (FastAPI)                   │
│  Repositories → Services → Intelligence Layer (GPT-4)   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                REACT FRONTEND                           │
│  Dashboard │ Budget Comparison │ Reports │ Alerts      │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
.
├── backend/              # Python FastAPI application
│   ├── app/
│   │   ├── main.py       # FastAPI entry point
│   │   ├── config.py     # Pydantic settings
│   │   ├── models/       # Data models
│   │   ├── repositories/ # Data access layer
│   │   ├── services/     # Business logic
│   │   ├── strategies/   # Scoring algorithms
│   │   ├── factories/    # Recommendation factories
│   │   ├── events/       # Event bus & handlers
│   │   └── api/v1/       # API routes
│   ├── tests/            # Test suite
│   └── requirements.txt  # Python dependencies
│
├── frontend/             # React + TypeScript (Coming Soon)
│
├── docker-compose.yml    # Infrastructure orchestration
├── .env.example          # Environment template
└── README.md             # This file
```

---

## 🛠️ Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

### Run Tests

```bash
cd backend
pytest -v --cov=app
```

### Code Quality

```bash
# Format code
black app/

# Lint
ruff check app/

# Type checking
mypy app/
```

---

## 📊 Business Impact

**Typical Savings for 800 Users (€1.44M/year budget):**

| Category | Users | Problem | Savings/year |
|----------|-------|---------|--------------|
| Zombies | 240 (30%) | Not connected 6+ months | €345,600 |
| Over-licensed | 180 (22%) | Sales Cloud → Platform | €194,400 |
| Unused Einstein | 60 (8%) | Add-on never used | €86,400 |
| **TOTAL** | 480 users | 43% of budget | **€626,400/year** |

---

## 🔒 Security

- Zero access to business data (opportunities, contacts, accounts)
- Only metadata and usage logs analyzed
- Encrypted credential storage
- 24/7 permission monitoring with alerts
- Non-root Docker containers

---

## 📚 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed technical architecture
- [TODO.md](TODO.md) - Development roadmap

---

## 🤝 Contributing

This project follows enterprise-grade development practices:
- Design patterns (Repository, Strategy, Factory, Observer)
- Comprehensive test coverage (>80%)
- Type safety with Pydantic v2
- Async/await throughout
- Docker-first development

---

## 📝 License

Copyright © 2025 Uprizon - AXIOMCORE

---

## 🚀 Roadmap

- [x] **Phase 1**: Infrastructure setup
- [ ] **Phase 2**: Data collection engine (5-6 Salesforce APIs)
- [ ] **Phase 3**: Classification algorithm
- [ ] **Phase 4**: GPT-4 action plan generation
- [ ] **Phase 5**: React dashboard
- [ ] **Phase 6**: PDF report generator (30-40 pages)
- [ ] **Phase 7**: 24/7 security monitoring
- [ ] **Phase 8**: ROI tracking & billing

---

> **Status**: Phase 1 - Infrastructure Setup Complete ✅  
> **Last Updated**: December 29, 2025

