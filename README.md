# Salesforce License Optimizer

> **« Le chirurgien des budgets Salesforce »**
> FastAPI + React + GPT-4 + WeasyPrint. Détecte 20-40 % d'économies sur les licences SF.

---

## Quickstart (3 minutes, sans Salesforce)

```bash
git clone <repo>
cd SalesforceLicenseOptimizer
cp .env.example .env

# Génère les deux clés requises
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(48))"      >> .env
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())" >> .env

# DATA_PROVIDER=demo par défaut — pas besoin de Salesforce
docker-compose up --build
```

- **Frontend** : http://localhost:3000 — login `demo@uprizon.io` / `demo-password`
- **API docs** : http://localhost:8000/docs
- **Health** : http://localhost:8000/health

Le `DemoDataProvider` génère 800 utilisateurs réalistes à la volée — vous obtenez
immédiatement dashboard, recommandations, plan CFO et alertes de sécurité.

---

## Brancher une vraie org Salesforce

1. Créer une **Connected App** Salesforce (Setup > App Manager > New).
2. Renseigner dans `.env` :
   ```
   DATA_PROVIDER=salesforce
   SF_CLIENT_ID=...
   SF_CLIENT_SECRET=...
   SF_REDIRECT_URI=http://localhost:8000/oauth/callback
   ```
3. `docker-compose up`, puis ouvrir `/api/v1/auth/authorize` → callback Salesforce.

---

## Stack

| Couche | Tech |
|---|---|
| Backend | FastAPI 0.115, Pydantic v2, SQLAlchemy 2 async, Alembic |
| Données | PostgreSQL 16, Redis 7 (cache GPT-4 + slowapi) |
| Salesforce | simple-salesforce (OAuth 2.0, OAuth tokens chiffrés Fernet) |
| IA | OpenAI GPT-4 (PlanGenerator) + fallback déterministe |
| PDF | WeasyPrint + Jinja2 |
| Frontend | React 18, Vite, TypeScript strict, Tailwind, TanStack Query, Zustand |
| Auth | JWT HS256 + bcrypt (passlib) |
| Observabilité | logs JSON optionnels + Sentry optionnel + X-Request-ID middleware |
| CI | GitHub Actions : ruff, black, mypy, pytest, tsc, vitest, build Docker, gitleaks |

---

## Architecture (vue tech lead)

```
                ┌────────────────────────────────────────────┐
                │            React SPA (Vite)                │
                │  Dashboard │ Zombies │ Recos │ Reports │   │
                │            │            │ Alerts │         │
                └───────────────────┬────────────────────────┘
                                    │ JWT (Bearer)
                ┌───────────────────▼────────────────────────┐
                │           FastAPI /api/v1                  │
                │  auth │ analysis │ recos │ reports │ alerts │
                │   ↓ require_tenant_match (multi-tenant)    │
                │   ↓ slowapi rate-limit                     │
                └───────────────────┬────────────────────────┘
                                    │
        ┌───────────────────────────┼────────────────────────┐
        ▼                           ▼                        ▼
  AnalysisService            PlanGenerator (GPT-4)    PermissionMonitor
  (cache TTL 5 min)          + Redis cache 24h        (security alerts)
        │                           │
        ▼                           ▼
  DataProvider strategy       PDFService (WeasyPrint)
  ├── DemoDataProvider
  └── SalesforceDataProvider
        │
        ▼
  simple_salesforce (OAuth + SOQL via asyncio.to_thread)
```

---

## Endpoints clés

| Méthode | Route | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Login (form `username`/`password`) → JWT |
| GET  | `/api/v1/auth/me` | Profil du token courant |
| GET  | `/api/v1/analysis/{org}/dashboard` | KPIs synthétiques |
| GET  | `/api/v1/analysis/{org}/zombies` | Utilisateurs inactifs + économies |
| GET  | `/api/v1/analysis/{org}/users?category=` | Liste paginée filtrée |
| POST | `/api/v1/analysis/{org}/refresh` | Bypass cache (rate-limit 5/min) |
| GET  | `/api/v1/recommendations/{org}` | Recos triées par priorité/savings |
| GET  | `/api/v1/reports/{org}/cfo-plan` | Plan CFO GPT-4 (rate-limit 10/min) |
| GET  | `/api/v1/reports/{org}/pdf` | PDF download (rate-limit 3/min) |
| GET  | `/api/v1/alerts/{org}` | Alertes de sécurité (orphan admins…) |

Tous les endpoints data appliquent `require_tenant_match` : le `tenant_id`
du JWT doit matcher l'`org` de l'URL — anti-IDOR garanti par construction.

---

## Tests

```bash
# Backend
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest

# Frontend
cd frontend
npm install
npm test
```

Le `conftest.py` provisionne des env vars dummy + 2 fixtures (`client`
authentifié sur `test-org`, `unauth_client` pour les tests d'auth) — pas
besoin d'infrastructure pour faire tourner la suite.

---

## Roadmap

Voir [TODO.md](TODO.md). État actuel (post Sprint 4) :

```
Phase 0 - Sprint 0 hardening    ██████████ 100%
Phase 1 - Setup & Infra         ██████████ 100%
Phase 2 - Data Collection       ██████████ 100% (Demo + SF providers)
Phase 3 - Classification        ██████████ 100%
Phase 4 - Intelligence GPT-4    ██████████ 100% (Redis cache + budget guard)
Phase 5 - Dashboard React       ██████████ 100% (5 pages branchées API)
Phase 6 - PDF Generator         ██████████ 100% (WeasyPrint endpoint)
Phase 7 - Security Monitor      ██████████  90% (perm monitor v1 + alerts UI)
Phase 8 - Auth & Multi-tenant   ██████████  90% (JWT + tenant guard, DB user store TODO)
```

---

Copyright © 2026 Uprizon — AXIOMCORE
