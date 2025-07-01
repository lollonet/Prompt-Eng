"""
MySQL/MariaDB Template Engine for high-availability database clusters.

Business Context: Generates production-ready MySQL and MariaDB configurations
including Galera clusters, replication setups, and ProxySQL load balancing.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .base_engine import BaseTemplateEngine, TemplateContext, TemplateResult
from datetime import datetime


@dataclass
class MySQLClusterConfig:
    """Configuration for MySQL/MariaDB cluster setup."""
    cluster_type: str  # galera, replication, ndb
    node_count: int = 3
    engine_type: str = "mariadb"  # mysql, mariadb
    version: str = "10.6"
    enable_ssl: bool = True
    enable_proxy: bool = True
    proxy_type: str = "proxysql"  # proxysql, maxscale, haproxy


class MySQLTemplateEngine(BaseTemplateEngine):
    """
    Template engine for MySQL/MariaDB high-availability setups.
    
    Supports:
    - Galera clusters (MariaDB/MySQL)
    - Master-slave replication
    - MySQL NDB Cluster
    - ProxySQL and MaxScale integration
    """
    
    def __init__(self):
        super().__init__(
            name="mysql",
            technologies=["mysql", "mariadb", "galera", "mysql-cluster", "proxysql", "maxscale"]
        )
    
    def can_handle(self, context: TemplateContext) -> bool:
        """Check if this engine can handle the context."""
        mysql_technologies = {
            'mysql', 'mariadb', 'galera', 'mysql-cluster', 
            'proxysql', 'maxscale', 'mysql-replication'
        }
        
        # Handle both string and list technology inputs
        if isinstance(context.technology, str):
            context_technologies = {context.technology.lower()}
        else:
            context_technologies = {tech.lower() for tech in context.technology}
        
        return bool(mysql_technologies.intersection(context_technologies))
    
    async def generate_template(self, context: TemplateContext) -> TemplateResult:
        """Generate MySQL/MariaDB cluster template."""
        try:
            # Determine cluster configuration from context
            cluster_config = self._determine_cluster_config(context)
            
            # Generate appropriate template based on setup type
            if cluster_config.cluster_type == "galera":
                template_content = await self._generate_galera_template(context, cluster_config)
            elif cluster_config.cluster_type == "replication":
                template_content = await self._generate_replication_template(context, cluster_config)
            elif cluster_config.cluster_type == "ndb":
                template_content = await self._generate_ndb_template(context, cluster_config)
            else:
                template_content = await self._generate_single_instance_template(context, cluster_config)
            
            return TemplateResult(
                content=template_content,
                template_type=f"mysql_{cluster_config.cluster_type}",
                confidence_score=0.85,
                estimated_complexity=self.estimate_complexity(context),
                generated_at=datetime.now(),
                context_hash=self._calculate_context_hash(context)
            )
            
        except Exception as e:
            return TemplateResult(
                content=self._generate_fallback_template(context),
                template_type="mysql_fallback",
                confidence_score=0.4,
                estimated_complexity="simple",
                generated_at=datetime.now(),
                context_hash=self._calculate_context_hash(context)
            )
    
    def _determine_cluster_config(self, context: TemplateContext) -> MySQLClusterConfig:
        """Determine cluster configuration from context."""
        # Handle both string and list technology inputs
        if isinstance(context.technology, str):
            technologies = [context.technology.lower()]
        else:
            technologies = [tech.lower() for tech in context.technology]
        
        # Determine cluster type
        if 'galera' in technologies:
            cluster_type = "galera"
            engine_type = "mariadb"
        elif 'mysql-cluster' in technologies or 'ndb' in technologies:
            cluster_type = "ndb"
            engine_type = "mysql"
        elif 'replication' in context.task_description.lower():
            cluster_type = "replication"
        else:
            cluster_type = "galera"  # Default for HA
        
        # Determine engine type
        if 'mysql' in technologies and 'mariadb' not in technologies:
            engine_type = "mysql"
        else:
            engine_type = "mariadb"  # Default to MariaDB for better features
        
        # Determine node count from context
        node_count = 3  # Default
        if hasattr(context.specific_options, 'cluster_size') and context.specific_options.cluster_size:
            node_count = context.specific_options.cluster_size
        elif 'cluster' in context.task_description.lower():
            # Try to extract number from description
            import re
            match = re.search(r'(\d+)[- ]node', context.task_description.lower())
            if match:
                node_count = int(match.group(1))
        
        return MySQLClusterConfig(
            cluster_type=cluster_type,
            node_count=node_count,
            engine_type=engine_type,
            enable_proxy='proxy' in context.task_description.lower() or len(technologies) > 2
        )
    
    async def _generate_galera_template(self, context: TemplateContext, config: MySQLClusterConfig) -> str:
        """Generate Galera cluster template."""
        return f"""# {config.engine_type.title()} Galera Cluster Setup

## TASK
Deploy: **{config.node_count}-node {config.engine_type.title()} Galera cluster with ProxySQL load balancer**

## EXPECTED OUTPUT EXAMPLE

### Docker Compose Configuration
```yaml
version: '3.8'

services:
  galera-node-1:
    image: {config.engine_type}:{config.version}
    container_name: galera-node-1
    environment:
      MYSQL_ROOT_PASSWORD: secure_root_password
      MYSQL_DATABASE: application_db
      MYSQL_USER: app_user
      MYSQL_PASSWORD: app_password
    command: |
      --wsrep-new-cluster
      --wsrep-on=ON
      --wsrep-provider=/usr/lib/galera/libgalera_smm.so
      --wsrep-cluster-address=gcomm://galera-node-1,galera-node-2,galera-node-3
      --wsrep-cluster-name=galera_cluster
      --wsrep-node-address=galera-node-1
      --wsrep-node-name=node1
      --wsrep-sst-method=rsync
      --innodb-buffer-pool-size=512M
    volumes:
      - galera_data_1:/var/lib/mysql
      - ./galera.cnf:/etc/mysql/conf.d/galera.cnf
    networks:
      galera_network:
        ipv4_address: 172.20.0.10
    ports:
      - "3306:3306"
      - "4567:4567"
      - "4568:4568"
      - "4444:4444"

  galera-node-2:
    image: {config.engine_type}:{config.version}
    container_name: galera-node-2
    environment:
      MYSQL_ROOT_PASSWORD: secure_root_password
      MYSQL_DATABASE: application_db
      MYSQL_USER: app_user
      MYSQL_PASSWORD: app_password
    command: |
      --wsrep-on=ON
      --wsrep-provider=/usr/lib/galera/libgalera_smm.so
      --wsrep-cluster-address=gcomm://galera-node-1,galera-node-2,galera-node-3
      --wsrep-cluster-name=galera_cluster
      --wsrep-node-address=galera-node-2
      --wsrep-node-name=node2
      --wsrep-sst-method=rsync
      --innodb-buffer-pool-size=512M
    volumes:
      - galera_data_2:/var/lib/mysql
      - ./galera.cnf:/etc/mysql/conf.d/galera.cnf
    networks:
      galera_network:
        ipv4_address: 172.20.0.11
    depends_on:
      - galera-node-1

  galera-node-3:
    image: {config.engine_type}:{config.version}
    container_name: galera-node-3
    environment:
      MYSQL_ROOT_PASSWORD: secure_root_password
      MYSQL_DATABASE: application_db
      MYSQL_USER: app_user
      MYSQL_PASSWORD: app_password
    command: |
      --wsrep-on=ON
      --wsrep-provider=/usr/lib/galera/libgalera_smm.so
      --wsrep-cluster-address=gcomm://galera-node-1,galera-node-2,galera-node-3
      --wsrep-cluster-name=galera_cluster
      --wsrep-node-address=galera-node-3
      --wsrep-node-name=node3
      --wsrep-sst-method=rsync
      --innodb-buffer-pool-size=512M
    volumes:
      - galera_data_3:/var/lib/mysql
      - ./galera.cnf:/etc/mysql/conf.d/galera.cnf
    networks:
      galera_network:
        ipv4_address: 172.20.0.12
    depends_on:
      - galera-node-1

  proxysql:
    image: proxysql/proxysql:latest
    container_name: proxysql
    volumes:
      - ./proxysql.cnf:/etc/proxysql.cnf
      - proxysql_data:/var/lib/proxysql
    ports:
      - "6032:6032"  # Admin interface
      - "6033:6033"  # MySQL interface
    networks:
      galera_network:
        ipv4_address: 172.20.0.20
    depends_on:
      - galera-node-1
      - galera-node-2
      - galera-node-3

  monitoring:
    image: prom/prometheus:latest
    container_name: mysql_monitoring
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - galera_network

volumes:
  galera_data_1:
  galera_data_2:
  galera_data_3:
  proxysql_data:
  prometheus_data:

networks:
  galera_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
```

### Galera Configuration (galera.cnf)
```ini
[galera]
# Galera Provider Configuration
wsrep_on=ON
wsrep_provider=/usr/lib/galera/libgalera_smm.so

# Galera Cluster Configuration
wsrep_cluster_name="galera_cluster"
wsrep_cluster_address="gcomm://172.20.0.10,172.20.0.11,172.20.0.12"

# Galera Synchronization Configuration
wsrep_sst_method=rsync

# Galera Node Configuration
wsrep_node_name="node1"
wsrep_node_address="172.20.0.10"

# InnoDB Configuration
innodb_autoinc_lock_mode=2
innodb_locks_unsafe_for_binlog=1

# Performance Tuning
wsrep_slave_threads=4
wsrep_certify_nonPK=1
wsrep_max_ws_rows=0
wsrep_max_ws_size=2G
wsrep_debug=0
wsrep_convert_LOCK_to_trx=0
wsrep_retry_autocommit=1
wsrep_auto_increment_control=1
```

### ProxySQL Configuration (proxysql.cnf)
```ini
datadir="/var/lib/proxysql"

admin_variables={{
    admin_credentials="admin:admin"
    mysql_ifaces="0.0.0.0:6032"
    refresh_interval=2000
}}

mysql_variables={{
    threads=4
    max_connections=2048
    default_query_delay=0
    default_query_timeout=36000000
    have_compress=true
    poll_timeout=2000
    interfaces="0.0.0.0:6033"
    default_schema="information_schema"
    stacksize=1048576
    server_version="5.7.22"
    connect_timeout_server=3000
    monitor_username="monitor"
    monitor_password="monitor"
    monitor_history=600000
    monitor_connect_interval=60000
    monitor_ping_interval=10000
    ping_interval_server_msec=120000
    ping_timeout_server=500
    commands_stats=true
    sessions_sort=true
}}

mysql_servers={{
    {{ address="172.20.0.10", port=3306, hostgroup=0, weight=1000 }},
    {{ address="172.20.0.11", port=3306, hostgroup=0, weight=1000 }},
    {{ address="172.20.0.12", port=3306, hostgroup=0, weight=1000 }}
}}

mysql_users={{
    {{ username = "app_user", password = "app_password", default_hostgroup = 0, max_connections=1000 }}
}}

mysql_query_rules={{
    {{ rule_id=1, match_pattern="^SELECT.*", destination_hostgroup=0, apply=1 }}
}}
```

## REQUIREMENTS
{context.user_requirements or 'Follow best practices and write clean, maintainable code'}

## IMPLEMENTATION STEPS

1. **Prepare Environment**
   - Create network configuration for cluster communication
   - Set up persistent volumes for database data
   - Configure firewall rules for Galera ports (3306, 4567, 4568, 4444)

2. **Deploy Galera Cluster**
   - Start first node with --wsrep-new-cluster
   - Bootstrap remaining nodes sequentially
   - Verify cluster status with SHOW STATUS LIKE 'wsrep%'

3. **Configure Load Balancer**
   - Deploy ProxySQL with cluster node configuration
   - Set up health checks and failover rules
   - Configure read/write split if needed

4. **Security Hardening**
   - Change default passwords and remove test accounts
   - Configure SSL/TLS for cluster communication
   - Set up proper user permissions and access controls

5. **Monitoring Setup**
   - Deploy monitoring stack (Prometheus + Grafana)
   - Configure alerts for cluster health and performance
   - Set up log aggregation for troubleshooting

## PRODUCTION CHECKLIST

### Security
- [ ] All default passwords changed
- [ ] SSL/TLS enabled for client and cluster communication
- [ ] Firewall configured with minimal required ports
- [ ] User accounts follow principle of least privilege

### High Availability
- [ ] Minimum 3 nodes for proper quorum
- [ ] Automatic failover configured in ProxySQL
- [ ] Split-brain protection mechanisms in place
- [ ] Backup and recovery procedures tested

### Performance
- [ ] InnoDB buffer pool sized appropriately (70% of RAM)
- [ ] Connection pooling configured in ProxySQL
- [ ] Query performance monitoring enabled
- [ ] Index optimization completed

### Monitoring
- [ ] Cluster health metrics tracked
- [ ] Alerting configured for critical issues
- [ ] Log rotation and retention policies set
- [ ] Performance baselines established

## OPERATIONAL COMMANDS

```bash
# Check cluster status
docker exec galera-node-1 mysql -e "SHOW STATUS LIKE 'wsrep%'"

# Monitor cluster size
docker exec galera-node-1 mysql -e "SHOW STATUS LIKE 'wsrep_cluster_size'"

# ProxySQL admin interface
mysql -h 127.0.0.1 -P 6032 -u admin -padmin

# Backup cluster
docker exec galera-node-1 mariabackup --backup --galera-info --user=root --password=secure_root_password --target-dir=/backup

# Restore from backup
docker exec galera-node-1 mariabackup --prepare --target-dir=/backup
docker exec galera-node-1 mariabackup --copy-back --target-dir=/backup
```

Deploy this {config.engine_type.title()} Galera cluster ensuring high availability, security, and monitoring capabilities."""
    
    async def _generate_replication_template(self, context: TemplateContext, config: MySQLClusterConfig) -> str:
        """Generate MySQL replication template."""
        return f"""# {config.engine_type.title()} Master-Slave Replication Setup

## TASK
Deploy: **{config.engine_type.title()} master-slave replication with {config.node_count} nodes**

## EXPECTED OUTPUT EXAMPLE

### Docker Compose Configuration
```yaml
version: '3.8'

services:
  mysql-master:
    image: {config.engine_type}:{config.version}
    container_name: mysql-master
    environment:
      MYSQL_ROOT_PASSWORD: secure_root_password
      MYSQL_REPLICATION_USER: replicator
      MYSQL_REPLICATION_PASSWORD: replicator_password
    command: |
      --server-id=1
      --log-bin=mysql-bin
      --binlog-format=ROW
      --gtid-mode=ON
      --enforce-gtid-consistency=ON
    volumes:
      - master_data:/var/lib/mysql
    ports:
      - "3306:3306"
    networks:
      - mysql_replication

  mysql-slave-1:
    image: {config.engine_type}:{config.version}
    container_name: mysql-slave-1
    environment:
      MYSQL_ROOT_PASSWORD: secure_root_password
    command: |
      --server-id=2
      --relay-log=mysql-relay-bin
      --log-slave-updates=1
      --read-only=1
      --gtid-mode=ON
      --enforce-gtid-consistency=ON
    volumes:
      - slave1_data:/var/lib/mysql
    ports:
      - "3307:3306"
    networks:
      - mysql_replication
    depends_on:
      - mysql-master

volumes:
  master_data:
  slave1_data:

networks:
  mysql_replication:
    driver: bridge
```

## REQUIREMENTS
{context.user_requirements or 'Follow best practices and write clean, maintainable code'}

Deploy this {config.engine_type.title()} replication setup with automated failover capabilities."""

    async def _generate_ndb_template(self, context: TemplateContext, config: MySQLClusterConfig) -> str:
        """Generate MySQL NDB Cluster template."""
        return f"""# MySQL NDB Cluster Setup

## TASK
Deploy: **MySQL NDB Cluster with {config.node_count} data nodes**

## EXPECTED OUTPUT EXAMPLE

### Docker Compose Configuration
```yaml
version: '3.8'

services:
  ndb-mgmd:
    image: mysql/mysql-cluster:latest
    container_name: ndb-mgmd
    command: ndb_mgmd --initial --configdir=/var/lib/mysql-cluster
    volumes:
      - ./ndb_mgmd.cnf:/var/lib/mysql-cluster/config.ini
    networks:
      - ndb_cluster
    ports:
      - "1186:1186"

  ndb-data-1:
    image: mysql/mysql-cluster:latest
    container_name: ndb-data-1
    command: ndbd
    networks:
      - ndb_cluster
    depends_on:
      - ndb-mgmd

  ndb-data-2:
    image: mysql/mysql-cluster:latest
    container_name: ndb-data-2
    command: ndbd
    networks:
      - ndb_cluster
    depends_on:
      - ndb-mgmd

  mysql-server:
    image: mysql/mysql-cluster:latest
    container_name: mysql-server
    command: mysqld
    environment:
      MYSQL_ROOT_PASSWORD: secure_root_password
    ports:
      - "3306:3306"
    networks:
      - ndb_cluster
    depends_on:
      - ndb-mgmd
      - ndb-data-1
      - ndb-data-2

networks:
  ndb_cluster:
    driver: bridge
```

## REQUIREMENTS
{context.user_requirements or 'Follow best practices and write clean, maintainable code'}

Deploy this MySQL NDB Cluster for distributed computing and high availability."""

    async def _generate_single_instance_template(self, context: TemplateContext, config: MySQLClusterConfig) -> str:
        """Generate single MySQL instance template."""
        return f"""# {config.engine_type.title()} Single Instance Setup

## TASK
Deploy: **{config.engine_type.title()} single instance with monitoring**

## EXPECTED OUTPUT EXAMPLE

### Docker Compose Configuration
```yaml
version: '3.8'

services:
  database:
    image: {config.engine_type}:{config.version}
    container_name: {config.engine_type}-db
    environment:
      MYSQL_ROOT_PASSWORD: secure_root_password
      MYSQL_DATABASE: application_db
      MYSQL_USER: app_user
      MYSQL_PASSWORD: app_password
    volumes:
      - db_data:/var/lib/mysql
      - ./my.cnf:/etc/mysql/conf.d/my.cnf
    ports:
      - "3306:3306"
    networks:
      - app_network

volumes:
  db_data:

networks:
  app_network:
    driver: bridge
```

## REQUIREMENTS
{context.user_requirements or 'Follow best practices and write clean, maintainable code'}

Deploy this {config.engine_type.title()} instance with proper security and backup procedures."""
    
    def _generate_fallback_template(self, context: TemplateContext) -> str:
        """Generate fallback template for MySQL/MariaDB."""
        return f"""# MySQL/MariaDB Database Setup

## TASK
Implement: **MySQL/MariaDB database solution**

## EXPECTED OUTPUT EXAMPLE
```yaml
version: '3.8'
services:
  database:
    image: mariadb:10.6
    environment:
      MYSQL_ROOT_PASSWORD: secure_password
      MYSQL_DATABASE: app_db
    volumes:
      - db_data:/var/lib/mysql
    ports:
      - "3306:3306"

volumes:
  db_data:
```

## REQUIREMENTS
{context.user_requirements or 'Follow best practices and write clean, maintainable code'}

## IMPLEMENTATION STEPS
1. Configure database with proper security settings
2. Set up backup and recovery procedures
3. Implement monitoring and alerting
4. Optimize for production performance

Please implement MySQL/MariaDB following best practices for security and performance."""