#!/bin/bash
# ============================================
# ESH.TRADE - ULTIMATE start.sh
# Complete Production & Development Script
# ============================================

set -e

# ============ COLORS ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# ============ FUNCTIONS ============
print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${GREEN}🚀 ESH.TRADE - ULTIMATE TRADING PLATFORM${NC}              ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}  ${CYAN}Version 4.0.0 | Forex | Crypto | Stocks | Metals${NC}    ${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${PURPLE}📍 $1${NC}"
}

# ============ CHECK PYTHON ============
check_python() {
    print_step "Checking Python..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found. Please install Python 3.9+"
        print_info "Download: https://python.org/downloads"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
    print_success "Python $PYTHON_VERSION found"
    
    # Check version
    if (( $(echo "$PYTHON_VERSION < 3.9" | bc -l) )); then
        print_error "Python 3.9+ required. Found: $PYTHON_VERSION"
        exit 1
    fi
}

# ============ CHECK PIP ============
check_pip() {
    print_step "Checking pip..."
    
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 not found"
        exit 1
    fi
    
    print_success "pip3 found"
}

# ============ CREATE VENV ============
create_venv() {
    print_step "Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# ============ INSTALL DEPENDENCIES ============
install_dependencies() {
    print_step "Installing dependencies..."
    
    if [ ! -f "venv/.installed" ]; then
        print_info "Upgrading pip..."
        pip install --upgrade pip -q
        
        print_info "Installing requirements..."
        pip install -r requirements.txt -q
        
        touch venv/.installed
        print_success "Dependencies installed"
    else
        print_success "Dependencies already installed"
    fi
}

# ============ CHECK .env ============
check_env() {
    print_step "Checking environment file..."
    
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        
        if [ -f ".env.example" ]; then
            print_info "Creating .env from example..."
            cp .env.example .env
            print_warning "Please edit .env with your settings"
        else
            print_error ".env file missing"
            exit 1
        fi
    else
        print_success ".env file found"
    fi
}

# ============ CREATE DIRECTORIES ============
create_directories() {
    print_step "Creating directories..."
    
    mkdir -p data/logs
    mkdir -p data/backups
    mkdir -p data/cache
    mkdir -p data/sessions
    mkdir -p data/biometric
    mkdir -p data/temp
    mkdir -p data/uploads
    
    print_success "Directories created"
}

# ============ CHECK DATABASE ============
check_database() {
    print_step "Checking database..."
    
    if [ ! -f "data/estrade.db" ]; then
        print_info "Initializing database..."
        python3 -c "
import sys
sys.path.insert(0, '.')
from backend.app.database import DatabaseManager
db = DatabaseManager()
print('✅ Database initialized successfully')
" 2>/dev/null || print_warning "Database initialization skipped"
    else
        print_success "Database exists"
    fi
}

# ============ CHECK REDIS ============
check_redis() {
    print_step "Checking Redis..."
    
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            print_success "Redis connected"
        else
            print_warning "Redis not running (optional)"
        fi
    else
        print_warning "Redis not installed (optional)"
    fi
}

# ============ CHECK EXCHANGES ============
check_exchanges() {
    print_step "Checking exchange API keys..."
    
    if [ -f ".env" ]; then
        source .env 2>/dev/null
        
        if [ -n "$BINANCE_API_KEY" ]; then
            print_success "Binance API configured"
        else
            print_warning "Binance API not configured (users will add their own)"
        fi
        
        if [ -n "$BYBIT_API_KEY" ]; then
            print_success "Bybit API configured"
        fi
    fi
}

# ============ CHECK EMAIL ============
check_email() {
    print_step "Checking email configuration..."
    
    if [ -f ".env" ]; then
        source .env 2>/dev/null
        
        if [ -n "$GMAIL_APP_PASSWORD" ]; then
            print_success "Email configured: $GMAIL_USER"
        else
            print_warning "Email not configured (TOTP will work without email)"
            print_info "Setup: https://myaccount.google.com/apppasswords"
        fi
    fi
}

# ============ RUN PRE-START CHECKS ============
pre_start_checks() {
    print_step "Running pre-start checks..."
    
    python3 -c "
from backend.app.config import settings
print(f'✅ App: {settings.APP_NAME} v{settings.APP_VERSION}')
print(f'✅ Environment: {settings.ENVIRONMENT}')
print(f'✅ Database: {settings.DATABASE_TYPE}')
print(f'✅ Min Capital: \${settings.MIN_CAPITAL}')
" 2>/dev/null || print_warning "Config check skipped"
}

# ============ START APPLICATION ============
start_app() {
    print_header
    
    print_step "Starting ESH.TRADE..."
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}  🌐 URL:      http://localhost:8000${NC}"
    echo -e "${WHITE}  📚 Docs:     http://localhost:8000/api/docs${NC}"
    echo -e "${WHITE}  🔑 Admin:    admin123 / eSmwas@2004${NC}"
    echo -e "${WHITE}  📧 Email:    estradingmachine@gmail.com${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check for reload flag
    if [ "$1" == "--reload" ]; then
        print_info "Development mode with hot reload"
        python3 -m uvicorn backend.app.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --reload \
            --log-level debug
    elif [ "$1" == "--dev" ]; then
        print_info "Development mode"
        python3 -m uvicorn backend.app.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --workers 1 \
            --reload \
            --log-level debug
    elif [ "$1" == "--prod" ]; then
        print_info "Production mode"
        python3 -m uvicorn backend.app.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --workers 8 \
            --loop uvloop \
            --http httptools \
            --log-level info
    else
        print_info "Standard mode"
        python3 -m uvicorn backend.app.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --workers 4 \
            --loop uvloop \
            --http httptools \
            --log-level info
    fi
}

# ============ MAIN ============
main() {
    print_header
    
    check_python
    check_pip
    create_venv
    install_dependencies
    check_env
    create_directories
    check_database
    check_redis
    check_exchanges
    check_email
    pre_start_checks
    start_app "$1"
}

# Run main
main "$@"