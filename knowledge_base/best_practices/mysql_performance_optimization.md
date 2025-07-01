# MySQL Performance Optimization

## Query Optimization
- Use appropriate indexes for frequently queried columns
- Avoid SELECT * and only fetch required columns
- Use EXPLAIN to analyze query execution plans
- Optimize WHERE clauses and avoid functions on columns

## Configuration Tuning
```sql
-- Key MySQL performance settings
innodb_buffer_pool_size = 70% of available RAM
innodb_log_file_size = 256M
query_cache_size = 128M
max_connections = 100-200
```

## Index Strategy
- Create composite indexes for multi-column queries
- Use covering indexes to avoid key lookups
- Monitor index usage with SHOW INDEX and sys schema
- Remove unused indexes to improve write performance

## Storage Engine Optimization
- Use InnoDB for transactional workloads
- Configure appropriate page size (16KB default)
- Enable compression for large tables
- Use partitioning for very large tables

## Monitoring and Maintenance
- Regular ANALYZE TABLE and OPTIMIZE TABLE
- Monitor slow query log
- Use Performance Schema for detailed analysis
- Implement automated backup and recovery procedures