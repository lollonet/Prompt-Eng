# MariaDB Best Practices

## High Availability Architecture
- Implement Master-Slave or Master-Master replication
- Use Galera Cluster for synchronous multi-master replication
- Configure automatic failover with MaxScale or HAProxy
- Implement proper backup and point-in-time recovery

## Security Configuration
```sql
-- Security hardening
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
FLUSH PRIVILEGES;
```

## Performance Optimization
- Configure appropriate InnoDB settings for workload
- Use MariaDB's advanced features like virtual columns
- Implement connection pooling with MaxScale
- Monitor with Performance Schema and sys schema

## Galera Cluster Setup
```ini
[galera]
wsrep_on=ON
wsrep_provider=/usr/lib64/galera/libgalera_smm.so
wsrep_cluster_address="gcomm://node1,node2,node3"
wsrep_cluster_name='mariadb_cluster'
wsrep_node_address='10.0.0.1'
wsrep_node_name='node1'
```

## Backup Strategy
- Implement automated backups with mariabackup
- Use binary log shipping for point-in-time recovery
- Test restore procedures regularly
- Consider cross-datacenter backup replication