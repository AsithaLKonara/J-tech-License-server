# 🚀 Deployment Guide

**Upload Bridge - Production Deployment Procedures**

This guide provides step-by-step instructions for deploying Upload Bridge to production environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Verification](#verification)
5. [Rollback](#rollback)
6. [Updates](#updates)

---

## Prerequisites

### System Requirements

- **Operating System**: Windows 10+, Linux, macOS
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Disk Space**: 500MB for application + logs
- **Dependencies**: See `requirements.txt`

### Pre-Deployment Checklist

- [ ] Python 3.8+ installed
- [ ] System dependencies installed
- [ ] Network access (if needed)
- [ ] File permissions configured
- [ ] Backup of previous version (if upgrading)

---

## Installation

### Step 1: Prepare Environment

1. **Create Application Directory**
   ```bash
   mkdir -p /opt/upload_bridge
   cd /opt/upload_bridge
   ```

2. **Set Up Python Environment** (Optional but recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

### Step 2: Install Application

1. **Clone or Copy Application**
   ```bash
   # Option 1: Git clone
   git clone <repository-url> .
   
   # Option 2: Copy files
   cp -r /path/to/upload_bridge/* .
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Installation**
   ```bash
   python main.py --version  # If version flag exists
   # Or just verify imports
   python -c "from ui.main_window import UploadBridgeMainWindow; print('OK')"
   ```

### Step 3: Create Directories

```bash
# Create necessary directories
mkdir -p logs
mkdir -p config
mkdir -p data  # If needed

# Set permissions
chmod 755 logs
chmod 755 config
```

---

## Configuration

### Step 1: Environment Configuration

1. **Set Environment Variable**
   ```bash
   # Linux/Mac
   export ENVIRONMENT=production
   
   # Windows
   set ENVIRONMENT=production
   
   # Or add to system environment variables
   ```

2. **Create Configuration File**
   ```bash
   # Copy template
   cp config/production.json.template config/production.json
   
   # Edit configuration
   nano config/production.json  # or use your editor
   ```

### Step 2: Configure Logging

1. **Log Configuration**
   ```json
   {
     "log_level": "INFO",
     "log_to_file": true,
     "log_to_console": false,
     "log_json": false,
     "log_dir": "/var/log/upload_bridge"
   }
   ```

2. **Environment Variables**
   ```bash
   export LOG_LEVEL=INFO
   export LOG_TO_FILE=true
   export LOG_TO_CONSOLE=false
   export LOG_DIR=/var/log/upload_bridge
   ```

### Step 3: Application Configuration

1. **Application Settings**
   ```json
   {
     "app_name": "Upload Bridge",
     "app_version": "1.0.0",
     "debug": false,
     "max_pattern_size": 1000000,
     "cache_size": 100
   }
   ```

2. **Feature Flags**
   ```json
   {
     "enable_analytics": false,
     "enable_telemetry": false
   }
   ```

### Step 4: Security Configuration

1. **Secrets Management**
   - Store secrets in environment variables
   - Use secure secret management system
   - Never commit secrets to repository

2. **File Permissions**
   ```bash
   # Application files
   chmod 755 /opt/upload_bridge
   chmod 644 /opt/upload_bridge/*.py
   
   # Configuration
   chmod 600 config/production.json  # If contains secrets
   
   # Logs
   chmod 755 logs
   ```

---

## Verification

### Step 1: Health Check

1. **Run Health Check**
   ```python
   from core.health import get_health_checker
   
   health_checker = get_health_checker()
   status = health_checker.check_health()
   print(status)
   ```

2. **Verify Status**
   - All checks should be "healthy"
   - Resource usage within limits
   - No critical errors

### Step 2: Functional Testing

1. **Start Application**
   ```bash
   ENVIRONMENT=production python main.py
   ```

2. **Test Key Operations**
   - Load a pattern
   - Save a pattern
   - Export a pattern
   - Build firmware (if applicable)
   - Upload firmware (if applicable)

3. **Verify Logs**
   ```bash
   # Check for errors
   tail -50 logs/errors.log
   
   # Check application log
   tail -50 logs/application.log
   ```

### Step 3: Performance Verification

1. **Check Performance**
   - Monitor startup time
   - Check operation times
   - Verify resource usage

2. **Load Testing** (if applicable)
   - Test with typical workloads
   - Monitor resource usage
   - Check for performance degradation

---

## Rollback

### Rollback Procedure

1. **Stop Application**
   ```bash
   # Graceful shutdown (if possible)
   # Or kill process
   pkill -f "python main.py"
   ```

2. **Restore Previous Version**
   ```bash
   # Option 1: Git rollback
   git checkout <previous-version>
   
   # Option 2: Restore from backup
   tar -xzf app_backup_YYYYMMDD.tar.gz
   ```

3. **Restore Configuration**
   ```bash
   # Restore config backup
   cp config_backup_YYYYMMDD.json config/production.json
   ```

4. **Reinstall Dependencies** (if needed)
   ```bash
   pip install -r requirements.txt
   ```

5. **Restart Application**
   ```bash
   ENVIRONMENT=production python main.py
   ```

6. **Verify Rollback**
   - Run health check
   - Test key operations
   - Check logs

---

## Updates

### Update Procedure

1. **Backup Current Version**
   ```bash
   # Backup application
   tar -czf app_backup_$(date +%Y%m%d).tar.gz \
     --exclude='*.pyc' \
     --exclude='__pycache__' \
     --exclude='.git' \
     .
   
   # Backup configuration
   cp config/production.json config/production.json.backup
   ```

2. **Update Application**
   ```bash
   # Option 1: Git pull
   git pull origin main
   
   # Option 2: Copy new files
   cp -r /path/to/new/version/* .
   ```

3. **Update Dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

4. **Verify Configuration**
   - Check configuration compatibility
   - Update configuration if needed
   - Test configuration

5. **Restart Application**
   ```bash
   # Stop application
   pkill -f "python main.py"
   
   # Start application
   ENVIRONMENT=production python main.py
   ```

6. **Verify Update**
   - Run health check
   - Test key operations
   - Monitor for errors
   - Check logs

### Rollback from Update

If update causes issues:
1. Follow [Rollback Procedure](#rollback)
2. Report issue with details
3. Wait for fix before retrying

---

## Service Management

### Systemd Service (Linux)

1. **Create Service File**
   ```ini
   # /etc/systemd/system/upload-bridge.service
   [Unit]
   Description=Upload Bridge Application
   After=network.target
   
   [Service]
   Type=simple
   User=upload_bridge
   WorkingDirectory=/opt/upload_bridge
   Environment="ENVIRONMENT=production"
   Environment="LOG_LEVEL=INFO"
   ExecStart=/usr/bin/python3 /opt/upload_bridge/main.py
   Restart=on-failure
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable upload-bridge
   sudo systemctl start upload-bridge
   ```

3. **Service Management**
   ```bash
   # Start
   sudo systemctl start upload-bridge
   
   # Stop
   sudo systemctl stop upload-bridge
   
   # Restart
   sudo systemctl restart upload-bridge
   
   # Status
   sudo systemctl status upload-bridge
   
   # Logs
   sudo journalctl -u upload-bridge -f
   ```

### Windows Service

1. **Use NSSM** (Non-Sucking Service Manager)
   ```bash
   # Install service
   nssm install UploadBridge "C:\Python\python.exe" "C:\upload_bridge\main.py"
   
   # Set environment variables
   nssm set UploadBridge AppEnvironmentExtra ENVIRONMENT=production
   nssm set UploadBridge AppEnvironmentExtra LOG_LEVEL=INFO
   
   # Start service
   nssm start UploadBridge
   ```

---

## Monitoring Setup

### Log Monitoring

1. **Configure Log Rotation**
   - Automatic rotation at 10MB
   - 5 backup files retained
   - Archive old logs

2. **Set Up Log Aggregation** (Optional)
   - Use log aggregation tool (ELK, Splunk, etc.)
   - Configure log shipping
   - Set up alerts

### Health Monitoring

1. **Health Check Endpoint** (if implemented)
   - Set up monitoring to call health check
   - Configure alerts for unhealthy status
   - Monitor resource usage

2. **Alerting**
   - Set up alerts for errors
   - Configure resource thresholds
   - Set up notification channels

---

## Post-Deployment

### Immediate Tasks

1. **Verify Deployment**
   - Run health check
   - Test key operations
   - Check logs

2. **Monitor**
   - Watch logs for errors
   - Monitor resource usage
   - Check performance

3. **Document**
   - Document deployment date
   - Note any issues
   - Update runbook if needed

### Ongoing Maintenance

1. **Regular Checks**
   - Daily: Review error logs
   - Weekly: Check performance
   - Monthly: Review configuration

2. **Updates**
   - Monitor for updates
   - Test updates in staging
   - Deploy updates following procedure

---

## Troubleshooting Deployment

### Common Issues

1. **Import Errors**
   - Verify dependencies installed
   - Check Python path
   - Verify file permissions

2. **Configuration Errors**
   - Check JSON syntax
   - Verify environment variables
   - Check file permissions

3. **Permission Issues**
   - Check file permissions
   - Verify user permissions
   - Check directory permissions

See [Troubleshooting Guide](TROUBLESHOOTING.md) for more details.

---

*Deployment Guide - Updated: 2024*

