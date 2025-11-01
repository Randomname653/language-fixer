# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Language-Fixer seriously. If you discover a security vulnerability, please report it responsibly:

### 🔒 **How to Report**

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. **Email:** Send details to the repository owner via GitHub
3. **Include:** 
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

### 🕐 **Response Timeline**

- **Initial Response:** Within 48 hours
- **Assessment:** Within 1 week
- **Fix Timeline:** Depends on severity
  - Critical: Within 24-48 hours
  - High: Within 1 week
  - Medium/Low: Next release cycle

### 🛡️ **Security Measures**

Language-Fixer implements several security best practices:

- **Safe Defaults:** DRY_RUN=true prevents accidental damage
- **Input Validation:** All file paths and commands are validated
- **Container Security:** Runs with non-root user (PUID/PGID)
- **Dependency Scanning:** Automated security updates via Dependabot
- **Code Analysis:** Regular CodeQL security scans
- **Docker Scanning:** Trivy vulnerability scanning for container images

### 🔍 **Security Features**

- **No Network Exposure:** Tool runs locally, no external API requirements
- **File System Isolation:** Operates only on mounted volumes
- **Audit Logging:** Comprehensive logging of all operations
- **Version Control:** Automatic update notifications with changelog

### 🏆 **Responsible Disclosure**

We appreciate security researchers who:
- Report vulnerabilities responsibly
- Allow reasonable time for fixes
- Respect user privacy and data

**Thank you for helping keep Language-Fixer secure!**