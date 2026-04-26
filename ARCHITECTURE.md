# 🏗️ ARCHITECTURE.md — Salesforce License Optimizer

> **"Le Chirurgien des Budgets Salesforce"**  
> Optimisation financière automatique des licences Salesforce  
> Stack: Python 3.12 + FastAPI + PostgreSQL + React + GPT-4

---

## 📋 Table des Matières

1. [Objectif Business](#-objectif-business)
2. [Stack Technologique](#-stack-technologique)
3. [Design Patterns](#-design-patterns)
4. [Architecture Globale](#-architecture-globale)
5. [Structure du Projet](#-structure-du-projet)
6. [Collecte Salesforce (5-6 APIs)](#-collecte-salesforce-5-6-apis)
7. [Algorithme de Classification](#-algorithme-de-classification)
8. [Génération Plan GPT-4](#-génération-plan-gpt-4)
9. [Monitoring Sécurité 24/7](#-monitoring-sécurité-247)
10. [API Endpoints](#-api-endpoints)
11. [Modèle de Données](#-modèle-de-données)
12. [Configuration](#-configuration)

---

## 🎯 Objectif Business

### Le Problème : Le Gaspillage Invisible

**20-40% des licences Salesforce sont gaspillées** dans les grandes entreprises :
- Licence Sales Cloud : **150€/mois/user**
- Licence Platform : **25€/mois/user**
- Beaucoup d'utilisateurs paient 150€ alors que 25€ suffirait

### Cas Concret (800 users, budget 1.44M€/an)

| Catégorie | Users | Problème | Économie/an |
|-----------|-------|----------|-------------|
| **Zombies** | 240 (30%) | Pas connectés 6+ mois | 345 600€ |
| **Sur-licensés** | 180 (22%) | Sales Cloud → Platform | 194 400€ |
| **Einstein inutilisé** | 60 (8%) | Add-on jamais utilisé | 86 400€ |
| **TOTAL** | 480 users | 43% du budget | **626 400€/an** |

### Ce qu'on analyse (Zero-Knowledge)

- ✅ **Métadonnées licences** : Qui a quelle licence (50+ types)
- ✅ **Logs d'activité** : Dernière connexion, fréquence, features
- ✅ **Permissions & Profils** : Accès accordés vs utilisés
- ❌ **Zéro donnée business** : Pas d'accès aux opportunités, contacts, comptes

---

## 🛠️ Stack Technologique

| Couche | Technologie | Version | Rôle |
|--------|-------------|---------|------|
| **Backend** | Python + FastAPI | 3.12 / 0.109+ | API REST, async I/O |
| **Salesforce** | simple-salesforce | 1.12+ | 5-6 endpoints REST API |
| **Database** | PostgreSQL + SQLAlchemy | 16 / 2.0+ | Stockage, agrégation |
| **Cache** | Redis | 7+ | Sessions, rate limiting |
| **Intelligence** | OpenAI GPT-4 | API | Plans d'action CFO-ready |
| **Frontend** | React + TanStack Query | 18 / 5+ | Dashboard comparatif |
| **PDF** | WeasyPrint | 60+ | Rapports 30-40 pages |
| **Testing** | pytest + pytest-asyncio | 8+ | Tests unitaires/intégration |

### Dépendances Python Principales

```txt
# backend/requirements.txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
simple-salesforce>=1.12.0
openai>=1.10.0
redis>=5.0.0
weasyprint>=60.0
httpx>=0.26.0
python-multipart>=0.0.6
```

---

## 🧩 Design Patterns

### 1. Repository Pattern — Accès Données

Abstrait l'accès aux données Salesforce et PostgreSQL.

```python
# repositories/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_all(self) -> List[T]: ...
    
    @abstractmethod
    async def get_by_id(self, id: str) -> T | None: ...
    
    @abstractmethod
    async def save(self, entity: T) -> T: ...
```

### 2. Strategy Pattern — Scoring

Permet de changer l'algorithme de scoring sans modifier le code appelant.

```python
# strategies/base.py
from abc import ABC, abstractmethod
from models import UserMetrics

class ScoringStrategy(ABC):
    @abstractmethod
    def calculate(self, metrics: UserMetrics) -> int:
        """Retourne un score 0-100"""
        ...
```

### 3. Factory Pattern — Recommandations

Crée les recommandations appropriées selon la classification.

```python
# factories/recommendation_factory.py
class RecommendationFactory:
    """Génère des recommandations basées sur 200+ règles métier"""
    
    LICENSE_PRICES = {
        'Salesforce': 150, 'Sales Cloud': 150,
        'Platform': 25, 'Chatter Free': 0,
        # ... 50+ types
    }
    
    def create(self, user: ClassifiedUser) -> Recommendation:
        match user.category:
            case UserCategory.ZOMBIE:
                return self._create_deactivation(user)
            case UserCategory.CASUAL:
                return self._create_downgrade(user)
            # ...
```

### 4. Observer Pattern — Events & Alertes

Découple la génération d'événements de leur traitement.

```python
# events/event_bus.py
class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        self._subscribers.setdefault(event_type, []).append(handler)
    
    async def publish(self, event: Event):
        for handler in self._subscribers.get(event.type, []):
            await handler(event)
```

---

## 🏛️ Architecture Globale

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SALESFORCE ORG (Client)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ User Query   │  │ LoginEvent   │  │ PermissionSet│  │ EventLog   │  │
│  │    API       │  │    API       │  │    API       │  │ File API   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘  │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     PYTHON BACKEND (FastAPI)                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  REPOSITORIES (Data Access Layer)                               │   │
│  │  UserRepo │ LoginEventRepo │ PermissionRepo │ EventLogRepo      │   │
│  └─────────────────────────────┬───────────────────────────────────┘   │
│                                │                                        │
│  ┌─────────────────────────────┴───────────────────────────────────┐   │
│  │  SERVICES (Business Logic)                                      │   │
│  │  CollectionService │ ClassificationService │ RecommendationSvc  │   │
│  └─────────────────────────────┬───────────────────────────────────┘   │
│                                │                                        │
│  ┌─────────────────────────────┴───────────────────────────────────┐   │
│  │  INTELLIGENCE LAYER                                             │   │
│  │  ScoringStrategy (0-100) │ RuleEngine (200+ rules) │ GPT-4 API  │   │
│  └─────────────────────────────┬───────────────────────────────────┘   │
│                                │                                        │
│  ┌──────────────┐  ┌───────────┴───────────┐  ┌────────────────────┐   │
│  │  PostgreSQL  │  │      EventBus         │  │   PDF Generator    │   │
│  │  (Metrics)   │  │  (Observer Pattern)   │  │   (WeasyPrint)     │   │
│  └──────────────┘  └───────────────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────────────────┐
│                       REACT FRONTEND                                    │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │
│  │ Dashboard      │  │ Comparaison      │  │ Export PDF             │  │
│  │ Budget Actuel  │  │ Actuel/Optimisé  │  │ 30-40 pages CFO-ready  │  │
│  └────────────────┘  └──────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Structure du Projet

```
salesforce-license-optimizer/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application
│   │   ├── config.py                  # Settings (pydantic-settings)
│   │   ├── dependencies.py            # Dependency injection
│   │   │
│   │   ├── models/                    # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── user.py                # SfUser, ClassifiedUser
│   │   │   ├── metrics.py             # UserMetrics, UsageStats
│   │   │   ├── recommendation.py      # Recommendation, ActionPlan
│   │   │   └── license.py             # LicenseType, LicensePrice
│   │   │
│   │   ├── repositories/              # Repository Pattern
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # BaseRepository ABC
│   │   │   ├── user_repository.py     # SalesforceUserRepository
│   │   │   ├── login_repository.py    # LoginEventRepository
│   │   │   ├── permission_repository.py
│   │   │   └── eventlog_repository.py
│   │   │
│   │   ├── strategies/                # Strategy Pattern
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # ScoringStrategy ABC
│   │   │   ├── default_scoring.py     # DefaultScoringStrategy
│   │   │   └── aggressive_scoring.py  # Variante plus stricte
│   │   │
│   │   ├── factories/                 # Factory Pattern
│   │   │   ├── __init__.py
│   │   │   ├── recommendation_factory.py  # 200+ règles métier
│   │   │   └── license_rules.py       # Règles 50+ licences
│   │   │
│   │   ├── services/                  # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── collection_service.py  # Orchestration collecte
│   │   │   ├── classification_service.py
│   │   │   ├── plan_generator.py      # GPT-4 integration
│   │   │   ├── pdf_generator.py       # WeasyPrint
│   │   │   ├── savings_tracker.py     # ROI tracking
│   │   │   └── permission_monitor.py  # Sécurité 24/7
│   │   │
│   │   ├── events/                    # Observer Pattern
│   │   │   ├── __init__.py
│   │   │   ├── event_bus.py           # EventBus central
│   │   │   └── handlers/
│   │   │       ├── __init__.py
│   │   │       ├── slack_handler.py   # Alertes Slack
│   │   │       ├── email_handler.py   # Notifications email
│   │   │       └── audit_handler.py   # Logging audit
│   │   │
│   │   └── api/v1/                    # Routes FastAPI
│   │       ├── __init__.py
│   │       ├── router.py              # Router principal
│   │       ├── analysis.py
│   │       ├── recommendations.py
│   │       ├── reports.py
│   │       └── alerts.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                # Fixtures pytest
│   │   ├── test_repositories/
│   │   ├── test_services/
│   │   ├── test_strategies/
│   │   └── test_api/
│   │
│   ├── alembic/                       # Migrations DB
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
│
├── frontend/                          # React app
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx          # Vue principale
│   │   │   ├── BudgetComparison.tsx   # Actuel vs Optimisé
│   │   │   ├── UserTable.tsx          # Liste users classifiés
│   │   │   ├── SavingsChart.tsx       # Graphique économies
│   │   │   └── AlertsPanel.tsx        # Alertes sécurité
│   │   ├── hooks/
│   │   │   └── useAnalysis.ts         # TanStack Query
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
├── ARCHITECTURE.md                    # Ce fichier
├── TODO.md                            # Tâches de développement
└── README.md
```

---

## 🔌 Collecte Salesforce (5-6 APIs)

### APIs et Queries SOQL

| # | API | Query SOQL | Volume estimé |
|---|-----|------------|---------------|
| 1 | **User** | `SELECT Id, Username, LastLoginDate, UserType, Profile.Name, Profile.UserLicense.Name FROM User WHERE IsActive=TRUE` | ~1000 records |
| 2 | **LoginEvent** | `SELECT UserId, EventType, CreatedDate FROM LoginEvent WHERE CreatedDate=LAST_N_DAYS:90` | ~50k records |
| 3 | **PermissionSetAssignment** | `SELECT AssigneeId, PermissionSet.Name, PermissionSet.Label FROM PermissionSetAssignment` | ~5k records |
| 4 | **SetupAuditTrail** | `SELECT CreatedById, Action, Section, CreatedDate FROM SetupAuditTrail ORDER BY CreatedDate DESC` | ~10k records |
| 5 | **EventLogFile** | `SELECT Id, EventType, LogDate FROM EventLogFile WHERE EventType IN ('Login','Report','Dashboard')` | Si Shield actif |
| 6 | **FieldHistoryTracking** | Via Metadata API | Config dépendante |

### Implémentation Repository

```python
# repositories/user_repository.py
from simple_salesforce import Salesforce
from typing import List
from models import SfUser

class SalesforceUserRepository:
    """Repository pour les utilisateurs Salesforce actifs"""
    
    QUERY = """
        SELECT Id, Username, Email, LastLoginDate, UserType,
               Profile.Name, Profile.UserLicense.Name,
               Profile.UserLicense.LicenseDefinitionKey
        FROM User
        WHERE IsActive = TRUE
    """
    
    def __init__(self, sf_client: Salesforce):
        self._sf = sf_client
    
    async def get_all_active(self) -> List[SfUser]:
        """Récupère tous les utilisateurs actifs avec leur licence"""
        result = self._sf.query_all(self.QUERY)
        return [
            SfUser(
                id=r['Id'],
                username=r['Username'],
                email=r['Email'],
                last_login=r['LastLoginDate'],
                user_type=r['UserType'],
                profile_name=r['Profile']['Name'],
                license_type=r['Profile']['UserLicense']['Name'],
                license_key=r['Profile']['UserLicense']['LicenseDefinitionKey']
            )
            for r in result['records']
        ]
```

### Les 50+ Types de Licences Salesforce

```python
# factories/license_rules.py
LICENSE_CATALOG = {
    # Licences principales
    'Salesforce': {'price': 150, 'features': ['full_crm']},
    'Sales Cloud': {'price': 150, 'features': ['opportunities', 'leads', 'forecasting']},
    'Service Cloud': {'price': 150, 'features': ['cases', 'knowledge', 'omnichannel']},
    'Sales Cloud Einstein': {'price': 200, 'features': ['sales_cloud', 'ai_scoring']},
    
    # Licences économiques
    'Platform': {'price': 25, 'features': ['custom_objects']},
    'Platform Plus': {'price': 100, 'features': ['platform', 'advanced_api']},
    'Essentials': {'price': 25, 'features': ['basic_crm'], 'max_users': 10},
    
    # Licences gratuites/minimales
    'Chatter Free': {'price': 0, 'features': ['collaboration']},
    'Identity': {'price': 5, 'features': ['sso_only']},
    
    # ... 40+ autres types
}

DOWNGRADE_PATHS = {
    'Sales Cloud': ['Platform', 'Essentials', 'Chatter Free'],
    'Service Cloud': ['Platform', 'Essentials', 'Chatter Free'],
    'Sales Cloud Einstein': ['Sales Cloud', 'Platform'],
    'Platform Plus': ['Platform', 'Chatter Free'],
}
```

---

## 🧮 Algorithme de Classification

### Formule de Scoring (0-100)

| Critère | Poids | Logique | Points max |
|---------|-------|---------|------------|
| **Dernière connexion** | 30% | >90j=0, 30-90j=15, <30j=30 | 30 |
| **Fréquence connexion** | 20% | min(logins_semaine × 4, 20) | 20 |
| **Features utilisées** | 30% | (features_used / total) × 30 | 30 |
| **Records touchés** | 20% | min(records / 5, 20) | 20 |

### Implémentation Strategy

```python
# strategies/default_scoring.py
from datetime import datetime, timedelta
from dataclasses import dataclass
from strategies.base import ScoringStrategy

@dataclass
class UserMetrics:
    user_id: str
    license_type: str
    license_cost: float
    last_login: datetime | None
    login_count_90d: int
    features_used: set[str]
    total_features_available: int
    records_created: int
    records_modified: int

class DefaultScoringStrategy(ScoringStrategy):
    """Algorithme de scoring standard utilisé en production"""
    
    def calculate(self, m: UserMetrics) -> int:
        score = 0
        now = datetime.utcnow()
        
        # 1. Dernière connexion (30 points max)
        if m.last_login is None:
            score += 0  # Jamais connecté = Zombie
        elif (now - m.last_login) > timedelta(days=90):
            score += 0  # Inactif 90+ jours
        elif (now - m.last_login) > timedelta(days=30):
            score += 15  # Inactif 30-90 jours
        else:
            score += 30  # Actif récemment
        
        # 2. Fréquence de connexion (20 points max)
        weekly_logins = m.login_count_90d / 13  # 90 jours ≈ 13 semaines
        score += min(int(weekly_logins * 4), 20)
        
        # 3. Features utilisées (30 points max)
        if m.total_features_available > 0:
            feature_ratio = len(m.features_used) / m.total_features_available
            score += int(feature_ratio * 30)
        
        # 4. Records touchés (20 points max)
        records_touched = m.records_created + m.records_modified
        score += min(records_touched // 5, 20)
        
        return min(score, 100)
```

### Classification en 4 Catégories

| Catégorie | Score | Comportement | Recommandation | Économie |
|-----------|-------|--------------|----------------|----------|
| **ZOMBIE** 🔴 | 0-10 | Pas connecté 90+ jours | Désactiver | 150€/mois |
| **CASUAL** 🟡 | 11-30 | Connexions sporadiques | → Platform (25€) | 125€/mois |
| **POWER** 🟢 | 31-70 | Usage régulier | Garder licence | 0€ |
| **SUPER** 🟣 | 71-100 | Usage intensif | Upgrade Einstein? | -50€/mois |

```python
# models/user.py
from enum import Enum

class UserCategory(Enum):
    ZOMBIE = 'zombie'    # 0-10
    CASUAL = 'casual'    # 11-30
    POWER = 'power'      # 31-70
    SUPER = 'super'      # 71-100

def score_to_category(score: int) -> UserCategory:
    if score <= 10:
        return UserCategory.ZOMBIE
    elif score <= 30:
        return UserCategory.CASUAL
    elif score <= 70:
        return UserCategory.POWER
    else:
        return UserCategory.SUPER
```

---

## 🤖 Génération Plan GPT-4

### Prompt Template

```python
# services/plan_generator.py
from openai import AsyncOpenAI

class PlanGenerator:
    """Génère le plan d'optimisation via GPT-4"""
    
    SYSTEM_PROMPT = """
Tu es un expert en optimisation des coûts Salesforce.
Tu génères des rapports professionnels pour les CFO et DSI.
Ton ton est : data-driven, orienté business, professionnel.
Tu fournis toujours des chiffres précis et des actions concrètes.
"""
    
    USER_PROMPT_TEMPLATE = """
Génère un plan d'optimisation Salesforce complet :

## SITUATION ACTUELLE
- Entreprise : {company_name}
- Budget licences annuel : {budget_actuel:,.0f}€ ({total_users} utilisateurs)
- Coût moyen par utilisateur : {cout_moyen:.0f}€/mois

## ANALYSE D'UTILISATION (90 derniers jours)
| Catégorie | Users | % | Comportement |
|-----------|-------|---|--------------|
| Zombies | {zombies} | {zombies_pct:.1f}% | Inactifs 90+ jours |
| Casual | {casual} | {casual_pct:.1f}% | Usage <30% features |
| Power | {power} | {power_pct:.1f}% | Usage régulier |
| Super | {super_users} | {super_pct:.1f}% | Usage intensif |

## ÉCONOMIES POTENTIELLES
- Total annuel : {savings:,.0f}€
- Pourcentage du budget : {savings_pct:.1f}%

---
Génère un rapport structuré avec :

1. **EXECUTIVE SUMMARY** (1 page)
2. **QUICK WINS** (actions <30 jours)
3. **PLAN D'ACTION DÉTAILLÉ** (phases 1-3)
4. **ANALYSE DES RISQUES**
5. **CALCUL ROI**

Format : Markdown structuré.
"""
    
    async def generate(self, result: ClassificationResult) -> str:
        client = AsyncOpenAI()
        
        prompt = self.USER_PROMPT_TEMPLATE.format(
            company_name=result.company_name,
            budget_actuel=result.current_annual_cost,
            total_users=result.total_users,
            cout_moyen=result.avg_monthly_cost,
            zombies=result.by_category['zombie'],
            zombies_pct=result.by_category['zombie']/result.total_users*100,
            casual=result.by_category['casual'],
            casual_pct=result.by_category['casual']/result.total_users*100,
            power=result.by_category['power'],
            power_pct=result.by_category['power']/result.total_users*100,
            super_users=result.by_category['super'],
            super_pct=result.by_category['super']/result.total_users*100,
            savings=result.total_annual_savings,
            savings_pct=result.total_annual_savings/result.current_annual_cost*100
        )
        
        response = await client.chat.completions.create(
            model='gpt-4-turbo-preview',
            messages=[
                {'role': 'system', 'content': self.SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        return response.choices[0].message.content
```

---

## 🔒 Monitoring Sécurité 24/7

### Permissions Critiques Surveillées

| Permission | Risque | Alerte | Action |
|------------|--------|--------|--------|
| `ModifyAllData` | Critique | User non-admin | Révocation immédiate |
| `ViewAllData` | Élevé | User inactif 30+ jours | Review obligatoire |
| `ManageUsers` | Critique | Nouveau user | Validation manager |
| `ExportReports` | Moyen | Stagiaire avec export | Alerte RSSI |
| `ApiEnabled` | Moyen | User non-tech | Vérification usage |

### Implémentation Observer

```python
# services/permission_monitor.py
from dataclasses import dataclass, asdict
from datetime import datetime
from events.event_bus import EventBus, Event

@dataclass
class SecurityAlert:
    type: str  # 'critical', 'high', 'medium', 'low'
    permission: str
    user_id: str
    user_name: str
    description: str
    detected_at: datetime
    recommended_action: str

class PermissionMonitor:
    """Surveille les permissions critiques et émet des alertes"""
    
    CRITICAL_PERMISSIONS = [
        'ModifyAllData', 'ViewAllData', 'ManageUsers',
        'ManageInternalUsers', 'AssignPermissionSets',
        'ManageProfilesPermissionsets', 'ResetPasswords'
    ]
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    
    async def check_anomalies(self, permissions: List[PermissionAssignment]):
        """Détecte les anomalies de permissions"""
        for perm in permissions:
            # Règle 1: Permission critique sur user non-admin
            if perm.name in self.CRITICAL_PERMISSIONS and not perm.user.is_admin:
                await self._emit_alert(SecurityAlert(
                    type='critical',
                    permission=perm.name,
                    user_id=perm.user.id,
                    user_name=perm.user.username,
                    description=f'Permission {perm.name} sur user non-admin',
                    detected_at=datetime.utcnow(),
                    recommended_action='Révoquer immédiatement'
                ))
    
    async def _emit_alert(self, alert: SecurityAlert):
        await self.event_bus.publish(Event(
            type='security_alert',
            payload=asdict(alert)
        ))
```

---

## 🌐 API Endpoints

### Routes Principales

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/v1/orgs/{org_id}/analyze` | Lance analyse complète |
| `GET` | `/api/v1/orgs/{org_id}/classification` | Classification actuelle |
| `GET` | `/api/v1/orgs/{org_id}/recommendations` | Liste recommandations |
| `POST` | `/api/v1/orgs/{org_id}/generate-plan` | Génère plan GPT-4 |
| `GET` | `/api/v1/orgs/{org_id}/report/pdf` | Télécharge PDF |
| `GET` | `/api/v1/orgs/{org_id}/savings` | Tracking économies |
| `GET` | `/api/v1/orgs/{org_id}/alerts` | Alertes sécurité |

### Implémentation FastAPI

```python
# main.py
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI(
    title='Salesforce License Optimizer',
    description='Optimisation financière automatique des licences Salesforce',
    version='1.0.0'
)

class ClassificationResponse(BaseModel):
    total_users: int
    zombies: int
    casual: int
    power: int
    super_users: int
    current_monthly_cost: float
    current_annual_cost: float
    potential_monthly_savings: float
    potential_annual_savings: float
    savings_percentage: float

@app.post('/api/v1/orgs/{org_id}/analyze')
async def analyze_org(
    org_id: str,
    collection_svc: CollectionService = Depends(get_collection_service),
    classification_svc: ClassificationService = Depends(get_classification_service)
) -> ClassificationResponse:
    """Lance l'analyse complète d'une org Salesforce"""
    collection = await collection_svc.collect_all(org_id=org_id, days=90)
    result = await classification_svc.classify_users(collection.metrics)
    return ClassificationResponse.from_result(result)
```

---

## 💾 Modèle de Données

### Schéma PostgreSQL

```sql
-- Tenants (clients)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    sf_org_id VARCHAR(18) UNIQUE,
    sf_instance_url VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users Salesforce analysés
CREATE TABLE sf_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    sf_user_id VARCHAR(18) NOT NULL,
    username VARCHAR(255),
    license_type VARCHAR(100),
    profile_name VARCHAR(255),
    last_login_date TIMESTAMPTZ,
    UNIQUE(tenant_id, sf_user_id)
);

-- Métriques d'utilisation
CREATE TABLE usage_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sf_user_id UUID REFERENCES sf_users(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    login_count INTEGER DEFAULT 0,
    features_used TEXT[],
    records_created INTEGER DEFAULT 0,
    records_modified INTEGER DEFAULT 0,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    category VARCHAR(20),
    UNIQUE(sf_user_id, period_start)
);

-- Recommandations générées
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    sf_user_id UUID REFERENCES sf_users(id),
    current_license VARCHAR(100),
    recommended_license VARCHAR(100),
    action VARCHAR(20),  -- 'deactivate', 'downgrade', 'keep', 'upgrade'
    monthly_savings DECIMAL(10,2),
    annual_savings DECIMAL(10,2),
    risk_level VARCHAR(10),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alertes sécurité
CREATE TABLE security_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    alert_type VARCHAR(20),
    permission VARCHAR(100),
    user_id UUID REFERENCES sf_users(id),
    description TEXT,
    recommended_action TEXT,
    status VARCHAR(20) DEFAULT 'open',
    detected_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tracking économies (facturation)
CREATE TABLE savings_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    month DATE NOT NULL,
    baseline_cost DECIMAL(12,2),
    current_cost DECIMAL(12,2),
    savings DECIMAL(12,2),
    commission_rate DECIMAL(4,2) DEFAULT 0.30,
    commission_amount DECIMAL(12,2),
    UNIQUE(tenant_id, month)
);
```

---

## ⚙️ Configuration

### Variables d'Environnement

```bash
# .env.example

# Application
APP_NAME=salesforce-license-optimizer
APP_ENV=development  # development | staging | production
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/license_optimizer
DATABASE_POOL_SIZE=10

# Redis
REDIS_URL=redis://localhost:6379/0

# Salesforce OAuth
SF_CLIENT_ID=your_connected_app_client_id
SF_CLIENT_SECRET=your_connected_app_client_secret
SF_REDIRECT_URI=http://localhost:8000/oauth/callback

# OpenAI
OPENAI_API_KEY=sk-...

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=notifications@example.com
SMTP_PASSWORD=...

# Security
SECRET_KEY=your-secret-key-for-jwt
CORS_ORIGINS=["http://localhost:3000"]
```

### Config Pydantic

```python
# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "salesforce-license-optimizer"
    app_env: str = "development"
    debug: bool = False
    
    # Database
    database_url: str
    database_pool_size: int = 10
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Salesforce
    sf_client_id: str
    sf_client_secret: str
    sf_redirect_uri: str
    
    # OpenAI
    openai_api_key: str
    
    # Security
    secret_key: str
    cors_origins: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## 📚 Références

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [simple-salesforce](https://github.com/simple-salesforce/simple-salesforce)
- [Salesforce REST API](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Pydantic v2](https://docs.pydantic.dev/latest/)

---

> **Last updated:** 29 décembre 2025  
> **Version:** 3.0
