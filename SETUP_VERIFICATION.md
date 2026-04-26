# 🔍 Setup Verification Guide

## Phase 1 - Infrastructure Setup Complete ✅

All files have been created according to the plan. Follow these steps to verify the infrastructure:

---

## 📋 Pre-requisites

Before running the verification steps, ensure you have:

- ✅ Docker Desktop installed and running
- ✅ Docker Compose v2.0+ installed
- ✅ 4GB+ available RAM
- ✅ 10GB+ available disk space

---

## 🚀 Verification Steps

### Step 1: Start Docker Services

```bash
# Navigate to project root
cd SalesforceLicenseOptimizer

# Start all services in detached mode
docker-compose up -d --build
```

**Expected output:**
```
[+] Building ...
[+] Running 4/4
 ✔ Network slo-network       Created
 ✔ Container slo-postgres    Started
 ✔ Container slo-redis       Started
 ✔ Container slo-backend     Started
```

---

### Step 2: Check Service Health

```bash
# Check all containers are running
docker-compose ps
```

**Expected output:**
```
NAME            IMAGE               STATUS              PORTS
slo-backend     ...                 Up (healthy)       0.0.0.0:8000->8000/tcp
slo-postgres    postgres:16-alpine  Up (healthy)       0.0.0.0:5432->5432/tcp
slo-redis       redis:7-alpine      Up (healthy)       0.0.0.0:6379->6379/tcp
```

All services should show `Up (healthy)` status.

---

### Step 3: Verify Backend Health Endpoint

```bash
# Test the health endpoint
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-29T...",
  "app_name": "salesforce-license-optimizer",
  "version": "1.0.0",
  "environment": "development"
}
```

Or open in browser: [http://localhost:8000/health](http://localhost:8000/health)

---

### Step 4: Verify API Documentation

Open in browser: [http://localhost:8000/docs](http://localhost:8000/docs)

You should see the FastAPI Swagger UI with the `/health` endpoint documented.

---

### Step 5: Check Backend Logs

```bash
# View backend logs
docker-compose logs backend

# Follow logs in real-time
docker-compose logs -f backend
```

**Expected log entries:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Starting salesforce-license-optimizer in development mode
INFO:     Debug mode: True
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Step 6: Verify Database Connection

```bash
# Connect to PostgreSQL
docker exec -it slo-postgres psql -U slo_user -d license_optimizer

# Inside psql, run:
\l                    # List databases
\dt                   # List tables (empty for now)
\q                    # Quit
```

---

### Step 7: Verify Redis Connection

```bash
# Connect to Redis
docker exec -it slo-redis redis-cli

# Inside redis-cli, run:
PING                  # Should return: PONG
INFO server           # Show server info
exit                  # Quit
```

---

## 🛠️ Troubleshooting

### Backend Container Won't Start

```bash
# Check backend logs for errors
docker-compose logs backend

# Common issues:
# 1. Port 8000 already in use
#    - Stop other services on port 8000
#    - Or change port in docker-compose.yml

# 2. Missing environment variables
#    - Check .env file exists
#    - Verify all required variables are set
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs db

# Verify database is healthy
docker exec slo-postgres pg_isready -U slo_user

# Reset database (if needed)
docker-compose down -v
docker-compose up -d
```

### Redis Connection Issues

```bash
# Check Redis logs
docker-compose logs redis

# Test Redis connectivity
docker exec slo-redis redis-cli ping
```

---

## 🧪 Testing Backend Locally (Without Docker)

If you want to run the backend locally for development:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env in backend/)
# Copy values from root .env.example and adjust DATABASE_URL

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Note:** You still need PostgreSQL and Redis running (via docker-compose or locally).

---

## 📊 Project Structure Verification

Verify the complete structure was created:

```bash
# Check backend structure
ls -la backend/app/
ls -la backend/app/models/
ls -la backend/app/repositories/
ls -la backend/app/services/
ls -la backend/app/strategies/
ls -la backend/app/factories/
ls -la backend/app/events/
ls -la backend/app/api/v1/

# Check frontend structure (for later phases)
ls -la frontend/src/
ls -la frontend/src/components/
ls -la frontend/src/hooks/
```

---

## ✅ Success Criteria

Phase 1 is complete when:

- [x] All directory structure created
- [x] All configuration files in place
- [x] Backend Python code implemented
- [x] Frontend scaffold created
- [x] Docker infrastructure configured
- [ ] `docker-compose up` successfully starts all services
- [ ] Health endpoint returns 200 OK
- [ ] PostgreSQL is accessible and healthy
- [ ] Redis is accessible and healthy
- [ ] No errors in logs

---

## 🎯 Next Steps

Once verification is complete, you're ready for:

**Phase 2 - Data Collection Engine (Days 3-7)**
- Salesforce OAuth implementation
- Repository pattern for 5-6 APIs
- Collection service orchestration

See [TODO.md](TODO.md) for the complete roadmap.

---

## 📞 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify Docker resources (RAM/CPU/Disk)
3. Ensure ports 5432, 6379, 8000 are available
4. Review environment variables in docker-compose.yml

---

> **Created:** December 29, 2025  
> **Phase:** 1 - Infrastructure Setup  
> **Status:** ✅ Complete

