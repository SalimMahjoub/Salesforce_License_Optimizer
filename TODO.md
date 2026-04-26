# 📋 TODO.md — Salesforce License Optimizer

> **Roadmap de Développement**  
> MVP en 25 jours → Version vendable → Scale  
> Stack: Python 3.12 + FastAPI + PostgreSQL + React + GPT-4

---

## 🎯 Objectifs

- [ ] **MVP (Jour 1-15)** : Démontrer 10k€+ d'économies sur 1 org pilote
- [ ] **Version Vendable (Jour 16-25)** : Premier client signé (revenue share)
- [ ] **Scale (Mois 2-3)** : 10 clients, 100k€/mois de revenus

---

## 📊 Progression Globale

```
Phase 1 - Setup & Infra      [░░░░░░░░░░] 0%
Phase 2 - Data Collection    [░░░░░░░░░░] 0%
Phase 3 - Classification     [░░░░░░░░░░] 0%
Phase 4 - Intelligence GPT-4 [░░░░░░░░░░] 0%
Phase 5 - Dashboard React    [░░░░░░░░░░] 0%
Phase 6 - PDF Generator      [░░░░░░░░░░] 0%
Phase 7 - Monitoring 24/7    [░░░░░░░░░░] 0%
Phase 8 - Tracking ROI       [░░░░░░░░░░] 0%
```

---

## 🚀 Phase 1 — Setup & Infrastructure (Jour 1-2)

### 1.1 Initialisation Projet

- [ ] Créer structure de dossiers selon `ARCHITECTURE.md`
- [ ] Initialiser `pyproject.toml` ou `requirements.txt`
- [ ] Configurer `pre-commit` hooks (black, ruff, mypy)
- [ ] Setup `.env.example` avec toutes les variables

### 1.2 Database Setup

- [ ] Créer `docker-compose.yml` (PostgreSQL + Redis)
- [ ] Configurer Alembic pour migrations
- [ ] Créer migration initiale avec schéma complet :
  - [ ] Table `tenants`
  - [ ] Table `sf_users`
  - [ ] Table `usage_metrics`
  - [ ] Table `recommendations`
  - [ ] Table `security_alerts`
  - [ ] Table `savings_tracking`
- [ ] Tester connexion async avec `asyncpg`

### 1.3 FastAPI Bootstrap

- [ ] Créer `main.py` avec FastAPI app
- [ ] Configurer CORS, middleware logging
- [ ] Setup `config.py` avec pydantic-settings
- [ ] Créer `dependencies.py` pour injection
- [ ] Endpoint health check `/health`
- [ ] Tester avec `uvicorn --reload`

### 1.4 Tests Setup

- [ ] Configurer `pytest` + `pytest-asyncio`
- [ ] Créer `conftest.py` avec fixtures DB
- [ ] Premier test : health check endpoint

**Deliverable :** API FastAPI fonctionnelle avec DB connectée

---

## 🔌 Phase 2 — Data Collection Engine (Jour 3-7)

### 2.1 Salesforce OAuth

- [ ] Créer Connected App sur Salesforce (dev org)
- [ ] Implémenter OAuth 2.0 flow :
  - [ ] Endpoint `/oauth/authorize`
  - [ ] Endpoint `/oauth/callback`
  - [ ] Stockage tokens (chiffrés) en DB
  - [ ] Refresh token automatique
- [ ] Tester connexion avec org de dev

### 2.2 Repository Pattern — Base

```python
# À implémenter dans repositories/base.py
- [ ] class BaseRepository(ABC, Generic[T])
    - [ ] async def get_all() -> List[T]
    - [ ] async def get_by_id(id: str) -> T | None
    - [ ] async def save(entity: T) -> T
```

### 2.3 User Repository (API #1)

```python
# repositories/user_repository.py
- [ ] class SalesforceUserRepository(BaseRepository[SfUser])
    - [ ] QUERY avec Profile.UserLicense.Name
    - [ ] async def get_all_active() -> List[SfUser]
    - [ ] async def get_by_sf_id(sf_id: str) -> SfUser | None
    - [ ] Mapping vers model SfUser
```

**Query SOQL :**
```sql
SELECT Id, Username, Email, LastLoginDate, UserType,
       Profile.Name, Profile.UserLicense.Name,
       Profile.UserLicense.LicenseDefinitionKey
FROM User WHERE IsActive = TRUE
```

### 2.4 LoginEvent Repository (API #2)

```python
# repositories/login_repository.py
- [ ] class LoginEventRepository
    - [ ] async def get_events_last_n_days(days: int) -> List[LoginEvent]
    - [ ] async def get_login_count_by_user(days: int) -> Dict[str, int]
```

**Query SOQL :**
```sql
SELECT UserId, EventType, CreatedDate
FROM LoginEvent
WHERE CreatedDate = LAST_N_DAYS:90
```

### 2.5 Permission Repository (API #3)

```python
# repositories/permission_repository.py
- [ ] class PermissionRepository
    - [ ] async def get_all_assignments() -> List[PermissionAssignment]
    - [ ] async def get_by_user(user_id: str) -> List[PermissionAssignment]
```

**Query SOQL :**
```sql
SELECT AssigneeId, PermissionSet.Name, PermissionSet.Label,
       PermissionSet.IsCustom
FROM PermissionSetAssignment
```

### 2.6 SetupAuditTrail Repository (API #4)

```python
# repositories/audit_repository.py
- [ ] class AuditTrailRepository
    - [ ] async def get_recent_changes(days: int) -> List[AuditEvent]
```

**Query SOQL :**
```sql
SELECT CreatedById, Action, Section, Display, CreatedDate
FROM SetupAuditTrail
ORDER BY CreatedDate DESC
LIMIT 2000
```

### 2.7 EventLogFile Repository (API #5 - Optionnel)

```python
# repositories/eventlog_repository.py
- [ ] class EventLogRepository
    - [ ] async def check_shield_enabled() -> bool
    - [ ] async def get_log_files(event_types: List[str]) -> List[EventLogFile]
    - [ ] async def download_log_content(log_id: str) -> bytes
```

### 2.8 Collection Service

```python
# services/collection_service.py
- [ ] class CollectionService
    - [ ] __init__(user_repo, login_repo, permission_repo, ...)
    - [ ] async def collect_all(org_id: str, days: int) -> CollectionResult
    - [ ] async def _aggregate_metrics(users, logins, permissions) -> List[UserMetrics]
    - [ ] Gestion erreurs et retry
    - [ ] Logging détaillé
```

### 2.9 Tests Collection

- [ ] Test unitaire : SalesforceUserRepository (mock SF client)
- [ ] Test unitaire : LoginEventRepository
- [ ] Test intégration : CollectionService (org de dev)

**Deliverable :** Collecte complète des données Salesforce (5-6 APIs)

---

## 🧮 Phase 3 — Algorithme de Classification (Jour 8-10)

### 3.1 Models

```python
# models/metrics.py
- [ ] @dataclass UserMetrics
    - [ ] user_id: str
    - [ ] license_type: str
    - [ ] license_cost: float
    - [ ] last_login: datetime | None
    - [ ] login_count_90d: int
    - [ ] features_used: set[str]
    - [ ] total_features_available: int
    - [ ] records_created: int
    - [ ] records_modified: int

# models/user.py
- [ ] class UserCategory(Enum): ZOMBIE, CASUAL, POWER, SUPER
- [ ] @dataclass ClassifiedUser
    - [ ] id, username, email
    - [ ] score: int (0-100)
    - [ ] category: UserCategory
    - [ ] license_type, license_cost
    - [ ] days_inactive: int
    - [ ] feature_usage_pct: float
```

### 3.2 Strategy Pattern — Scoring

```python
# strategies/base.py
- [ ] class ScoringStrategy(ABC)
    - [ ] @abstractmethod calculate(metrics: UserMetrics) -> int

# strategies/default_scoring.py
- [ ] class DefaultScoringStrategy(ScoringStrategy)
    - [ ] Dernière connexion (30 pts)
    - [ ] Fréquence connexion (20 pts)
    - [ ] Features utilisées (30 pts)
    - [ ] Records touchés (20 pts)
    - [ ] Tests unitaires
```

### 3.3 License Rules (50+ types)

```python
# factories/license_rules.py
- [ ] LICENSE_CATALOG = {
    'Salesforce': {'price': 150, 'features': [...]},
    'Sales Cloud': {'price': 150, ...},
    'Platform': {'price': 25, ...},
    # ... 50+ types
}
- [ ] DOWNGRADE_PATHS = {...}
- [ ] def get_license_price(license_type: str) -> float
- [ ] def get_downgrade_options(license_type: str) -> List[str]
```

### 3.4 Factory Pattern — Recommendations

```python
# factories/recommendation_factory.py
- [ ] @dataclass Recommendation
    - [ ] user_id, username
    - [ ] current_license, current_cost
    - [ ] recommended_license, recommended_cost
    - [ ] action: 'deactivate' | 'downgrade' | 'keep' | 'upgrade'
    - [ ] monthly_savings, annual_savings
    - [ ] risk_level: 'low' | 'medium' | 'high'
    - [ ] justification: str

- [ ] class RecommendationFactory
    - [ ] def create(user: ClassifiedUser) -> Recommendation
    - [ ] def _create_deactivation(user) -> Recommendation
    - [ ] def _create_downgrade(user) -> Recommendation
    - [ ] def _find_best_downgrade(user) -> str
```

### 3.5 Classification Service

```python
# services/classification_service.py
- [ ] class ClassificationService
    - [ ] __init__(strategy: ScoringStrategy, factory: RecommendationFactory)
    - [ ] async def classify_users(metrics: List[UserMetrics]) -> ClassificationResult
    - [ ] def _score_to_category(score: int) -> UserCategory
    - [ ] async def generate_recommendations(result) -> List[Recommendation]
```

### 3.6 Tests Classification

- [ ] Test DefaultScoringStrategy : cas limites (0, 50, 100)
- [ ] Test RecommendationFactory : chaque catégorie
- [ ] Test ClassificationService : dataset complet mock

**Deliverable :** Classification 4 catégories avec recommandations

---

## 🤖 Phase 4 — Intelligence GPT-4 (Jour 11-13)

### 4.1 Plan Generator Service

```python
# services/plan_generator.py
- [ ] class PlanGenerator
    - [ ] SYSTEM_PROMPT (expert optimisation Salesforce)
    - [ ] USER_PROMPT_TEMPLATE (structure du rapport)
    - [ ] async def generate(result: ClassificationResult) -> str
    - [ ] def _format_top_10(recommendations) -> str
    - [ ] Gestion erreurs OpenAI, retry
```

### 4.2 Prompt Engineering

- [ ] Rédiger SYSTEM_PROMPT optimal
- [ ] Rédiger USER_PROMPT_TEMPLATE avec :
  - [ ] Section SITUATION ACTUELLE
  - [ ] Section ANALYSE D'UTILISATION
  - [ ] Section ÉCONOMIES POTENTIELLES
  - [ ] Section TOP 10 QUICK WINS
  - [ ] Instructions de génération (5 sections)
- [ ] Tester et itérer sur le prompt

### 4.3 API Endpoint Generate Plan

```python
# api/v1/analysis.py
- [ ] @app.post('/api/v1/orgs/{org_id}/generate-plan')
    - [ ] async def generate_plan(org_id: str) -> PlanResponse
    - [ ] Récupère dernière analyse
    - [ ] Appelle PlanGenerator
    - [ ] Retourne markdown formaté
```

### 4.4 Tests GPT-4

- [ ] Test unitaire : formatage prompt (mock OpenAI)
- [ ] Test intégration : génération réelle (budget API)
- [ ] Validation qualité output (structure, ton)

**Deliverable :** Génération plan d'action via GPT-4

---

## 📊 Phase 5 — Dashboard React (Jour 14-18)

### 5.1 Setup Frontend

- [ ] `npm create vite@latest frontend -- --template react-ts`
- [ ] Installer dépendances :
  - [ ] `@tanstack/react-query`
  - [ ] `recharts` (graphiques)
  - [ ] `tailwindcss`
  - [ ] `axios` ou `ky`
- [ ] Configurer proxy API (vite.config.ts)

### 5.2 Composants Principaux

```tsx
// components/Dashboard.tsx
- [ ] Vue principale avec layout
- [ ] Sélecteur d'org
- [ ] Bouton "Lancer analyse"

// components/BudgetComparison.tsx
- [ ] Graphique donut : Budget actuel vs Optimisé
- [ ] Affichage économies potentielles
- [ ] Animation des chiffres

// components/CategoryBreakdown.tsx
- [ ] Bar chart : répartition 4 catégories
- [ ] Couleurs : 🔴 Zombie, 🟡 Casual, 🟢 Power, 🟣 Super
- [ ] Tooltip avec détails

// components/UserTable.tsx
- [ ] Tableau paginé des users classifiés
- [ ] Colonnes : Username, Licence, Score, Catégorie, Recommandation
- [ ] Tri et filtres
- [ ] Export CSV

// components/SavingsChart.tsx
- [ ] Line chart : économies cumulées dans le temps
- [ ] Projection 12 mois

// components/AlertsPanel.tsx
- [ ] Liste alertes sécurité
- [ ] Badge par sévérité
- [ ] Actions rapides
```

### 5.3 Hooks TanStack Query

```tsx
// hooks/useAnalysis.ts
- [ ] useAnalyzeOrg(orgId: string)
- [ ] useClassification(orgId: string)
- [ ] useRecommendations(orgId: string)
- [ ] useGeneratePlan(orgId: string)
- [ ] useSavings(orgId: string)
- [ ] useAlerts(orgId: string)
```

### 5.4 Pages

- [ ] `/` — Dashboard principal
- [ ] `/analysis/:orgId` — Détails analyse
- [ ] `/recommendations/:orgId` — Liste recommandations
- [ ] `/alerts` — Centre d'alertes
- [ ] `/settings` — Configuration

### 5.5 Tests Frontend

- [ ] Tests composants (React Testing Library)
- [ ] Test hooks (mock API)

**Deliverable :** Dashboard React fonctionnel

---

## 📄 Phase 6 — PDF Generator (Jour 19-21)

### 6.1 Template HTML/CSS

```python
# services/pdf_generator.py
- [ ] class PDFGenerator
    - [ ] TEMPLATE_HTML (Jinja2)
    - [ ] STYLES_CSS (professionnel, CFO-ready)
```

### 6.2 Structure PDF (30-40 pages)

- [ ] Page de garde (logo, titre, date)
- [ ] Table des matières
- [ ] Executive Summary (2 pages)
  - [ ] KPIs clés
  - [ ] Recommandation principale
  - [ ] ROI attendu
- [ ] Méthodologie (3 pages)
- [ ] Résultats détaillés (20 pages)
  - [ ] Graphiques
  - [ ] Tableaux par catégorie
  - [ ] Top 50 recommandations
- [ ] Plan d'action (5 pages)
  - [ ] Timeline
  - [ ] Risques
  - [ ] Quick wins
- [ ] Annexes (data brute)

### 6.3 Implémentation WeasyPrint

```python
- [ ] async def generate(result: ClassificationResult, plan: str) -> bytes
- [ ] def _render_template(data: dict) -> str
- [ ] def _generate_charts_base64(data: dict) -> dict
- [ ] Gestion fonts, images
```

### 6.4 API Endpoint PDF

```python
# api/v1/reports.py
- [ ] @app.get('/api/v1/orgs/{org_id}/report/pdf')
    - [ ] Response avec Content-Type: application/pdf
    - [ ] Content-Disposition: attachment
```

### 6.5 Tests PDF

- [ ] Test génération (vérifier PDF valide)
- [ ] Test visuel (review manuel)

**Deliverable :** Rapport PDF 30-40 pages CFO-ready

---

## 🔒 Phase 7 — Monitoring Sécurité 24/7 (Jour 22-23)

### 7.1 Observer Pattern — EventBus

```python
# events/event_bus.py
- [ ] @dataclass Event(type: str, payload: dict, timestamp: datetime)
- [ ] class EventBus
    - [ ] _subscribers: Dict[str, List[Callable]]
    - [ ] def subscribe(event_type, handler)
    - [ ] async def publish(event: Event)
```

### 7.2 Permission Monitor

```python
# services/permission_monitor.py
- [ ] CRITICAL_PERMISSIONS = ['ModifyAllData', 'ViewAllData', ...]
- [ ] class PermissionMonitor
    - [ ] async def check_anomalies(permissions) -> List[SecurityAlert]
    - [ ] Règle 1: Permission critique sur non-admin
    - [ ] Règle 2: Permission inutilisée 90+ jours
    - [ ] Règle 3: Nouvelle permission critique
```

### 7.3 Event Handlers

```python
# events/handlers/
- [ ] slack_handler.py : Webhook Slack
- [ ] email_handler.py : SMTP notifications
- [ ] audit_handler.py : Logging en DB
```

### 7.4 Scheduler (Collecte Périodique)

- [ ] Intégrer APScheduler ou Celery Beat
- [ ] Job quotidien : collecte + check anomalies
- [ ] Job hebdomadaire : rapport complet

### 7.5 API Endpoints Alertes

```python
# api/v1/alerts.py
- [ ] GET /api/v1/orgs/{org_id}/alerts
- [ ] PATCH /api/v1/alerts/{alert_id}/acknowledge
- [ ] PATCH /api/v1/alerts/{alert_id}/resolve
```

**Deliverable :** Monitoring sécurité avec alertes temps réel

---

## 💰 Phase 8 — Tracking ROI & Facturation (Jour 24-25)

### 8.1 Savings Tracker Service

```python
# services/savings_tracker.py
- [ ] @dataclass SavingsReport
    - [ ] baseline_monthly_cost
    - [ ] current_monthly_cost
    - [ ] monthly_savings
    - [ ] cumulative_savings
    - [ ] commission_rate (0.30)
    - [ ] commission_due
    - [ ] net_savings
    - [ ] months_active
    - [ ] contract_end_date

- [ ] class SavingsTracker
    - [ ] async def calculate_savings(org_id: str) -> SavingsReport
    - [ ] async def record_monthly_snapshot(org_id: str)
```

### 8.2 Baseline Management

```python
- [ ] async def set_baseline(org_id: str, analysis: ClassificationResult)
- [ ] async def get_baseline(org_id: str) -> Baseline
- [ ] Logique : baseline = coût au moment du premier audit
```

### 8.3 API Endpoint Savings

```python
# api/v1/analysis.py
- [ ] GET /api/v1/orgs/{org_id}/savings
    - [ ] Retourne SavingsReport
    - [ ] Graphique économies cumulées
```

### 8.4 Dashboard Widget Savings

```tsx
// components/SavingsTracker.tsx
- [ ] Affichage temps réel des économies
- [ ] "Économies à ce jour : 626 400€"
- [ ] "Votre commission : 187 920€"
- [ ] "Économie nette : 438 480€"
- [ ] Countdown fin contrat 12 mois
```

**Deliverable :** Tracking ROI pour justifier facturation

---

## 🧪 Tests & Qualité

### Tests Unitaires

- [ ] Coverage > 80% sur services
- [ ] Tests strategies (scoring)
- [ ] Tests factories (recommendations)
- [ ] Tests repositories (mock SF)

### Tests Intégration

- [ ] Test flow complet : OAuth → Collecte → Classification → Plan
- [ ] Test avec org Salesforce de dev
- [ ] Test génération PDF

### Tests E2E (Optionnel)

- [ ] Playwright ou Cypress
- [ ] Scénario : login → analyse → export PDF

---

## 📦 Déploiement

### Docker

- [ ] `Dockerfile` backend (Python)
- [ ] `Dockerfile` frontend (Node + nginx)
- [ ] `docker-compose.yml` complet
- [ ] Healthchecks

### CI/CD (GitHub Actions)

- [ ] Workflow : lint + test + build
- [ ] Build images Docker
- [ ] Push vers registry

### Hébergement (MVP)

- [ ] Option 1 : Railway / Render
- [ ] Option 2 : AWS (ECS ou Lambda)
- [ ] PostgreSQL managé (Neon / Supabase / RDS)
- [ ] Redis managé (Upstash / ElastiCache)

---

## 📅 Timeline Récapitulatif

| Phase | Jours | Tâches principales | Deliverable |
|-------|-------|---------------------|-------------|
| 1 | 1-2 | Setup, DB, FastAPI bootstrap | API fonctionnelle |
| 2 | 3-7 | OAuth, 5-6 Repositories, Collection | Collecte Salesforce |
| 3 | 8-10 | Scoring, Classification, Factory | 4 catégories + recommandations |
| 4 | 11-13 | GPT-4 integration, Prompt engineering | Plan d'action généré |
| 5 | 14-18 | Dashboard React complet | UI fonctionnelle |
| 6 | 19-21 | PDF Generator 30-40 pages | Rapport CFO-ready |
| 7 | 22-23 | EventBus, Monitoring, Alertes | Sécurité 24/7 |
| 8 | 24-25 | Savings Tracker, ROI | Facturation justifiée |

---

## 🎯 Critères de Succès MVP

- [ ] ✅ Connexion OAuth à org Salesforce
- [ ] ✅ Collecte 5-6 APIs sans erreur
- [ ] ✅ Classification 4 catégories correcte
- [ ] ✅ Calcul économies > 10k€ sur org test
- [ ] ✅ Plan GPT-4 généré (qualité CFO-ready)
- [ ] ✅ Dashboard affiche comparaison budget
- [ ] ✅ PDF 30+ pages exportable
- [ ] ✅ Alertes sécurité fonctionnelles
- [ ] ✅ Tracking économies temps réel

---

## 🚀 Post-MVP (Mois 2-3)

- [ ] Multi-tenant complet
- [ ] Onboarding self-service
- [ ] White-label pour ESN
- [ ] API publique (OpenAPI)
- [ ] Intégration Slack avancée
- [ ] Mobile responsive
- [ ] Benchmarks industrie
- [ ] ML predictions (anticipation)

---

## 📝 Notes Cursor IDE

### Commandes Utiles

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Docker
docker-compose up -d
docker-compose logs -f

# Tests
pytest -v --cov=app
npm test
```

### Extensions Recommandées

- Python (ms-python.python)
- Pylance
- Ruff
- ES7+ React/Redux
- Tailwind CSS IntelliSense
- Thunder Client (API testing)

### Snippets Cursor

```
# Créer un nouveau repository
cursor: "Créer SalesforceUserRepository selon ARCHITECTURE.md"

# Créer un service
cursor: "Implémenter ClassificationService avec Strategy pattern"

# Créer un composant React
cursor: "Créer BudgetComparison.tsx avec Recharts"
```

---

> **Last updated:** 29 décembre 2025  
> **Status:** Phase 1 - Setup
