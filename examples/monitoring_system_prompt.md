# Enterprise Monitoring System Deployment Prompt

## Generated Prompt for Docker Compose Monitoring Stack

This example demonstrates how the Advanced Prompt Engineering CLI generates optimized prompts for enterprise monitoring infrastructure deployment.

---

## TASK
Build: **Comprehensive monitoring system deployment with Prometheus, Grafana, and Alertmanager on RHEL9**

## TECHNICAL REQUIREMENTS
- **Target Environment**: RHEL9 production deployment
- **Container Runtime**: Docker with Docker Compose orchestration
- **Monitoring Stack**: Prometheus, Grafana, Alertmanager
- **Security Standards**: PCI DSS compliance required
- **Enterprise Features**: High availability, persistent storage, secure configurations

## EXPECTED OUTPUT EXAMPLE

### Docker Compose Configuration
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - monitoring
    security_opt:
      - no-new-privileges:true
    user: "1001:1001"

  grafana:
    image: grafana/grafana:10.0.0
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    networks:
      - monitoring
    security_opt:
      - no-new-privileges:true
    user: "472:472"

  alertmanager:
    image: prom/alertmanager:v0.25.0
    container_name: alertmanager
    restart: unless-stopped
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    networks:
      - monitoring
    security_opt:
      - no-new-privileges:true
    user: "1001:1001"

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
  alertmanager_data:
    driver: local
```

### Environment Variables (.env)
```bash
# Grafana Configuration
GRAFANA_USER=admin
GRAFANA_PASSWORD=${SECURE_GRAFANA_PASSWORD}

# Security Configuration
SECURE_GRAFANA_PASSWORD=<use-secret-management>
```

## IMPLEMENTATION REQUIREMENTS

### Security Best Practices
- **Non-root users**: All containers run with dedicated user IDs
- **Security options**: Enable no-new-privileges for all services
- **Secret management**: Use environment variables for sensitive data
- **Network isolation**: Dedicated monitoring network
- **Port exposure**: Minimal necessary port exposure

### Performance Optimization
- **Resource limits**: Configure memory and CPU limits
- **Data persistence**: Persistent volumes for all data
- **Health checks**: Implement health check endpoints
- **Retention policies**: Configure appropriate data retention

### Enterprise Compliance (PCI DSS)
- **Access controls**: Restricted Grafana user registration
- **Audit logging**: Enable comprehensive logging
- **Data encryption**: Secure data transmission
- **Version pinning**: Use specific image versions for reproducibility

### RHEL9 Specific Configuration
- **SELinux compatibility**: Container security contexts
- **Firewall rules**: Configure firewalld for required ports
- **System integration**: Systemd service integration for production

## BEST PRACTICES

1. **Container Security**
   - Pin specific image versions (never use 'latest')
   - Run containers with non-root users
   - Enable security options and constraints
   - Implement proper network segmentation

2. **Data Management**
   - Use named volumes for persistent data
   - Implement backup strategies for monitoring data
   - Configure retention policies based on compliance requirements

3. **Monitoring Configuration**
   - Set up proper Prometheus targets and scraping intervals
   - Configure Grafana dashboards for enterprise visibility
   - Implement alerting rules for critical infrastructure metrics

4. **Production Deployment**
   - Use external configuration management
   - Implement proper secret management (HashiCorp Vault, etc.)
   - Configure reverse proxy for secure external access
   - Set up SSL/TLS termination

## VALIDATION CHECKLIST

- [ ] All containers start successfully
- [ ] Prometheus can scrape configured targets
- [ ] Grafana can connect to Prometheus data source
- [ ] Alertmanager receives and processes alerts
- [ ] All services have health checks configured
- [ ] Security configurations are properly applied
- [ ] PCI DSS compliance requirements are met
- [ ] Data persistence is working correctly

---

**Generated by**: Advanced Prompt Engineering CLI - Enterprise Template Engine  
**Target Environment**: RHEL9 Production  
**Compliance Level**: PCI DSS  
**Template Engine**: DockerTemplateEngine  
**Generation Time**: ~8-12 seconds  
**Confidence Score**: 0.89/1.0