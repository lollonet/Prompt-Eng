# MySQL/MariaDB Template System - Quick Reference Guide

> **Complete cheat sheet for using the MySQL/MariaDB clustering templates in the Prompt Engineering CLI**

## 🚀 Quick Start

### Prerequisites
```bash
# Activate virtual environment (required for full functionality)
source ./venv/bin/activate

# Verify installation
python main.py --help
```

### Basic Usage Pattern
```bash
python main.py --tech [TECHNOLOGY] --task "[DESCRIPTION]" [OPTIONS] --auto-research
```

## 📋 Available MySQL Technologies

| Technology | Description | Use Case |
|------------|-------------|----------|
| `mysql` | MySQL Database Server | General database needs |
| `mariadb` | MariaDB Database Server | MySQL alternative with enhanced features |
| `galera` | Galera Cluster | Multi-master synchronous replication |
| `mysql-cluster` | MySQL NDB Cluster | Distributed computing and high availability |
| `proxysql` | ProxySQL Load Balancer | Connection pooling and load balancing |

## 🏗️ Deployment Patterns

### 1. Galera Cluster (Recommended for HA)
```bash
# 3-node MariaDB Galera cluster with ProxySQL
python main.py \
  --tech mariadb galera proxysql \
  --task "high availability database cluster" \
  --cluster-size 3 \
  --ha-setup \
  --monitoring-stack prometheus grafana \
  --auto-research
```

**Generates:**
- 3-node Galera cluster configuration
- ProxySQL load balancer setup
- Monitoring with Prometheus/Grafana
- Security hardening checklist
- Operational commands

### 2. MySQL NDB Cluster (Distributed Computing)
```bash
# 4-node MySQL NDB cluster
python main.py \
  --tech mysql mysql-cluster \
  --task "distributed database cluster" \
  --cluster-size 4 \
  --auto-research
```

**Generates:**
- NDB management nodes
- Data nodes configuration
- MySQL server setup
- Cluster initialization scripts

### 3. Master-Slave Replication
```bash
# MySQL replication setup
python main.py \
  --tech mysql \
  --task "master-slave replication setup" \
  --cluster-size 2 \
  --backup-strategy incremental \
  --auto-research
```

**Generates:**
- Master server configuration
- Slave server setup
- Replication user creation
- Failover procedures

### 4. Single Instance (Development)
```bash
# Single MySQL instance
python main.py \
  --tech mysql \
  --task "development database" \
  --cluster-size 1 \
  --auto-research
```

**Generates:**
- Single MySQL container
- Development-friendly configuration
- Basic monitoring setup

## 🔧 Essential CLI Options

### Database-Specific Options
```bash
--db-engine mysql              # Force MySQL engine selection
--db-version 8.0              # Specify MySQL version
--cluster-size N              # Number of nodes (default: 3)
```

### High Availability Options
```bash
--ha-setup                    # Enable HA configuration
--backup-strategy [TYPE]      # continuous|scheduled|snapshot|incremental
--disaster-recovery           # Include DR procedures
```

### Monitoring & Security
```bash
--monitoring-stack prometheus grafana    # Add monitoring
--security-standards pci-dss hipaa      # Compliance standards
--encryption tls1.3                     # Encryption standard
```

### Infrastructure Options
```bash
--distro rhel9                # Target OS (rhel9|ubuntu22|debian11)
--cloud-provider aws          # Cloud platform
--container-runtime docker    # Container runtime
```

## 🎯 Common Use Cases

### Production Galera Cluster
```bash
python main.py \
  --tech mariadb galera \
  --task "production database cluster" \
  --cluster-size 3 \
  --ha-setup \
  --backup-strategy continuous \
  --security-standards pci-dss \
  --monitoring-stack prometheus grafana \
  --encryption tls1.3 \
  --distro rhel9 \
  --auto-research \
  --format text
```

### Development MySQL Setup
```bash
python main.py \
  --tech mysql \
  --task "local development database" \
  --cluster-size 1 \
  --container-runtime docker \
  --auto-research
```

### Enterprise MariaDB with MaxScale
```bash
python main.py \
  --tech mariadb proxysql \
  --task "enterprise database with load balancing" \
  --cluster-size 5 \
  --ha-setup \
  --monitoring-stack prometheus \
  --security-standards hipaa gdpr \
  --auto-research
```

## 📊 Output Formats

| Format | Command | Best For |
|--------|---------|----------|
| Text | `--format text` | Terminal viewing, documentation |
| JSON | `--format json` | API integration, automation |
| Markdown | `--format markdown` | Documentation, wikis |

### Save to File
```bash
python main.py [OPTIONS] --output galera-cluster.md
```

## 🛠️ Template Components Generated

### Docker Compose Files
- **Services**: Database nodes, load balancers, monitoring
- **Networks**: Cluster communication setup
- **Volumes**: Persistent data storage
- **Environment**: Security and configuration variables

### Configuration Files
- **Galera Configuration** (`galera.cnf`)
- **ProxySQL Configuration** (`proxysql.cnf`)
- **MySQL Configuration** (`my.cnf`)
- **Monitoring Configuration** (`prometheus.yml`)

### Operational Scripts
- **Cluster Status Checks**
- **Backup Procedures**
- **Recovery Commands**
- **Performance Monitoring**

### Security Checklists
- [ ] Password management
- [ ] SSL/TLS configuration
- [ ] User access controls
- [ ] Network security
- [ ] Compliance verification

## 🔍 Troubleshooting

### Web Research Not Working
```bash
# Ensure virtual environment is activated
source ./venv/bin/activate

# Check dependencies
pip list | grep aiohttp
```

### Template Engine Not Selected
```bash
# Force MySQL engine usage by being specific
python main.py --tech mysql mariadb --auto-research
```

### No Output Generated
```bash
# Check technology recognition
python main.py --list-tech | grep mysql

# Verify template availability
python main.py --tech mysql --task "test" --auto-research
```

## 📚 Advanced Features

### Interactive Mode
```bash
python main.py --interactive
# Follow guided prompts for MySQL setup
```

### Technology Listing
```bash
python main.py --list-tech          # All available technologies
python main.py --list-examples      # Predefined examples
```

### Custom Requirements
```bash
python main.py \
  --tech mariadb galera \
  --requirements "Must support 10000 concurrent connections" \
  --auto-research
```

## 🎯 Best Practices

### 1. Always Use Auto-Research
```bash
# ✅ Recommended
--auto-research

# ❌ Missing dynamic templates
# (omit --auto-research)
```

### 2. Specify Multiple Technologies
```bash
# ✅ Better template selection
--tech mariadb galera proxysql

# ❌ Generic templates
--tech database
```

### 3. Use Appropriate Cluster Sizes
- **Development**: `--cluster-size 1`
- **Testing**: `--cluster-size 3`
- **Production**: `--cluster-size 3` or `5` (odd numbers)

### 4. Include Monitoring
```bash
--monitoring-stack prometheus grafana  # Production monitoring
```

### 5. Save Important Templates
```bash
--output production-galera-cluster.md  # Save for reuse
```

## 🔗 Quick Reference Commands

### Most Common Commands
```bash
# Quick Galera cluster
python main.py --tech mariadb galera --cluster-size 3 --ha-setup --auto-research

# MySQL development
python main.py --tech mysql --cluster-size 1 --auto-research

# Production-ready with monitoring
python main.py --tech mariadb galera --cluster-size 3 --ha-setup --monitoring-stack prometheus --auto-research

# Enterprise setup
python main.py --tech mariadb proxysql --cluster-size 5 --ha-setup --security-standards pci-dss --auto-research
```

### Template Quality Indicators
- **Quality Score**: 0.85+ indicates high-quality templates
- **Complexity**: `simple` | `moderate` | `complex`
- **Character Count**: 5000+ chars for comprehensive templates

---

## 💡 Pro Tips

1. **Start with virtual environment**: Always `source ./venv/bin/activate`
2. **Use descriptive tasks**: Better task descriptions = better templates
3. **Combine technologies**: `mariadb galera proxysql` for complete solutions
4. **Save successful configs**: Use `--output` for reusable templates
5. **Check template quality**: Look for 0.85+ confidence scores

**Need help?** Run `python main.py --help` for full option reference!