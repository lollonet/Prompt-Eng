# MySQL/MariaDB Template System - Troubleshooting Guide

## 🚨 Common Issues & Solutions

### Issue 1: "Web research module not available"

**Symptoms:**
```
⚠️ Web research module not available, using standard generation
```

**Cause:** Virtual environment not activated or missing dependencies

**Solution:**
```bash
# Activate virtual environment
source ./venv/bin/activate

# Verify aiohttp is installed
pip list | grep aiohttp

# If missing, install
pip install aiohttp
```

---

### Issue 2: Generic Templates Instead of MySQL Templates

**Symptoms:**
- Getting FastAPI/Python templates instead of MySQL Docker Compose
- Template type shows `focused_api` instead of `mysql_galera`

**Cause:** Template engine not properly selected

**Solution:**
```bash
# ✅ Be specific with technologies
python main.py --tech mariadb galera --auto-research

# ✅ Force database context
python main.py --tech mysql --task "database cluster" --auto-research

# ❌ Avoid generic terms
python main.py --tech database --auto-research
```

---

### Issue 3: "No compatible engines found"

**Symptoms:**
```
WARNING - No compatible engines found for technology: [technology]
```

**Solution:**
```bash
# Check available technologies
python main.py --list-tech

# Use exact technology names
python main.py --tech mysql mariadb galera

# Ensure auto-research is enabled
python main.py --tech mysql --auto-research
```

---

### Issue 4: Circuit Breaker Errors

**Symptoms:**
```
ERROR - Circuit breaker 'search_duckduckgo' OPENED
```

**Cause:** External search API failures (expected in restricted environments)

**Impact:** Templates still generate using local knowledge base

**Solution:** This is normal - templates will use cached knowledge and still work properly.

---

### Issue 5: Template Quality Too Low

**Symptoms:**
- Confidence score < 0.5
- Very short templates
- Missing configuration details

**Solution:**
```bash
# Add more context
python main.py \
  --tech mariadb galera \
  --task "production 3-node cluster with load balancing" \
  --cluster-size 3 \
  --ha-setup \
  --auto-research

# Include specific requirements
--requirements "Must handle 1000 concurrent connections"
```

---

### Issue 6: Missing Knowledge Base Files

**Symptoms:**
```
ERROR - File not found at /knowledge_base/best_practices/mysql_*.md
```

**Solution:**
```bash
# Verify files exist
ls knowledge_base/best_practices/mysql*
ls knowledge_base/tools/mysql*

# Files should include:
# - mysql_performance_optimization.md
# - mariadb_best_practices.md
# - galera_cluster_management.md
# - mysql.json, mariadb.json, etc.
```

---

### Issue 7: Import Errors

**Symptoms:**
```
ImportError: No module named 'web_research'
ModuleNotFoundError: No module named 'aiohttp'
```

**Solution:**
```bash
# Ensure you're in project directory
cd /path/to/Prompt-Eng

# Activate virtual environment
source ./venv/bin/activate

# Check Python path
python -c "import sys; print(sys.path)"

# Verify src is in path or run from project root
python main.py [options]
```

---

## 🔧 Debug Commands

### Check Template Engine Status
```bash
# Test MySQL engine directly
python -c "
import sys
sys.path.insert(0, 'src')
from web_research.template_engines.mysql_engine import MySQLTemplateEngine
engine = MySQLTemplateEngine()
print(f'Engine: {engine.name}')
print(f'Technologies: {engine.technologies}')
"
```

### Verify Knowledge Base
```bash
# Check tech stack mapping
python -c "
import json
with open('config/tech_stack_mapping.json') as f:
    mapping = json.load(f)
mysql_techs = ['mysql', 'mariadb', 'galera', 'mysql-cluster', 'proxysql']
for tech in mysql_techs:
    print(f'{tech}: {tech in mapping}')
"
```

### Test Template Generation
```bash
# Minimal test
python main.py --tech mysql --task "test" --cluster-size 1 --auto-research --quiet
```

---

## 📊 Expected Outputs

### Successful Galera Template Should Include:
- ✅ 3+ Docker services (galera-node-1, galera-node-2, galera-node-3)
- ✅ ProxySQL service configuration
- ✅ Galera configuration file (galera.cnf)
- ✅ Network configuration (galera_network)
- ✅ Volume definitions
- ✅ Operational commands section
- ✅ Security checklist
- ✅ 5000+ character comprehensive template

### Template Quality Indicators:
- **Confidence Score**: 0.85+ for MySQL templates
- **Template Type**: `mysql_galera`, `mysql_ndb`, `mysql_replication`
- **Complexity**: `moderate` or `complex` for clusters
- **Character Count**: 3000+ for production templates

---

## 🚑 Emergency Fixes

### Quick MySQL Template (Fallback)
If the system isn't working, you can still get basic MySQL templates:

```bash
# Basic MySQL without web research
python main.py --tech mysql --task "database setup" --format text

# Force specific template with manual description
python main.py \
  --tech mysql \
  --task "Deploy MariaDB Galera 3-node cluster with ProxySQL load balancer" \
  --cluster-size 3 \
  --ha-setup
```

### Reset Template Cache
```bash
# Clear research cache if corrupted
rm -rf cache/research/

# Clear template cache
rm -rf cache/templates/
```

### Verify Installation
```bash
# Check all required files
find . -name "mysql*" -type f
find . -name "*galera*" -type f
find . -name "*mariadb*" -type f

# Should find:
# - src/web_research/template_engines/mysql_engine.py
# - knowledge_base/best_practices/mysql_performance_optimization.md
# - knowledge_base/tools/mysql.json
# - And others...
```

---

## 📞 Getting Help

### Log Analysis
```bash
# Run with debug logging
python main.py --tech mysql --auto-research --verbose 2>&1 | tee debug.log

# Look for these key log entries:
# - "Registered X template engines" (should include mysql)
# - "Generating template using engine: mysql"
# - "Template generated successfully"
```

### Environment Check
```bash
# Python version
python --version  # Should be 3.8+

# Virtual environment status
which python  # Should point to ./venv/bin/python

# Required packages
pip list | grep -E "(aiohttp|async)"
```

### Minimal Working Example
```bash
# This should always work:
source ./venv/bin/activate
python main.py --tech mariadb --task "database" --auto-research
```

If this doesn't generate a proper MySQL template, there's a configuration issue.

---

## 🎯 Success Verification

A successful MySQL template generation should show:
```
🔍 Checking for unknown technologies...
✅ Generated dynamic templates for X technologies
🚀 Generated Prompt
==================================================
Technologies: mariadb, galera
# Mariadb Galera Cluster Setup
## TASK
Deploy: **3-node Mariadb Galera cluster with ProxySQL load balancer**
[... detailed configuration ...]
Character Count: 5000+
```

If you see this pattern, everything is working correctly! 🎉