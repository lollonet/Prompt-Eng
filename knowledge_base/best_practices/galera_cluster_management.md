# Galera Cluster Management

## Cluster Architecture
- Minimum 3 nodes for proper quorum
- Odd number of nodes to prevent split-brain
- All nodes are masters (multi-master replication)
- Synchronous replication ensures data consistency

## Configuration Best Practices
```ini
# Essential Galera settings
wsrep_slave_threads=4
wsrep_retry_autocommit=3
wsrep_max_ws_size=1G
innodb_autoinc_lock_mode=2
innodb_locks_unsafe_for_binlog=1
```

## Monitoring and Maintenance
- Monitor wsrep_cluster_size and wsrep_cluster_status
- Check wsrep_ready and wsrep_connected status
- Monitor replication lag with wsrep_local_recv_queue
- Implement automated node recovery procedures

## Split-Brain Prevention
- Use proper network architecture (multiple network paths)
- Configure pc.weight for weighted quorum
- Implement fencing mechanisms
- Monitor network connectivity between nodes

## Performance Optimization
- Tune wsrep_slave_threads based on workload
- Configure appropriate certification interval
- Use parallel applying for better throughput
- Optimize network settings for cluster communication

## Backup in Galera Environment
- Use mariabackup with --galera-info
- Implement consistent backup across cluster
- Test cluster recovery from backup
- Document emergency recovery procedures