# High-Availability PostgreSQL Cluster Prompt

## Generated Prompt for Patroni-based Database Cluster

This example demonstrates how the Advanced Prompt Engineering CLI generates optimized prompts for enterprise database cluster deployment using Patroni.

---

## TASK
Build: **3-node PostgreSQL cluster with Patroni on RHEL9 using automation**

## TECHNICAL REQUIREMENTS
- **Target Environment**: RHEL9 cluster environment
- **Database**: PostgreSQL 14+ with Patroni for high availability
- **Consensus Store**: etcd cluster for distributed coordination
- **Deployment Method**: Ansible automation with enterprise configurations
- **Cluster Size**: 3 nodes (1 primary, 2 standby replicas)
- **Security Standards**: Enterprise-grade security with encryption

## EXPECTED OUTPUT EXAMPLE

### Ansible Playbook Structure
```yaml
---
- name: Deploy PostgreSQL Patroni Cluster
  hosts: postgres_cluster
  become: yes
  vars:
    postgresql_version: "14"
    patroni_version: "3.0.2"
    etcd_version: "3.5.9"
    cluster_name: "postgres-ha-cluster"
    
  tasks:
    - name: Install PostgreSQL and dependencies
      dnf:
        name:
          - postgresql{{ postgresql_version }}-server
          - postgresql{{ postgresql_version }}-contrib
          - python3-psycopg2
          - python3-pip
        state: present

    - name: Install Patroni
      pip:
        name:
          - patroni[etcd]=={{ patroni_version }}
          - psycopg2-binary
        state: present

    - name: Create patroni configuration directory
      file:
        path: /etc/patroni
        state: directory
        mode: '0755'

    - name: Deploy Patroni configuration
      template:
        src: patroni.yml.j2
        dest: /etc/patroni/patroni.yml
        mode: '0600'
        backup: yes
      notify: restart patroni

    - name: Create systemd service for Patroni
      template:
        src: patroni.service.j2
        dest: /etc/systemd/system/patroni.service
      notify:
        - reload systemd
        - restart patroni

    - name: Configure firewall for PostgreSQL
      firewalld:
        port: "{{ item }}"
        permanent: yes
        state: enabled
        immediate: yes
      loop:
        - "5432/tcp"  # PostgreSQL
        - "8008/tcp"  # Patroni REST API

    - name: Start and enable Patroni service
      systemd:
        name: patroni
        state: started
        enabled: yes
        daemon_reload: yes

  handlers:
    - name: reload systemd
      systemd:
        daemon_reload: yes

    - name: restart patroni
      systemd:
        name: patroni
        state: restarted
```

### Patroni Configuration Template (patroni.yml.j2)
```yaml
scope: {{ cluster_name }}
namespace: /db/
name: {{ ansible_hostname }}

restapi:
  listen: {{ ansible_default_ipv4.address }}:8008
  connect_address: {{ ansible_default_ipv4.address }}:8008

etcd:
  hosts:
{% for host in groups['etcd_cluster'] %}
    - {{ hostvars[host]['ansible_default_ipv4']['address'] }}:2379
{% endfor %}

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 60
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      use_slots: true
      parameters:
        max_connections: 200
        shared_preload_libraries: pg_stat_statements
        wal_level: replica
        hot_standby: "on"
        wal_keep_segments: 8
        max_wal_senders: 10
        max_replication_slots: 10
        wal_log_hints: "on"
        logging_collector: "on"
        log_destination: csvlog
        log_directory: pg_log
        log_filename: postgresql-%Y-%m-%d_%H%M%S.log
        log_checkpoints: "on"
        log_connections: "on"
        log_disconnections: "on"
        log_lock_waits: "on"
        log_temp_files: 0

  initdb:
    - encoding: UTF8
    - data-checksums

  pg_hba:
    - host replication replicator 127.0.0.1/32 md5
    - host replication replicator {{ ansible_default_ipv4.network }}/{{ ansible_default_ipv4.netmask | ipaddr('prefix') }} md5
    - host all all 0.0.0.0/0 md5

  users:
    admin:
      password: "{{ postgres_admin_password }}"
      options:
        - createrole
        - createdb

postgresql:
  listen: {{ ansible_default_ipv4.address }}:5432
  connect_address: {{ ansible_default_ipv4.address }}:5432
  data_dir: /var/lib/pgsql/{{ postgresql_version }}/data
  bin_dir: /usr/pgsql-{{ postgresql_version }}/bin
  pgpass: /tmp/pgpass
  authentication:
    replication:
      username: replicator
      password: "{{ postgres_replication_password }}"
    superuser:
      username: postgres
      password: "{{ postgres_superuser_password }}"

tags:
  nofailover: false
  noloadbalance: false
  clonefrom: false
  nosync: false
```

### Inventory Configuration (inventory.ini)
```ini
[postgres_cluster]
postgres-01 ansible_host=10.0.1.10
postgres-02 ansible_host=10.0.1.11  
postgres-03 ansible_host=10.0.1.12

[etcd_cluster]
etcd-01 ansible_host=10.0.1.20
etcd-02 ansible_host=10.0.1.21
etcd-03 ansible_host=10.0.1.22

[all:vars]
ansible_user=ansible
ansible_ssh_private_key_file=~/.ssh/id_rsa
```

## IMPLEMENTATION REQUIREMENTS

### High Availability Architecture
- **Consensus Management**: etcd cluster for distributed coordination
- **Automatic Failover**: Patroni manages primary/standby switching
- **Split-brain Prevention**: Proper DCS (Distributed Configuration Store) setup
- **Health Monitoring**: Continuous cluster health checks

### Security Configuration
- **Authentication**: Strong password policies for all database users
- **Network Security**: Firewall rules for cluster communication
- **Encryption**: TLS encryption for client connections
- **Access Control**: Restricted pg_hba.conf configuration

### Performance Optimization
- **Connection Pooling**: Optimized max_connections settings
- **WAL Management**: Proper Write-Ahead Logging configuration
- **Replication**: Streaming replication with slots
- **Monitoring**: pg_stat_statements for query performance

### Backup and Recovery
- **WAL Archiving**: Configure continuous WAL archiving
- **Point-in-time Recovery**: Enable PITR capabilities
- **Backup Strategy**: Automated backup scheduling
- **Disaster Recovery**: Cross-site replication setup

## BEST PRACTICES

1. **Cluster Configuration**
   - Use odd number of nodes for quorum
   - Separate etcd cluster from PostgreSQL nodes
   - Configure proper network latency thresholds
   - Implement comprehensive monitoring

2. **Security Hardening**
   - Use dedicated service accounts
   - Implement certificate-based authentication
   - Enable audit logging for compliance
   - Regular security updates and patching

3. **Performance Tuning**
   - Configure shared_buffers based on available memory
   - Optimize checkpoint settings for workload
   - Set appropriate work_mem and maintenance_work_mem
   - Monitor and tune based on actual usage patterns

4. **Operational Excellence**
   - Implement automated health checks
   - Set up alerting for cluster events
   - Document runbooks for common scenarios
   - Regular backup testing and validation

## DEPLOYMENT COMMANDS

### Execute Playbook
```bash
# Deploy complete cluster
ansible-playbook -i inventory.ini deploy-patroni-cluster.yml

# Deploy with specific variables
ansible-playbook -i inventory.ini deploy-patroni-cluster.yml \
  --extra-vars "postgres_admin_password=SecureAdminPass123"

# Check cluster status
ansible postgres_cluster -i inventory.ini -m shell \
  -a "patronictl -c /etc/patroni/patroni.yml list"
```

### Cluster Management
```bash
# Check cluster status
patronictl -c /etc/patroni/patroni.yml list

# Manual failover
patronictl -c /etc/patroni/patroni.yml failover

# Restart cluster
patronictl -c /etc/patroni/patroni.yml restart postgres-ha-cluster

# Reload configuration
patronictl -c /etc/patroni/patroni.yml reload postgres-ha-cluster
```

## VALIDATION CHECKLIST

- [ ] All PostgreSQL nodes are running and accessible
- [ ] Patroni cluster shows healthy status
- [ ] etcd cluster is operational and accessible
- [ ] Primary/standby replication is working
- [ ] Automatic failover functionality tested
- [ ] Firewall rules allow cluster communication
- [ ] Backup and recovery procedures validated
- [ ] Monitoring and alerting configured
- [ ] Security configurations applied
- [ ] Performance parameters optimized

## MONITORING INTEGRATION

### Prometheus Metrics
```yaml
# Add to prometheus.yml
- job_name: 'patroni'
  static_configs:
    - targets: 
      - '10.0.1.10:8008'
      - '10.0.1.11:8008'
      - '10.0.1.12:8008'
  scrape_interval: 15s
  metrics_path: /metrics
```

### Grafana Dashboard
- **Cluster Overview**: Node status, primary/standby roles
- **Performance Metrics**: Connection counts, query performance
- **Replication Lag**: Monitor standby synchronization
- **Resource Usage**: CPU, memory, disk utilization

---

**Generated by**: Advanced Prompt Engineering CLI - Enterprise Template Engine  
**Target Environment**: RHEL9 Cluster  
**Template Engine**: AnsibleTemplateEngine  
**Generation Time**: ~12-18 seconds  
**Confidence Score**: 0.91/1.0  
**Complexity Level**: Advanced Enterprise