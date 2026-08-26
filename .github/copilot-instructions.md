# ESMH.TRADE Copilot Instructions

## Project Overview
**ESMH.TRADE** - Comprehensive AI-Powered Trading Platform

A full-stack trading system with:
- FastAPI backend with security layer
- PWA frontend
- Multiple exchange integrations
- Advanced trading bots (Forex, Crypto, Stocks)
- AI/ML models for price prediction & sentiment analysis
- Enterprise-grade security (2FA, AES-256, JWT, Audit logging)

## Code Quality Standards

### Python Backend
- Use **FastAPI** for async APIs
- Follow **PEP 8** standards
- Use **type hints** for all functions
- Implement proper **error handling**
- Add **logging** to critical sections
- Use **dependency injection** pattern
- Follow **SOLID** principles

### Security
- Always encrypt sensitive data
- Validate all inputs
- Use HTTPS in production
- Implement rate limiting
- Add audit logging for sensitive operations
- Use strong JWT tokens
- Enforce 2FA for admin operations

### Database
- Use SQLAlchemy ORM
- Implement migrations with Alembic
- Add proper indexing
- Use transactions for critical operations

### Frontend
- Use modern JavaScript (ES6+)
- Follow DRY principle
- Proper error handling
- Responsive design
- Progressive enhancement

## Upgrade Priorities

When polishing code, prioritize:

1. **Security** - Encryption, validation, authentication
2. **Performance** - Caching, optimization, async operations
3. **Reliability** - Error handling, logging, monitoring
4. **Maintainability** - Code structure, documentation, tests
5. **User Experience** - UI/UX improvements, responsiveness

## File Structure
```
backend/app/
├── api/              # API endpoints
├── core/             # Core engines (trading, risk, AI)
├── security/         # Security modules (encryption, 2FA, auth)
├── services/         # Business logic services
├── exchanges/        # Exchange integrations
├── data_providers/   # Market data providers
├── bots/             # Trading bots
├── ai/               # AI/ML models
├── models/           # Database models
└── utils/            # Utilities & helpers
```

## Development Workflow

1. **Code receives** → Analyze structure & patterns
2. **Polish** → Remove redundancy, optimize
3. **Upgrade** → Modernize, add security, improve performance
4. **Organize** → Create files, structure properly
5. **Document** → Add comments, docstrings
6. **Test** → Verify functionality

## Key Technologies

### Backend
- FastAPI, SQLAlchemy, Pydantic
- Cryptography, PyJWT, PyOTP
- Pandas, NumPy, Scikit-learn, TensorFlow
- CCXT, Python-Binance
- Celery, Redis

### Frontend
- Vanilla JavaScript (no framework initially)
- HTML5, CSS3
- Service Workers (PWA)
- Chart libraries (for trading charts)

### DevOps
- Docker & Docker Compose
- SQLite (can upgrade to PostgreSQL)
- Environment-based configuration

## Common Patterns

### API Endpoints
```python
@router.post("/endpoint", summary="Description")
async def endpoint(params, db: Session = Depends(get_db)):
    """Detailed docstring"""
    pass
```

### Security
```python
from app.security.encryption import encryption_service
encrypted = encryption_service.encrypt(data)
```

### Database
```python
from app.database import Base, get_db
from sqlalchemy import Column, String
class Model(Base):
    __tablename__ = "table_name"
```

## Review Checklist

Before delivering code, ensure:
- [ ] All imports are used
- [ ] No hardcoded secrets
- [ ] Proper error handling
- [ ] Type hints present
- [ ] Logging implemented
- [ ] Security best practices
- [ ] Comments/docstrings added
- [ ] Code follows project style
- [ ] No code duplication
- [ ] Tests pass (if applicable)

## Questions or Issues?
Refer to the README.md in project root for setup instructions.
