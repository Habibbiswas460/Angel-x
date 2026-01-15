# Security Policy

## Overview

Angel-X takes security seriously. This document outlines our security practices and how to report security vulnerabilities responsibly.

## Supported Versions

| Version | Status | Supported Until |
|---------|--------|-----------------|
| 2.x     | Active | January 2027    |
| 1.5.x   | LTS    | January 2026    |
| 1.0.x   | EOL    | June 2025       |

Security updates are provided for:
- ✅ Current major version (2.x)
- ✅ Previous LTS version (1.5.x)
- ❌ Older versions (1.0.x)

## Reporting Security Vulnerabilities

**DO NOT** open public GitHub issues for security vulnerabilities.

### Responsible Disclosure

To report a security vulnerability:

1. **Email us privately**
   - To: security@your-org.com
   - Include "SECURITY ISSUE" in subject line

2. **Provide details**
   - Vulnerability description
   - Affected version(s)
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)

3. **What to expect**
   - Acknowledgment within 24 hours
   - Updates every 3-5 days
   - Timeline to fix disclosed upfront
   - Credit in security advisory (if desired)

4. **Timeline**
   - **Critical**: Fixed within 24-48 hours
   - **High**: Fixed within 1 week
   - **Medium**: Fixed within 2 weeks
   - **Low**: Fixed with next release

### PGP Key

If you prefer encrypted communication:
```
pub   4096R/YOUR_KEY_ID created: 2026-01-01 expires: never
uid   Security <security@your-org.com>
```

[Download PGP key](https://your-org.com/.well-known/security.asc)

## Security Best Practices

### For Users

#### API Key Management
```python
# ❌ NEVER do this
ANGELONE_API_KEY = "your-actual-key-here"

# ✅ Always use environment variables
import os
ANGELONE_API_KEY = os.getenv("ANGELONE_API_KEY")

# ✅ Or use .env files with python-dotenv
from dotenv import load_dotenv
load_dotenv()
ANGELONE_API_KEY = os.getenv("ANGELONE_API_KEY")
```

#### Credentials File Security
```bash
# ✅ Restrict permissions on config files
chmod 600 config/config.production.py

# ✅ Never commit credentials
echo "config/config.production.py" >> .gitignore

# ✅ Use environment variables in production
export ANGELONE_API_KEY="your-key"
export DATABASE_URL="postgresql://..."
```

#### Network Security
- ✅ Use HTTPS for all connections
- ✅ Verify SSL certificates
- ✅ Use VPN in public networks
- ✅ Keep broker connection credentials secure
- ❌ Don't share API keys via email or chat

#### Database Security
- ✅ Use strong passwords (20+ characters)
- ✅ Enable encryption at rest
- ✅ Use connection pooling
- ✅ Regular backups with encryption
- ✅ Restrict database access to localhost/VPN

```bash
# ✅ Secure PostgreSQL connection
export DATABASE_URL="postgresql://user:pass@localhost:5432/angel_x?sslmode=require"

# ✅ Backup with encryption
pg_dump -U admin angel_x | gpg --encrypt -r security@your-org.com > backup.sql.gpg
```

#### Paper Trading
- ✅ Always test with paper trading first
- ✅ Validate all strategies in paper mode
- ✅ Never enable real trading accidentally
- ✅ Use feature flags for real trading

```python
# ✅ Feature flag for real trading
ENABLE_REAL_TRADING = os.getenv("ENABLE_REAL_TRADING", "false").lower() == "true"

if ENABLE_REAL_TRADING:
    broker = BrokerClient(paper_trading=False)
else:
    broker = BrokerClient(paper_trading=True)
```

### For Developers

#### Secure Coding Practices

**Input Validation**
```python
# ❌ Dangerous - no validation
def place_order(symbol, qty):
    return broker.place_order(symbol, qty)

# ✅ Safe - validates input
def place_order(symbol: str, qty: int) -> Dict:
    if not isinstance(symbol, str) or len(symbol) == 0:
        raise ValueError("Invalid symbol")
    if not isinstance(qty, int) or qty <= 0:
        raise ValueError("Quantity must be positive integer")
    return broker.place_order(symbol, qty)
```

**Error Handling**
```python
# ❌ Dangerous - exposes sensitive info
except Exception as e:
    return {"error": str(e)}  # May expose secrets in traceback

# ✅ Safe - generic error message
except ConnectionError as e:
    logger.error(f"Broker connection failed: {e}")
    return {"error": "Unable to connect to broker"}
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return {"error": "Internal server error"}
```

**SQL Injection Prevention**
```python
# ❌ Dangerous - SQL injection vulnerable
query = f"SELECT * FROM orders WHERE symbol = '{symbol}'"
result = db.execute(query)

# ✅ Safe - parameterized query
query = "SELECT * FROM orders WHERE symbol = %s"
result = db.execute(query, (symbol,))
```

**Secrets Management**
```python
# ❌ Dangerous - secrets in code
API_KEY = "sk_live_abc123def456"

# ✅ Safe - environment variables
API_KEY = os.getenv("ANGELONE_API_KEY")

# ✅ Better - secrets manager
from aws_secretsmanager import SecretManager
API_KEY = SecretManager().get_secret("angelone/api_key")
```

**Logging Security**
```python
# ❌ Dangerous - logs secrets
logger.info(f"Connecting with API key: {api_key}")

# ✅ Safe - masks sensitive data
logger.info("Connecting with API key: sk_live_***")

# ✅ Better - never log secrets
logger.debug(f"Broker connection initiated")
```

#### Dependency Security

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Keep dependencies updated
pip list --outdated
pip install --upgrade pip

# Use exact versions in production
pip freeze > requirements-prod.txt

# Regularly scan dependencies
pip install pip-audit
pip-audit --desc
```

#### Code Review Guidelines

Security aspects to review:

- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all user inputs
- [ ] Proper error handling without info disclosure
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention if applicable
- [ ] CSRF tokens if applicable
- [ ] Rate limiting on API endpoints
- [ ] Proper authentication and authorization
- [ ] Logging doesn't expose sensitive data
- [ ] Dependencies are up to date
- [ ] No use of weak cryptographic algorithms

### For Maintainers

#### Release Security Checklist

Before releasing a new version:

- [ ] All security patches applied
- [ ] Dependencies updated to latest secure versions
- [ ] Security review completed
- [ ] Tests passing, including security tests
- [ ] No new CVEs in dependencies
- [ ] Documentation updated with security notes
- [ ] Version bump reflects security importance (patch for fixes)
- [ ] Security advisories issued if needed
- [ ] Release notes mention security updates

#### Monitoring

```bash
# Docker image scanning
docker scan angelone/angel-x:latest

# Dependency vulnerabilities
pip install bandit
bandit -r src/

# SAST scanning
pip install pylint
pylint src/ --disable=all --enable=security
```

## Known Security Considerations

### Broker Integration

**Risk**: API credentials theft
- **Mitigation**: Never log credentials, use environment variables, restrict file permissions
- **Detection**: Monitor API usage for unusual patterns

**Risk**: Unauthorized order placement
- **Mitigation**: Rate limiting, amount limits, manual confirmation for large trades
- **Detection**: Real-time alerts on trades

**Risk**: Data man-in-the-middle attacks
- **Mitigation**: HTTPS only, certificate pinning, VPN in public networks
- **Detection**: SSL certificate monitoring

### WebSocket Connections

**Risk**: Connection hijacking
- **Mitigation**: TLS encryption, token rotation, connection validation
- **Detection**: Unusual IP addresses, multiple simultaneous connections

**Risk**: Message tampering
- **Mitigation**: Message signing, HMAC validation
- **Detection**: Checksum validation

### Database Security

**Risk**: SQL injection
- **Mitigation**: Parameterized queries, input validation
- **Detection**: Query logging, anomaly detection

**Risk**: Unauthorized access
- **Mitigation**: Strong passwords, network isolation, encryption
- **Detection**: Access logs, failed login attempts

**Risk**: Data breach
- **Mitigation**: Encryption at rest, backups, data minimization
- **Detection**: File integrity monitoring

### Machine Learning Models

**Risk**: Model poisoning with manipulated data
- **Mitigation**: Data validation, outlier detection, cross-validation
- **Detection**: Model performance degradation

**Risk**: Adversarial attacks on model
- **Mitigation**: Confidence thresholds, gradient clipping
- **Detection**: Unusual prediction patterns

## Security Headers

When deployed as web service:

```python
@app.after_request
def set_security_headers(response):
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # HTTPS enforcement
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    
    # Prevent referrer leaks
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response
```

## Rate Limiting

Implement rate limiting to prevent abuse:

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/api/orders", methods=["POST"])
@limiter.limit("5 per minute")
def place_order():
    return broker.place_order()
```

## Incident Response

### If You Discover a Vulnerability

1. **Stop and assess**
   - Don't continue testing
   - Don't create proof-of-concept exploits
   - Document what you found

2. **Report immediately**
   - Email security@your-org.com
   - Include all details
   - Provide your contact information

3. **Cooperate with fix**
   - Answer follow-up questions
   - Help verify fix if requested
   - Maintain confidentiality

### If Vulnerability is Disclosed

1. **Contain**
   - Assess impact and scope
   - Determine if live systems affected

2. **Fix**
   - Develop patch
   - Verify fix works
   - Prepare release

3. **Communicate**
   - Notify affected users
   - Release security advisory
   - Update documentation

4. **Review**
   - Post-incident analysis
   - Prevent similar issues
   - Update security practices

## Compliance

Angel-X follows these standards:

- ✅ **OWASP Top 10** - Security best practices
- ✅ **PCI DSS** - If processing payment data
- ✅ **SOC 2** - Applicable security controls
- ✅ **GDPR** - If handling EU user data

## Security Contacts

- **Security Issues**: security@your-org.com
- **Security Advisory**: advisory@your-org.com
- **General Questions**: support@your-org.com
- **PGP Key**: security@your-org.com

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Flask Security](https://flask.palletsprojects.com/en/2.3.x/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/sql-syntax.html)
- [Broker API Security](https://www.angelbroking.com/api-docs)

## Updates

This security policy is reviewed and updated:
- ✅ Quarterly (every 3 months)
- ✅ After any security incident
- ✅ When new threats emerge
- ✅ When adding new features

---

**Security is a shared responsibility. Thank you for helping keep Angel-X secure.**

*Last Updated: January 12, 2026*
*Next Review: April 12, 2026*
