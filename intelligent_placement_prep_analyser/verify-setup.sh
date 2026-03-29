#!/bin/bash

# Verification script for Placement Prep Analyser setup
echo "================================================"
echo "Placement Prep Analyser - Setup Verification"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to check
check_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_failure() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

echo "1. Checking Python Environment..."
if [ -d "backend/venv" ]; then
    check_success "Virtual environment exists at backend/venv"
else
    check_failure "Virtual environment not found at backend/venv"
fi

echo ""
echo "2. Checking Backend Configuration..."
if [ -f "backend/requirements.txt" ]; then
    check_success "requirements.txt found"
    if grep -q "fastapi\|sqlalchemy\|psycopg2" backend/requirements.txt; then
        check_success "Core dependencies listed in requirements.txt"
    else
        check_failure "Missing core dependencies in requirements.txt"
    fi
else
    check_failure "requirements.txt not found"
fi

if [ -f "backend/.env" ]; then
    check_success "Backend .env file found"
    if grep -q "DATABASE_URL" backend/.env; then
        check_success "DATABASE_URL configured in .env"
    else
        check_failure "DATABASE_URL not configured"
    fi
else
    check_failure "Backend .env file not found"
fi

echo ""
echo "3. Checking Frontend Configuration..."
if [ -f "frontend/package.json" ]; then
    check_success "Frontend package.json found"
    if grep -q "react\|vite" frontend/package.json; then
        check_success "React and Vite configured"
    else
        check_failure "React or Vite not configured"
    fi
else
    check_failure "Frontend package.json not found"
fi

if [ -f "frontend/vite.config.js" ]; then
    check_success "Vite configuration found"
    if grep -q "5175" frontend/vite.config.js; then
        check_success "Frontend port 5175 configured"
    else
        check_failure "Frontend port not set to 5175"
    fi
else
    check_failure "Vite configuration not found"
fi

if [ -f "frontend/.env" ]; then
    check_success "Frontend .env file found"
else
    check_failure "Frontend .env file not found"
fi

echo ""
echo "4. Checking Database Configuration..."
if [ -f "backend/app/database/migrate.py" ]; then
    check_success "Migration script found"
else
    check_failure "Migration script not found"
fi

if [ -f "backend/app/database/db.py" ]; then
    check_success "Database configuration found"
    if grep -q "postgresql\|QueuePool" backend/app/database/db.py; then
        check_success "PostgreSQL pooling configured"
    else
        check_failure "PostgreSQL pooling not configured"
    fi
else
    check_failure "Database configuration not found"
fi

echo ""
echo "5. Checking API Configuration..."
if [ -f "backend/app/main.py" ]; then
    check_success "FastAPI main app found"
    if grep -q "CORSMiddleware\|5175" backend/app/main.py; then
        check_success "CORS configured for port 5175"
    else
        check_failure "CORS not configured for frontend"
    fi
else
    check_failure "FastAPI main app not found"
fi

if [ -f "frontend/src/config/api.js" ]; then
    check_success "Frontend API configuration found"
    if grep -q "8003" frontend/src/config/api.js; then
        check_success "Frontend configured to use port 8003"
    else
        check_failure "Frontend not configured for port 8003"
    fi
else
    check_failure "Frontend API configuration not found"
fi

echo ""
echo "6. Checking Startup Scripts..."
if [ -f "run-backend.sh" ] && [ -x "run-backend.sh" ]; then
    check_success "run-backend.sh found and executable"
else
    check_warning "run-backend.sh not found or not executable"
fi

if [ -f "run-frontend.sh" ] && [ -x "run-frontend.sh" ]; then
    check_success "run-frontend.sh found and executable"
else
    check_warning "run-frontend.sh not found or not executable"
fi

if [ -f "run-all.sh" ] && [ -x "run-all.sh" ]; then
    check_success "run-all.sh found and executable"
else
    check_warning "run-all.sh not found or not executable"
fi

echo ""
echo "7. Documentation..."
if [ -f "SETUP_GUIDE.md" ]; then
    check_success "SETUP_GUIDE.md found"
else
    check_warning "SETUP_GUIDE.md not found"
fi

if [ -f "PORT_CONFIG.md" ]; then
    check_success "PORT_CONFIG.md found"
else
    check_warning "PORT_CONFIG.md not found"
fi

# Summary
echo ""
echo "================================================"
echo "Verification Summary"
echo "================================================"
echo -e "${GREEN}Passed:${NC} $CHECKS_PASSED"
echo -e "${RED}Failed:${NC} $CHECKS_FAILED"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to run.${NC}"
    echo ""
    echo "To start the application:"
    echo "  bash run-all.sh"
    echo ""
    echo "Or start services individually:"
    echo "  bash run-backend.sh   # Terminal 1"
    echo "  bash run-frontend.sh  # Terminal 2"
else
    echo -e "${RED}✗ Some checks failed. Please review the setup.${NC}"
fi

echo ""
echo "Service URLs:"
echo "  Frontend:      http://localhost:5175"
echo "  Backend API:   http://localhost:8003"
echo "  Swagger Docs:  http://localhost:8003/docs"
echo ""
