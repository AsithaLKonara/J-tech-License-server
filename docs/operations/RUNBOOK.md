# 📘 Operations Runbook

**Upload Bridge - Production Operations Guide**

This runbook provides step-by-step procedures for operating Upload Bridge in production environments.

---

## Table of Contents

1. [Startup Procedures](#startup-procedures)
2. [Monitoring](#monitoring)
3. [Health Checks](#health-checks)
4. [Troubleshooting](#troubleshooting)
5. [Maintenance](#maintenance)
6. [Backup & Recovery](#backup--recovery)
7. [Incident Response](#incident-response)

---

## Startup Procedures

### Application Startup

1. **Check Prerequisites**
   ```bash
   # Verify Python version (3.8+)
   python --version
   
   # Verify dependencies
   pip install -r requirements.txt
   
   # Verify environment variables (if set)
   echo $ENVIRONMENT
   echo $LOG_LEVEL
   ```

2. **Start Application**
   ```bash
   # Development
   python main.py
   
   # Production (with logging)
   ENVIRONMENT=production LOG_LEVEL=INFO python main.py
   
   # With custom log directory
   LOG_DIR=/var/log/upload_bridge python main.py
   ```

3. **Verify Startup**
   - Check application logs: `logs/application.log`
   - Check for errors: `logs/errors.log`
   - Verify health check: See [Health Checks](#health-checks)

### Configuration

1. **Environment Configuration**
   - Set `ENVIRONMENT` variable: `development`, `staging`, or `production`
   - Configure logging: `LOG_LEVEL`, `LOG_TO_FILE`, `LOG_TO_CONSOLE`
   - Set application settings: `MAX_PATTERN_SIZE`, `CACHE_SIZE`

2. **Configuration Files**
   - Development: `config/development.json`
   - Staging: `config/staging.json`
   - Production: `config/production.json`

---

## Monitoring

### Log Monitoring

1. **Application Logs**
   ```bash
   # View application log
   tail -f logs/application.log
   
   # View errors only
   tail -f logs/errors.log
   
   # View audit trail
   tail -f logs/audit.log
   ```

2. **Log Levels**
   - `DEBUG`: Detailed diagnostic information
   - `INFO`: General informational messages
   - `WARNING`: Warning messages
   - `ERROR`: Error messages
   - `CRITICAL`: Critical errors

3. **Log Rotation**
   - Logs rotate automatically at 10MB
   - 5 backup files retained
   - Location: `logs/` directory

### Performance Monitoring

1. **Performance Metrics**
   - Performance logs in `logs/application.log`
   - Look for `Performance:` entries
   - Monitor operation durations

2. **System Resources**
   - Use health check API (see below)
   - Monitor memory, CPU, disk usage
   - Set up alerts for resource thresholds

---

## Health Checks

### Manual Health Check

1. **Using Python**
   ```python
   from core.health import get_health_checker
   
   health_checker = get_health_checker()
   status = health_checker.check_health()
   print(status)
   ```

2. **Health Check Results**
   ```json
   {
     "status": "healthy" | "degraded" | "unhealthy",
     "timestamp": "2024-01-01T12:00:00",
     "checks": {
       "application": {
         "status": "healthy",
         "message": "Application is running"
       },
       "memory": {
         "status": "healthy",
         "percent_used": 45.2,
         "total_gb": 16.0,
         "available_gb": 8.8
       },
       "disk": {
         "status": "healthy",
         "percent_used": 60.5,
         "total_gb": 500.0,
         "free_gb": 197.5
       },
       "cpu": {
         "status": "healthy",
         "percent_used": 25.3,
         "cpu_count": 8
       }
     }
   }
   ```

3. **Health Status Interpretation**
   - **healthy**: All systems operational
   - **degraded**: Some systems have issues but application is functional
   - **unhealthy**: Critical issues, application may not function correctly

### Automated Health Monitoring

1. **Set Up Monitoring**
   - Configure monitoring tool to call health check
   - Set up alerts for `unhealthy` status
   - Monitor resource usage trends

2. **Alert Thresholds**
   - Memory usage > 90%: Critical
   - Memory usage > 75%: Warning
   - Disk usage > 90%: Critical
   - Disk usage > 80%: Warning
   - CPU usage > 90%: Warning

---

## Troubleshooting

### Common Issues

1. **Application Won't Start**
   - Check Python version: `python --version`
   - Verify dependencies: `pip install -r requirements.txt`
   - Check logs: `logs/errors.log`
   - Verify file permissions

2. **High Memory Usage**
   - Check health status
   - Review large pattern files
   - Reduce `CACHE_SIZE` if needed
   - Restart application

3. **Disk Space Issues**
   - Check log file sizes: `du -sh logs/`
   - Rotate or archive old logs
   - Clean up temporary files
   - Increase disk space

4. **Performance Issues**
   - Check performance logs
   - Review slow operations
   - Optimize pattern sizes
   - Check system resources

### Log Analysis

1. **Error Analysis**
   ```bash
   # Count errors by type
   grep ERROR logs/application.log | sort | uniq -c
   
   # Find recent errors
   grep ERROR logs/application.log | tail -20
   
   # Search for specific error
   grep "pattern_load" logs/application.log
   ```

2. **Performance Analysis**
   ```bash
   # Find slow operations
   grep "Performance:" logs/application.log | grep -E "[0-9]{4,}\.ms"
   
   # Average operation times
   grep "Performance:" logs/application.log | awk '{print $NF}' | awk -F'ms' '{print $1}' | awk '{sum+=$1; count++} END {print sum/count}'
   ```

---

## Maintenance

### Regular Maintenance Tasks

1. **Daily**
   - Review error logs
   - Check health status
   - Monitor disk space

2. **Weekly**
   - Review audit logs
   - Analyze performance metrics
   - Check for dependency updates

3. **Monthly**
   - Archive old logs
   - Review security logs
   - Update dependencies (if needed)
   - Review configuration

### Log Management

1. **Log Rotation**
   - Automatic rotation at 10MB
   - Manual rotation: Archive old logs
   - Retention: 5 backup files

2. **Log Archival**
   ```bash
   # Archive logs older than 30 days
   find logs/ -name "*.log.*" -mtime +30 -exec tar -czf logs_archive_$(date +%Y%m%d).tar.gz {} \;
   
   # Remove archived logs
   find logs/ -name "*.log.*" -mtime +30 -delete
   ```

### Configuration Updates

1. **Update Configuration**
   - Edit configuration file
   - Restart application
   - Verify changes in logs

2. **Hot Reload** (if supported)
   ```python
   from core.config import get_config
   
   config = get_config()
   config.reload()
   ```

---

## Backup & Recovery

### Backup Procedures

1. **Configuration Backup**
   ```bash
   # Backup configuration
   tar -czf config_backup_$(date +%Y%m%d).tar.gz config/
   ```

2. **Log Backup**
   ```bash
   # Backup logs
   tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
   ```

3. **Application Backup**
   ```bash
   # Full application backup
   tar -czf app_backup_$(date +%Y%m%d).tar.gz \
     --exclude='*.pyc' \
     --exclude='__pycache__' \
     --exclude='.git' \
     .
   ```

### Recovery Procedures

1. **Configuration Recovery**
   ```bash
   # Restore configuration
   tar -xzf config_backup_YYYYMMDD.tar.gz
   ```

2. **Application Recovery**
   ```bash
   # Restore application
   tar -xzf app_backup_YYYYMMDD.tar.gz
   pip install -r requirements.txt
   ```

3. **Verification**
   - Run health check
   - Verify logs
   - Test key operations

---

## Incident Response

### Incident Classification

1. **Critical** (P1)
   - Application completely unavailable
   - Data loss or corruption
   - Security breach

2. **High** (P2)
   - Major feature unavailable
   - Performance degradation
   - Partial data loss

3. **Medium** (P3)
   - Minor feature issues
   - Minor performance issues
   - Non-critical errors

4. **Low** (P4)
   - Cosmetic issues
   - Documentation issues
   - Enhancement requests

### Incident Response Steps

1. **Immediate Actions**
   - Assess severity
   - Check health status
   - Review error logs
   - Notify stakeholders

2. **Investigation**
   - Gather logs
   - Reproduce issue
   - Identify root cause
   - Document findings

3. **Resolution**
   - Implement fix
   - Test solution
   - Deploy fix
   - Verify resolution

4. **Post-Incident**
   - Document incident
   - Update runbook
   - Review lessons learned
   - Implement improvements

### Emergency Procedures

1. **Application Restart**
   ```bash
   # Graceful shutdown (if possible)
   # Then restart
   python main.py
   ```

2. **Rollback**
   ```bash
   # Restore previous version
   git checkout <previous-version>
   pip install -r requirements.txt
   python main.py
   ```

3. **Emergency Configuration**
   ```bash
   # Use minimal configuration
   ENVIRONMENT=production LOG_LEVEL=ERROR python main.py
   ```

---

## Contact & Support

### Support Channels

- **Documentation**: `docs/`
- **Troubleshooting Guide**: `docs/operations/TROUBLESHOOTING.md`
- **Security Issues**: See `docs/SECURITY.md`

### Escalation

1. Check documentation
2. Review logs
3. Consult troubleshooting guide
4. Escalate to development team

---

*Operations Runbook - Updated: 2024*

