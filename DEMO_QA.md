# Guide QA Test - Salesforce License Optimizer

## 🎯 Objectif QA

Ce document fournit un guide complet pour l'équipe QA afin de **valider toutes les fonctionnalités** de l'application, vérifier **l'intégrité des données** dans les bases de données, et identifier les **bugs ou problèmes de performance**.

**Durée Estimée**: 4-6 heures (test complet)  
**Prérequis**: Accès aux containers Docker, PostgreSQL, Redis

---

## 📋 Préparation Environnement QA

### **1. Démarrage des Services**

```bash
# Naviguer vers le projet
cd C:\Users\Selim Mahjoub\Documents\Uprizon\AXIOMCORE\SalesforceLicenseOptimizer

# Nettoyer les containers existants (si nécessaire)
docker-compose down -v

# Construire et démarrer tous les services
docker-compose up -d --build

# Attendre que tous les services soient healthy (60 secondes)
timeout 60

# Vérifier le statut des containers
docker-compose ps
```

**Résultat Attendu:**
```
NAME              STATUS         PORTS
slo-postgres      Up (healthy)   0.0.0.0:5432->5432/tcp
slo-redis         Up (healthy)   0.0.0.0:6379->6379/tcp
slo-backend       Up (healthy)   0.0.0.0:8000->8000/tcp
```

### **2. Vérification des Services**

```bash
# Test Backend Health
curl http://localhost:8000/health

# Résultat Attendu:
# {
#   "status": "healthy",
#   "timestamp": "2026-02-10T...",
#   "app_name": "salesforce-license-optimizer",
#   "version": "1.0.0",
#   "environment": "development"
# }

# Test Frontend (ouvrir dans navigateur)
# http://localhost:3000
# ✅ Doit afficher le Dashboard sans erreurs
```

### **3. Connexion aux Bases de Données**

#### **PostgreSQL:**

```bash
# Option 1: Via Docker
docker exec -it slo-postgres psql -U slo_user -d license_optimizer

# Option 2: Via client local (DBeaver, pgAdmin, psql)
# Host: localhost
# Port: 5432
# Database: license_optimizer
# User: slo_user
# Password: slo_password
```

#### **Redis:**

```bash
# Via Docker
docker exec -it slo-redis redis-cli

# Test connexion
> PING
# Résultat Attendu: PONG

# Voir toutes les clés
> KEYS *
```

---

## 🧪 TESTS FONCTIONNELS

### **TEST 1: Health Check & Configuration**

#### **1.1 Health Endpoint**

**Objectif:** Vérifier que l'API backend est opérationnelle

**Procédure:**
```bash
curl -X GET http://localhost:8000/health
```

**Résultat Attendu:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-10T14:30:00.000Z",
  "app_name": "salesforce-license-optimizer",
  "version": "1.0.0",
  "environment": "development"
}
```

**Vérifications:**
- [ ] Status = "healthy"
- [ ] Timestamp est récent (<5 secondes)
- [ ] Version = "1.0.0"
- [ ] Environment = "development"

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **1.2 Root Endpoint**

**Objectif:** Vérifier les informations de base de l'API

**Procédure:**
```bash
curl -X GET http://localhost:8000/
```

**Résultat Attendu:**
```json
{
  "message": "Salesforce License Optimizer API",
  "version": "1.0.0",
  "docs_url": "/docs",
  "health_check": "/health",
  "api_v1": "/api/v1"
}
```

**Vérifications:**
- [ ] Message présent
- [ ] Links fonctionnels (/docs, /health)
- [ ] API v1 référencée

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **1.3 API Documentation (Swagger)**

**Objectif:** Vérifier que la documentation interactive est accessible

**Procédure:**
1. Ouvrir http://localhost:8000/docs dans un navigateur
2. Vérifier que Swagger UI se charge
3. Vérifier que tous les endpoints sont listés

**Résultat Attendu:**
- Swagger UI s'affiche correctement
- Sections visibles: Auth, Users, Recommendations, Analytics
- Chaque endpoint a une description

**Vérifications:**
- [ ] Page Swagger accessible
- [ ] Endpoints /api/v1/auth/* visibles
- [ ] Endpoints /api/v1/users/* visibles
- [ ] Endpoints /api/v1/recommendations/* visibles
- [ ] Endpoints /api/v1/analytics/* visibles
- [ ] Schémas de modèles visibles

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

### **TEST 2: Authentication & OAuth**

#### **2.1 Authorization URL Generation**

**Objectif:** Vérifier la génération de l'URL OAuth Salesforce

**Procédure:**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/authorize?state=test123"
```

**Résultat Attendu:**
```json
{
  "authorization_url": "https://login.salesforce.com/services/oauth2/authorize?response_type=code&client_id=...&redirect_uri=...&scope=api%20refresh_token&state=test123"
}
```

**Vérifications:**
- [ ] URL contient "login.salesforce.com"
- [ ] Parameter state présent
- [ ] Parameter redirect_uri présent
- [ ] Parameter scope inclut "api refresh_token"

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **2.2 OAuth Callback (Mock)**

**Objectif:** Tester le callback OAuth (avec mock data en l'absence de Salesforce réel)

**Note:** Ce test nécessite un vrai code OAuth de Salesforce. En QA, tester la structure de l'endpoint.

**Procédure:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/callback" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "test_invalid_code",
    "org_id": "test_org_123"
  }'
```

**Résultat Attendu:**
- Code 400 (car code invalide)
- Message d'erreur clair

**Vérifications:**
- [ ] Endpoint accepte POST
- [ ] Validation des paramètres fonctionne
- [ ] Error messages clairs

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

### **TEST 3: User Management**

#### **3.1 User Collection Endpoint**

**Objectif:** Vérifier l'endpoint de collection des users

**Procédure:**
```bash
curl -X GET "http://localhost:8000/api/v1/users/collect/demo_org?days=90"
```

**Résultat Attendu:**
```json
{
  "success": false,
  "error": "No tokens found for org demo_org"
}
```
(Normal car pas d'OAuth configuré)

**Vérifications:**
- [ ] Endpoint répond
- [ ] Validation du parameter days
- [ ] Error handling approprié

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **3.2 User Listing Endpoint**

**Objectif:** Vérifier le listing des utilisateurs (mock data)

**Procédure:**
```bash
curl -X GET "http://localhost:8000/api/v1/users/list/demo_org"
```

**Résultat Attendu:**
```json
{
  "users": [
    {
      "id": "005xx000001X8F3AAK",
      "username": "john.doe@company.com",
      "email": "john.doe@company.com",
      "license_type": "Sales Cloud",
      "activity_score": 85,
      "category": "EFFICIENT",
      "last_login_date": "2024-02-08T10:30:00Z"
    }
  ],
  "total": 1
}
```

**Vérifications:**
- [ ] Response contient array "users"
- [ ] Chaque user a tous les champs requis
- [ ] Total count présent
- [ ] Score entre 0-100
- [ ] Category valide (INACTIVE, UNDERUTILIZED, OPTIMIZABLE, EFFICIENT)

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

### **TEST 4: Recommendations**

#### **4.1 Recommendations Listing**

**Objectif:** Vérifier le listing des recommandations

**Procédure:**
```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/list/demo_org"
```

**Résultat Attendu:**
```json
{
  "recommendations": [
    {
      "user_id": "005xx000001X8F3AAK",
      "username": "john.doe@company.com",
      "type": "KEEP",
      "priority": "LOW",
      "title": "Utilisation optimale - Conserver la licence",
      "monthly_savings": 0.0,
      "annual_savings": 0.0
    }
  ],
  "total": 1
}
```

**Vérifications:**
- [ ] Array "recommendations" présent
- [ ] Type valide (DEACTIVATE, DOWNGRADE, UPGRADE, OPTIMIZE, KEEP, etc.)
- [ ] Priority valide (CRITICAL, HIGH, MEDIUM, LOW)
- [ ] Savings sont des nombres
- [ ] Title descriptif

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **4.2 Action Plan Generation**

**Objectif:** Vérifier la génération de plan d'action

**Procédure:**
```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/plan/demo_org"
```

**Résultat Attendu:**
```json
{
  "success": true,
  "message": "Action plan generated",
  "plan": {
    "title": "Plan d'optimisation des licences Salesforce",
    "executive_summary": "...",
    "steps": []
  }
}
```

**Vérifications:**
- [ ] Success = true
- [ ] Plan contient title
- [ ] Plan contient executive_summary
- [ ] Plan contient steps array

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

### **TEST 5: Analytics & ROI**

#### **5.1 Analytics Dashboard**

**Objectif:** Vérifier les métriques du dashboard analytics

**Procédure:**
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/dashboard/demo_org"
```

**Résultat Attendu:**
```json
{
  "mrr": 12500.00,
  "ltv": 450000.00,
  "total_monthly_savings": 12500.00,
  "total_annual_savings": 150000.00,
  "optimization_rate": 28.5,
  "roi_percentage": 487.3,
  "payback_period_months": 0.5,
  "categories": {
    "EFFICIENT": 42,
    "OPTIMIZABLE": 35,
    "UNDERUTILIZED": 28,
    "INACTIVE": 45
  },
  "monthly_trend": [
    {"month": "Jan", "savings": 8500},
    {"month": "Feb", "savings": 12500}
  ]
}
```

**Vérifications:**
- [ ] MRR est un nombre positif
- [ ] LTV est un nombre positif
- [ ] Savings annuels = savings mensuels × 12
- [ ] ROI percentage raisonnable (>0)
- [ ] Payback period raisonnable (<24 mois)
- [ ] Categories sum = total users
- [ ] Monthly trend contient au moins 1 entrée

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **5.2 ROI Metrics**

**Objectif:** Vérifier le calcul des métriques ROI

**Procédure:**
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/roi/demo_org"
```

**Résultat Attendu:**
```json
{
  "baseline_cost": 43750.00,
  "current_cost": 31250.00,
  "monthly_savings": 12500.00,
  "annual_savings": 150000.00,
  "roi_percentage": 487.3,
  "payback_period_months": 0.5
}
```

**Vérifications:**
- [ ] Baseline > Current (si optimisé)
- [ ] Monthly savings = Baseline - Current
- [ ] Annual savings = Monthly × 12
- [ ] ROI calculation correcte
- [ ] Tous les champs sont des nombres

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **5.3 Savings Report**

**Objectif:** Vérifier le rapport détaillé des économies

**Procédure:**
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/savings-report/demo_org"
```

**Résultat Attendu:**
```json
{
  "period": "2024-02",
  "baseline": {
    "licenses": 150,
    "monthly_cost": 43750.00,
    "annual_cost": 525000.00
  },
  "current": {
    "licenses": 108,
    "monthly_cost": 31250.00,
    "annual_cost": 375000.00
  },
  "optimizations": {
    "licenses_optimized": 42,
    "optimization_rate": 28.0
  },
  "savings": {
    "monthly": 12500.00,
    "annual": 150000.00,
    "cumulative": 25000.00
  }
}
```

**Vérifications:**
- [ ] Baseline licenses >= Current licenses
- [ ] Annual cost = Monthly × 12
- [ ] Licenses optimized = Baseline - Current
- [ ] Optimization rate = (Optimized / Baseline) × 100
- [ ] Savings cohérents

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

### **TEST 6: Frontend Interface**

#### **6.1 Dashboard Loading**

**Objectif:** Vérifier le chargement du dashboard React

**Procédure:**
1. Ouvrir http://localhost:3000 dans le navigateur
2. Ouvrir DevTools (F12)
3. Vérifier la console (aucune erreur)
4. Vérifier Network tab (requêtes API)

**Résultat Attendu:**
- Dashboard s'affiche en <2 secondes
- Aucune erreur console
- 4 stat cards visibles
- Sidebar présente
- Header présent

**Vérifications:**
- [ ] Page charge sans erreur
- [ ] Stat cards affichent des valeurs
- [ ] Sidebar menu fonctionne
- [ ] Navigation entre pages fonctionne
- [ ] Pas d'erreur 404 sur assets

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **6.2 User Table Display**

**Objectif:** Vérifier l'affichage du tableau des utilisateurs

**Procédure:**
1. Sur le Dashboard, scroller vers le bas
2. Vérifier le tableau "Utilisateurs récents"
3. Cliquer sur les headers de colonnes (tri)

**Résultat Attendu:**
- Tableau avec au moins 1 utilisateur
- Colonnes: Utilisateur, Licence, Score, Catégorie, Dernière connexion
- Badges colorés pour catégories
- Données formatées correctement

**Vérifications:**
- [ ] Tableau visible
- [ ] Au moins 1 ligne de données
- [ ] Score affiché en format "XX/100"
- [ ] Badge catégorie coloré (vert/bleu/jaune/rouge)
- [ ] Date formatée en français
- [ ] Email cliquable (si applicable)

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **6.3 Responsive Design**

**Objectif:** Vérifier la responsivité sur différents écrans

**Procédure:**
1. DevTools → Device Toolbar (Ctrl+Shift+M)
2. Tester sur:
   - Mobile (375px)
   - Tablet (768px)
   - Desktop (1920px)

**Vérifications:**
- [ ] Layout s'adapte sur mobile
- [ ] Sidebar collapse sur mobile
- [ ] Stats cards en colonne sur mobile
- [ ] Tableau scrollable horizontalement
- [ ] Pas de débordement horizontal
- [ ] Texte lisible sur tous écrans

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **6.4 Navigation**

**Objectif:** Tester la navigation entre pages

**Procédure:**
1. Cliquer sur "Dashboard" (sidebar)
2. Cliquer sur "Utilisateurs"
3. Cliquer sur "Recommandations"
4. Cliquer sur "Analytics"
5. Utiliser bouton back du navigateur

**Vérifications:**
- [ ] Dashboard charge correctement
- [ ] Page Users affiche "Users Page (Coming soon)"
- [ ] Page Recommendations affiche message
- [ ] Page Analytics affiche message
- [ ] Back button fonctionne
- [ ] URL change correctement (/dashboard, /users, etc.)
- [ ] Pas d'erreur console lors navigation

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

## 🗄️ TESTS BASE DE DONNÉES

### **TEST 7: PostgreSQL Schema**

#### **7.1 Vérification des Tables**

**Objectif:** Vérifier que toutes les tables sont créées

**Procédure:**
```sql
-- Se connecter à PostgreSQL
docker exec -it slo-postgres psql -U slo_user -d license_optimizer

-- Lister toutes les tables
\dt

-- Résultat Attendu:
-- tenants
-- sf_users
-- usage_metrics
-- recommendations
-- security_alerts
-- savings_tracking
```

**Vérifications:**
- [ ] Table "tenants" existe
- [ ] Table "sf_users" existe
- [ ] Table "usage_metrics" existe
- [ ] Table "recommendations" existe
- [ ] Table "security_alerts" existe
- [ ] Table "savings_tracking" existe

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **7.2 Structure Table "tenants"**

**Objectif:** Vérifier la structure de la table tenants

**Procédure:**
```sql
-- Décrire la table
\d tenants

-- Vérifier les colonnes
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'tenants';
```

**Résultat Attendu:**
```
Column Name          | Type                  | Nullable
---------------------|-----------------------|---------
id                   | uuid                  | NO
org_id               | varchar(255)          | NO
org_name             | varchar(255)          | NO
salesforce_instance  | varchar(255)          | YES
is_active            | boolean               | NO
created_at           | timestamp             | NO
updated_at           | timestamp             | NO
```

**Vérifications:**
- [ ] Colonne "id" est UUID et NOT NULL
- [ ] Colonne "org_id" est VARCHAR et NOT NULL
- [ ] Colonne "is_active" est BOOLEAN avec default TRUE
- [ ] Timestamps (created_at, updated_at) présents
- [ ] Primary Key sur "id"
- [ ] Unique constraint sur "org_id"

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **7.3 Structure Table "sf_users"**

**Objectif:** Vérifier la structure de la table sf_users

**Procédure:**
```sql
\d sf_users

SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'sf_users';
```

**Résultat Attendu:**
```
Column Name          | Type                  | Nullable
---------------------|-----------------------|---------
id                   | uuid                  | NO
tenant_id            | uuid                  | NO
sf_user_id           | varchar(18)           | NO
username             | varchar(255)          | NO
email                | varchar(255)          | YES
full_name            | varchar(255)          | YES
is_active            | boolean               | NO
license_type         | varchar(100)          | YES
profile_name         | varchar(255)          | YES
last_login_date      | date                  | YES
created_date         | date                  | YES
activity_score       | integer               | YES
category             | varchar(50)           | YES
last_sync_at         | timestamp             | YES
created_at           | timestamp             | NO
updated_at           | timestamp             | NO
```

**Vérifications:**
- [ ] Foreign key vers "tenants(id)"
- [ ] Index sur "tenant_id"
- [ ] Index sur "sf_user_id"
- [ ] Index sur "activity_score"
- [ ] Index sur "category"
- [ ] Unique constraint sur (tenant_id, sf_user_id)

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **7.4 Structure Table "usage_metrics"**

**Objectif:** Vérifier la structure de la table usage_metrics

**Procédure:**
```sql
\d usage_metrics

-- Vérifier les indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'usage_metrics';
```

**Résultat Attendu:**
```
Column Name          | Type                  | Nullable
---------------------|-----------------------|---------
id                   | uuid                  | NO
user_id              | uuid                  | NO
period_start         | date                  | NO
period_end           | date                  | NO
login_count          | integer               | NO
features_used        | jsonb                 | YES
records_created      | integer               | NO
records_modified     | integer               | NO
calculated_at        | timestamp             | NO
created_at           | timestamp             | NO
```

**Vérifications:**
- [ ] Foreign key vers "sf_users(id)"
- [ ] Index sur "user_id"
- [ ] Index sur "period_start"
- [ ] Check constraint: login_count >= 0
- [ ] Check constraint: records_created >= 0
- [ ] JSONB pour "features_used"

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **7.5 Relations & Foreign Keys**

**Objectif:** Vérifier toutes les relations entre tables

**Procédure:**
```sql
-- Lister toutes les foreign keys
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

**Résultat Attendu:**
- sf_users.tenant_id → tenants.id
- usage_metrics.user_id → sf_users.id
- recommendations.user_id → sf_users.id
- security_alerts.user_id → sf_users.id (nullable)
- security_alerts.tenant_id → tenants.id
- savings_tracking.tenant_id → tenants.id

**Vérifications:**
- [ ] 6+ foreign keys définies
- [ ] ON DELETE CASCADE approprié
- [ ] ON UPDATE CASCADE approprié
- [ ] Aucune relation cassée

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **7.6 Indexes Performance**

**Objectif:** Vérifier que les indexes critiques existent

**Procédure:**
```sql
-- Lister tous les indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

**Vérifications:**
- [ ] Index sur tenants(org_id)
- [ ] Index sur sf_users(tenant_id)
- [ ] Index sur sf_users(sf_user_id)
- [ ] Index sur sf_users(activity_score)
- [ ] Index sur sf_users(category)
- [ ] Index sur usage_metrics(user_id)
- [ ] Index sur recommendations(user_id, priority)
- [ ] Index sur security_alerts(severity, detected_at)

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

### **TEST 8: Data Integrity**

#### **8.1 Insertion Test Data**

**Objectif:** Tester l'insertion de données et contraintes

**Procédure:**
```sql
-- Insérer un tenant de test
INSERT INTO tenants (id, org_id, org_name, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'TEST_ORG_001',
    'Test Organization',
    true,
    NOW(),
    NOW()
)
RETURNING id;

-- Noter l'ID retourné pour les prochains tests
-- Supposons: tenant_id = 'abc-123-def'

-- Insérer un utilisateur de test
INSERT INTO sf_users (
    id, tenant_id, sf_user_id, username, email, full_name,
    is_active, license_type, profile_name,
    activity_score, category, created_at, updated_at
)
VALUES (
    gen_random_uuid(),
    'abc-123-def', -- Remplacer par le tenant_id réel
    '005xx000001TEST',
    'test.user@qatest.com',
    'test.user@qatest.com',
    'Test QA User',
    true,
    'Sales Cloud',
    'Standard User',
    75,
    'OPTIMIZABLE',
    NOW(),
    NOW()
)
RETURNING id;

-- Vérifier l'insertion
SELECT * FROM sf_users WHERE username = 'test.user@qatest.com';
```

**Vérifications:**
- [ ] Insertion tenant réussie
- [ ] Insertion user réussie
- [ ] Timestamps auto-populés
- [ ] UUIDs générés automatiquement
- [ ] Données récupérables avec SELECT

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **8.2 Constraint Violation Tests**

**Objectif:** Vérifier que les contraintes sont appliquées

**Procédure:**
```sql
-- Test 1: Duplicate org_id (doit échouer)
INSERT INTO tenants (id, org_id, org_name, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'TEST_ORG_001', -- Duplicate
    'Another Org',
    true,
    NOW(),
    NOW()
);
-- Résultat Attendu: ERROR unique constraint violation

-- Test 2: NULL dans colonne NOT NULL (doit échouer)
INSERT INTO sf_users (
    id, tenant_id, sf_user_id, username,
    is_active, created_at, updated_at
)
VALUES (
    gen_random_uuid(),
    NULL, -- NOT NULL violation
    '005xx000002TEST',
    'another.user@test.com',
    true,
    NOW(),
    NOW()
);
-- Résultat Attendu: ERROR not-null constraint violation

-- Test 3: Foreign key invalid (doit échouer)
INSERT INTO sf_users (
    id, tenant_id, sf_user_id, username,
    is_active, created_at, updated_at
)
VALUES (
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000000', -- ID inexistant
    '005xx000003TEST',
    'fk.test@test.com',
    true,
    NOW(),
    NOW()
);
-- Résultat Attendu: ERROR foreign key constraint violation
```

**Vérifications:**
- [ ] Unique constraints fonctionnent
- [ ] NOT NULL constraints fonctionnent
- [ ] Foreign key constraints fonctionnent
- [ ] Check constraints fonctionnent (si applicable)
- [ ] Messages d'erreur clairs

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **8.3 Cascade Delete Test**

**Objectif:** Vérifier le comportement ON DELETE CASCADE

**Procédure:**
```sql
-- Récupérer l'ID du tenant de test
SELECT id FROM tenants WHERE org_id = 'TEST_ORG_001';

-- Compter les users de ce tenant
SELECT COUNT(*) FROM sf_users WHERE tenant_id = 'abc-123-def';

-- Supprimer le tenant
DELETE FROM tenants WHERE org_id = 'TEST_ORG_001';

-- Vérifier que les users associés sont supprimés
SELECT COUNT(*) FROM sf_users WHERE tenant_id = 'abc-123-def';
-- Résultat Attendu: 0

-- Vérifier que le tenant n'existe plus
SELECT COUNT(*) FROM tenants WHERE org_id = 'TEST_ORG_001';
-- Résultat Attendu: 0
```

**Vérifications:**
- [ ] Deletion du tenant réussie
- [ ] Users associés supprimés (CASCADE)
- [ ] Metrics associés supprimés (CASCADE)
- [ ] Recommendations associées supprimées (CASCADE)
- [ ] Pas d'orphan records

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

### **TEST 9: Redis Cache**

#### **9.1 Redis Connection**

**Objectif:** Vérifier la connexion Redis

**Procédure:**
```bash
docker exec -it slo-redis redis-cli

# Dans redis-cli:
> PING
# Résultat Attendu: PONG

> INFO server
# Vérifier la version Redis 7.x

> CONFIG GET maxmemory
# Vérifier la config mémoire
```

**Vérifications:**
- [ ] PING retourne PONG
- [ ] Version Redis 7.x
- [ ] Maxmemory configurée
- [ ] Pas d'erreurs dans les logs

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **9.2 Cache Operations**

**Objectif:** Tester les opérations CRUD sur Redis

**Procédure:**
```bash
# Dans redis-cli:

# SET operation
> SET test_key "test_value"
# Résultat: OK

# GET operation
> GET test_key
# Résultat: "test_value"

# SET with expiry (TTL)
> SETEX test_ttl 60 "expires_in_60s"
> TTL test_ttl
# Résultat: ~60

# DELETE operation
> DEL test_key
# Résultat: (integer) 1

# Vérifier suppression
> GET test_key
# Résultat: (nil)

# Hash operations (pour sessions)
> HSET session:user123 username "john.doe"
> HSET session:user123 email "john@test.com"
> HGETALL session:user123
# Résultat: username, john.doe, email, john@test.com

# Nettoyer
> DEL session:user123
```

**Vérifications:**
- [ ] SET fonctionne
- [ ] GET fonctionne
- [ ] TTL fonctionne
- [ ] DEL fonctionne
- [ ] Hash operations fonctionnent
- [ ] Expiration automatique fonctionne

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **9.3 Cache Performance**

**Objectif:** Mesurer les performances du cache

**Procédure:**
```bash
# Dans redis-cli:

# Test écriture de 1000 keys
> DEBUG POPULATE 1000
# Mesurer le temps

# Vérifier le nombre de keys
> DBSIZE
# Résultat: (integer) ~1000+

# Test lecture
> MGET key:1 key:2 key:3 key:4 key:5
# Mesurer le temps de réponse

# Flush tout
> FLUSHDB
```

**Vérifications:**
- [ ] Écriture de 1000 keys <1 seconde
- [ ] Lecture instantanée (<10ms)
- [ ] DBSIZE retourne le bon nombre
- [ ] FLUSHDB nettoie tout
- [ ] Pas de memory overflow

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

## 🔍 TESTS DE LOGIQUE MÉTIER

### **TEST 10: Scoring Algorithm**

#### **10.1 Score Calculation**

**Objectif:** Vérifier le calcul des scores d'activité

**Test Cases:**

**Case 1: Utilisateur INACTIF (Score attendu: 0-30)**
```python
# Données:
last_login = None (jamais connecté)
login_count_90d = 0
features_used = []
records_touched = 0

# Score Attendu:
last_login_score = 0 (0 pts)
frequency_score = 0 (0 pts)
features_score = 0 (0 pts)
records_score = 0 (0 pts)
TOTAL = 0 points → INACTIVE
```

**Case 2: Utilisateur SOUS-UTILISÉ (Score attendu: 31-55)**
```python
# Données:
last_login = 25 jours (récent)
login_count_90d = 15
features_used = [10 features sur 100]
records_touched = 20

# Score Attendu:
last_login_score = 30 pts (<30 jours)
frequency_score = 5 pts (15/90 = 0.16 × 7 ≈ 1.2/semaine → 5 pts)
features_score = 3 pts (10%)
records_score = 4 pts (20/5)
TOTAL = 42 points → UNDERUTILIZED
```

**Case 3: Utilisateur EFFICACE (Score attendu: 76-100)**
```python
# Données:
last_login = 1 jour
login_count_90d = 85
features_used = [75 features sur 100]
records_touched = 200

# Score Attendu:
last_login_score = 30 pts
frequency_score = 20 pts (85/90 = 6.6/semaine → 20 pts max)
features_score = 22 pts (75% × 30)
records_score = 20 pts (200/5 = 40, cap à 20)
TOTAL = 92 points → EFFICIENT
```

**Procédure de Test:**
1. Exécuter les tests unitaires
```bash
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_scoring.py -v
```

2. Vérifier les résultats

**Vérifications:**
- [ ] Test case INACTIVE passe
- [ ] Test case UNDERUTILIZED passe
- [ ] Test case EFFICIENT passe
- [ ] Score toujours entre 0-100
- [ ] Aucun score négatif
- [ ] Breakdown détaillé disponible

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

### **TEST 11: Recommendation Engine**

#### **11.1 Recommendation Generation**

**Objectif:** Vérifier que les recommandations sont correctes

**Test Cases:**

**Case 1: Utilisateur Jamais Connecté**
```
Input:
- last_login = None
- license_type = "Sales Cloud" ($150/mois)
- activity_score = 0

Expected Output:
- Type: DEACTIVATE
- Priority: CRITICAL
- Monthly Savings: $150
- Title: "Utilisateur jamais connecté - Désactivation immédiate"
```

**Case 2: Utilisateur Inactif >90 jours**
```
Input:
- last_login = 95 jours
- license_type = "Platform" ($75/mois)
- activity_score = 20

Expected Output:
- Type: DOWNGRADE
- Priority: HIGH
- Monthly Savings: $67.50 (90% de $75)
- Title: "Inactif depuis 95 jours"
```

**Case 3: Utilisateur Efficace**
```
Input:
- last_login = 2 jours
- license_type = "Sales Cloud" ($150/mois)
- activity_score = 88

Expected Output:
- Type: KEEP
- Priority: LOW
- Monthly Savings: $0
- Title: "Utilisation optimale - Conserver la licence"
```

**Procédure:**
```bash
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_recommendation_factory.py -v
```

**Vérifications:**
- [ ] Règle "jamais connecté" fonctionne
- [ ] Règle "inactif >90j" fonctionne
- [ ] Règle "utilisateur efficace" fonctionne
- [ ] Priorités correctes (CRITICAL > HIGH > MEDIUM > LOW)
- [ ] Savings calculés correctement
- [ ] Justifications présentes

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **11.2 Recommendation Sorting**

**Objectif:** Vérifier le tri des recommandations

**Procédure:**
```bash
# Exécuter test de tri
.\venv\Scripts\python.exe -m pytest tests/test_recommendation_factory.py::TestRecommendationFactory::test_recommendation_sorting -v
```

**Expected Behavior:**
Recommandations triées par:
1. Priority (CRITICAL → HIGH → MEDIUM → LOW)
2. Expected Savings (descendant)

**Exemple:**
```
Ordre attendu:
1. CRITICAL, $150/mois
2. CRITICAL, $100/mois
3. HIGH, $75/mois
4. HIGH, $50/mois
5. MEDIUM, $30/mois
6. LOW, $0/mois
```

**Vérifications:**
- [ ] Tri par priorité correct
- [ ] Tri par savings correct (à priorité égale)
- [ ] Ordre stable
- [ ] Aucune recommandation perdue

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

### **TEST 12: ROI Calculation**

#### **12.1 ROI Formula Validation**

**Objectif:** Vérifier la formule de calcul ROI

**Formula:**
```
ROI % = ((Annual Savings - Implementation Cost) / Implementation Cost) × 100

Payback Period (months) = Implementation Cost / Monthly Savings
```

**Test Case:**
```
Input:
- Baseline Cost: $43,750/mois
- Current Cost: $31,250/mois
- Monthly Savings: $12,500
- Annual Savings: $150,000
- Implementation Cost: $30,000

Expected Output:
- ROI: ((150,000 - 30,000) / 30,000) × 100 = 400%
- Payback: 30,000 / 12,500 = 2.4 mois
```

**Procédure:**
Vérifier manuellement ou via API:
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/roi/demo_org"
```

**Vérifications:**
- [ ] Formula correcte
- [ ] ROI > 0 pour économies positives
- [ ] Payback < 24 mois (raisonnable)
- [ ] Pas de division par zéro
- [ ] Gestion des cas edge (cost = 0, etc.)

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

## ⚡ TESTS DE PERFORMANCE

### **TEST 13: API Response Times**

#### **13.1 Latency Measurement**

**Objectif:** Mesurer les temps de réponse des endpoints

**Tool:** `curl` avec timing

**Procédure:**
```bash
# Test Health Endpoint (doit être <50ms)
curl -w "@curl-format.txt" -o NUL -s http://localhost:8000/health

# Créer curl-format.txt:
# time_namelookup:  %{time_namelookup}s\n
# time_connect:     %{time_connect}s\n
# time_total:       %{time_total}s\n

# Test Analytics Dashboard (doit être <500ms)
curl -w "@curl-format.txt" -o NUL -s http://localhost:8000/api/v1/analytics/dashboard/demo_org

# Test User List (doit être <300ms)
curl -w "@curl-format.txt" -o NUL -s http://localhost:8000/api/v1/users/list/demo_org
```

**Benchmarks:**
- Health: <50ms
- Analytics: <500ms
- User List: <300ms
- Recommendations: <400ms

**Vérifications:**
- [ ] Health <50ms
- [ ] Analytics <500ms
- [ ] User List <300ms
- [ ] Recommendations <400ms
- [ ] Pas de timeout

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **13.2 Load Testing**

**Objectif:** Tester la charge sur l'API

**Tool:** Apache Bench (ab) ou `wrk`

**Procédure:**
```bash
# Installer ab (si nécessaire)
# Windows: Download Apache binaries

# Test avec 100 requêtes, 10 concurrentes
ab -n 100 -c 10 http://localhost:8000/health

# Résultats à analyser:
# - Requests per second
# - Time per request
# - Failed requests (doit être 0)
```

**Benchmarks:**
- RPS (Requests/sec): >100
- Failed requests: 0%
- 95th percentile: <1000ms

**Vérifications:**
- [ ] RPS >100
- [ ] 0% failed
- [ ] P95 <1000ms
- [ ] Pas de crash
- [ ] Memory stable

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

### **TEST 14: Database Performance**

#### **14.1 Query Performance**

**Objectif:** Mesurer les performances des requêtes SQL

**Procédure:**
```sql
-- Activer le timing
\timing on

-- Test 1: Query simple (doit être <10ms)
SELECT COUNT(*) FROM tenants;

-- Test 2: Query avec JOIN (doit être <50ms)
SELECT 
    u.username,
    t.org_name,
    u.activity_score
FROM sf_users u
JOIN tenants t ON u.tenant_id = t.id
LIMIT 100;

-- Test 3: Query complexe avec agrégation (doit être <100ms)
SELECT 
    category,
    COUNT(*) as count,
    AVG(activity_score) as avg_score
FROM sf_users
WHERE tenant_id = (SELECT id FROM tenants LIMIT 1)
GROUP BY category;

-- Test 4: Index usage (doit utiliser index)
EXPLAIN ANALYZE
SELECT * FROM sf_users WHERE sf_user_id = '005xx000001TEST';
```

**Benchmarks:**
- Simple query: <10ms
- JOIN query: <50ms
- Aggregation: <100ms
- Index scan (pas seq scan)

**Vérifications:**
- [ ] Toutes queries <100ms
- [ ] EXPLAIN montre Index Scan
- [ ] Pas de Seq Scan sur grandes tables
- [ ] JOIN performant

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

## 🔐 TESTS DE SÉCURITÉ

### **TEST 15: Security Headers**

#### **15.1 CORS Configuration**

**Objectif:** Vérifier la configuration CORS

**Procédure:**
```bash
# Test CORS avec origin autorisé
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     -v http://localhost:8000/health

# Vérifier les headers de réponse:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE
# Access-Control-Allow-Headers: *
```

**Vérifications:**
- [ ] CORS headers présents
- [ ] Origin localhost:3000 autorisé
- [ ] Methods appropriés
- [ ] Credentials allowed

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

#### **15.2 Input Validation**

**Objectif:** Tester la validation des inputs

**Procédure:**
```bash
# Test 1: SQL Injection (doit être bloqué)
curl -X GET "http://localhost:8000/api/v1/users/list/'; DROP TABLE users; --"
# Résultat: Doit retourner erreur validation, pas crash

# Test 2: XSS (doit être escapé)
curl -X GET "http://localhost:8000/api/v1/users/list/<script>alert('xss')</script>"
# Résultat: Input sanitized

# Test 3: Path Traversal (doit être bloqué)
curl -X GET "http://localhost:8000/api/v1/users/list/../../../etc/passwd"
# Résultat: 404 ou erreur validation

# Test 4: Invalid parameters
curl -X GET "http://localhost:8000/api/v1/users/collect/demo?days=abc"
# Résultat: 422 Validation Error
```

**Vérifications:**
- [ ] SQL injection bloquée
- [ ] XSS sanitized
- [ ] Path traversal bloqué
- [ ] Parameter validation fonctionne
- [ ] Error messages sécurisés (pas de stack trace)

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

## 📝 TESTS D'INTÉGRATION

### **TEST 16: End-to-End Workflow**

#### **16.1 Full User Journey**

**Objectif:** Tester le workflow complet

**Scénario:**
1. OAuth authorization
2. Data collection
3. User classification
4. Recommendation generation
5. Action plan creation
6. Analytics retrieval

**Procédure:**
```bash
# Step 1: Get auth URL
AUTH_URL=$(curl -s http://localhost:8000/api/v1/auth/authorize | jq -r '.authorization_url')
echo "Authorization URL: $AUTH_URL"

# Step 2: (Manual) Complete OAuth in browser
# Step 3: Callback would provide token

# Step 4: Collect users (with valid token)
# curl -X GET "http://localhost:8000/api/v1/users/collect/demo_org"

# Step 5: Classify users
# curl -X POST "http://localhost:8000/api/v1/users/classify/demo_org"

# Step 6: Get recommendations
curl -X GET "http://localhost:8000/api/v1/recommendations/list/demo_org"

# Step 7: Generate action plan
curl -X POST "http://localhost:8000/api/v1/recommendations/plan/demo_org"

# Step 8: Get analytics
curl -X GET "http://localhost:8000/api/v1/analytics/dashboard/demo_org"

# Step 9: Get ROI
curl -X GET "http://localhost:8000/api/v1/analytics/roi/demo_org"
```

**Vérifications:**
- [ ] Chaque étape réussit
- [ ] Données cohérentes entre étapes
- [ ] Pas de perte de données
- [ ] Temps total <5 minutes
- [ ] Aucune erreur 500

**Status:** ⬜ PASS | ⬜ FAIL  
**Notes:** _________________

---

## 🐛 BUG TRACKING

### **Template de Bug Report**

```markdown
## BUG #XXX: [Titre court]

**Sévérité:** [CRITICAL | HIGH | MEDIUM | LOW]
**Priorité:** [P0 | P1 | P2 | P3]
**Composant:** [Backend API | Frontend | Database | Infrastructure]

### Description
[Description détaillée du bug]

### Steps to Reproduce
1. 
2. 
3. 

### Expected Behavior
[Ce qui devrait se passer]

### Actual Behavior
[Ce qui se passe réellement]

### Environment
- OS: Windows 10
- Docker version: 
- Browser (si applicable): 
- API version: 

### Logs
```
[Logs pertinents]
```

### Screenshots
[Captures d'écran si applicable]

### Possible Fix
[Si vous avez une idée de la solution]
```

---

## ✅ QA SIGN-OFF CHECKLIST

### **Infrastructure**
- [ ] Docker containers démarrent sans erreur
- [ ] PostgreSQL accessible et fonctionnel
- [ ] Redis accessible et fonctionnel
- [ ] Backend API répond sur port 8000
- [ ] Frontend charge sur port 3000

### **API Backend**
- [ ] Health check fonctionne
- [ ] Tous les endpoints répondent
- [ ] Validation des inputs fonctionne
- [ ] Error handling approprié
- [ ] CORS configuré correctement
- [ ] Swagger docs accessible

### **Frontend**
- [ ] Dashboard s'affiche
- [ ] Navigation fonctionne
- [ ] Responsive sur mobile/tablet/desktop
- [ ] Aucune erreur console
- [ ] Data fetching fonctionne

### **Database**
- [ ] Toutes les tables créées
- [ ] Foreign keys fonctionnent
- [ ] Indexes présents
- [ ] Constraints appliqués
- [ ] Performance acceptable

### **Business Logic**
- [ ] Scoring algorithm correct
- [ ] Classification fonctionne
- [ ] Recommendations pertinentes
- [ ] ROI calculation correcte
- [ ] Analytics précis

### **Performance**
- [ ] API response times acceptables
- [ ] Database queries optimisées
- [ ] Cache Redis fonctionne
- [ ] Pas de memory leaks
- [ ] Load handling OK

### **Security**
- [ ] OAuth flow sécurisé
- [ ] Input validation robuste
- [ ] SQL injection prévenue
- [ ] XSS sanitized
- [ ] CORS approprié

---

## 📊 QA METRICS

**Test Coverage:**
- Total Tests: ___
- Passed: ___
- Failed: ___
- Blocked: ___
- Coverage: ___%

**Defects:**
- Critical: ___
- High: ___
- Medium: ___
- Low: ___

**Performance:**
- Avg API Response: ___ms
- P95 Response: ___ms
- Database Query Avg: ___ms
- Frontend Load Time: ___s

---

## 🎯 QA CONCLUSION

**Ready for Production:** ⬜ YES | ⬜ NO | ⬜ CONDITIONAL

**Conditions (if any):**
1. 
2. 
3. 

**QA Engineer:** _________________  
**Date:** _________________  
**Signature:** _________________

---

**Notes Finales:**
_______________________________
_______________________________
_______________________________

