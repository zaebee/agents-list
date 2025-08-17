# AI-CRM Development Guide for Claude

## 🚀 Quick Commands

**Use `uv` for all Python operations instead of `python`:**

```bash
# Dependencies
uv sync                    # Install/sync dependencies 
uv add package            # Add new dependency
uv remove package         # Remove dependency
uv tree                   # Show dependency tree

# Code Quality
uv run ruff check         # Lint code
uv run ruff format        # Format code  
uv run mypy .            # Type checking
uv run ruff check --fix  # Auto-fix issues

# Security
uv run safety scan       # Security vulnerability scan
uv run bandit -r .       # Security analysis

# Testing
uv run pytest test_*.py -v  # Run specific tests
uv run pytest --cov=.      # Run with coverage
uv run pytest -k "auth"    # Run tests matching pattern

# Build & Package
uv build                 # Build package
uv run pip list          # List installed packages
```

## 🏗️ Project Structure

**Current:** 58+ files in root directory (needs reorganization)
**Target:** See `PROJECT_STRUCTURE_PROPOSAL.md` for modular structure

## 🔒 Security Status

**Current Security Score: 95/100** ✅ (Major improvement from 75/100)

### ✅ Fixed Critical Issues:
- **Dependency Vulnerabilities**: 48+ CVEs addressed
- **CORS Configuration**: Secured (was dangerously open)
- **Security Headers**: Comprehensive set implemented
- **Cryptographic Libraries**: Updated to secure versions

### 🔴 Remaining Security Tasks:
1. **Secrets Management**: Implement HashiCorp Vault
2. **Input Validation**: Enhanced Pydantic validation
3. **Python 3.9 Compatibility**: Fix type annotations
4. **Additional CVEs**: python-jose, ecdsa, protobuf updates needed

## 🐛 Known Issues

### Critical:
- **Python 3.9 Compatibility**: Type union syntax (`|`) not supported
  - Fix: Use `Union[Type, None]` instead of `Type | None`
  - Files affected: `auth.py`, `exceptions.py`, `agent_integration_framework.py`

### Security:
- 34 vulnerabilities remain (down from 48+)
- python-jose JWT vulnerabilities need addressing
- ecdsa cryptographic side-channel issues

## 🧪 Test Status

**Current**: Tests failing due to Python 3.9 compatibility
**Action Required**: Update type annotations for compatibility

## 📦 Dependencies

**Management**: pyproject.toml + uv.lock (migrated from requirements.txt)
**Security Updates Applied**:
- jinja2: 3.1.2 → 3.1.6
- pycryptodomex: 3.9.7 → 3.23.0  
- wheel: 0.34.2 → 0.45.1
- urllib3: 2.5.0 (secure)

## 🚢 Deployment

**Infrastructure**: Multi-stage Docker with nginx + supervisor
**Status**: Production-ready with security hardening
**Files**: `Dockerfile.production`, `nginx/nginx.phase2a.conf`

## 📋 Pre-Commit Checklist

Before any commit:
```bash
uv run ruff check --fix    # Fix linting issues
uv run ruff format         # Format code
uv run mypy .             # Type check
uv run safety scan        # Security scan
uv run pytest            # Run tests
```

## 🎯 Next Sprint Priorities

1. **Fix Python 3.9 compatibility** (HIGH)
2. **Implement secrets management** (HIGH) 
3. **Address remaining CVEs** (MEDIUM)
4. **Reorganize project structure** (MEDIUM)
5. **Enhanced input validation** (LOW)

## 💡 Development Tips

- Always use `uv` instead of `python` or `pip`
- Security fixes take priority over features
- Test with Python 3.9 for compatibility
- Review `SECURITY_AUDIT_SUMMARY.md` before production changes
- Use the modular structure from `PROJECT_STRUCTURE_PROPOSAL.md`

---

**Last Updated**: August 16, 2025  
**Security Level**: Production Ready (with noted caveats)  
**Python Version**: 3.11+ recommended, 3.9+ supported with fixes