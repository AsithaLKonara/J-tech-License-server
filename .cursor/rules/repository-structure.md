# Repository Structure Documentation

## Overview

This project uses a **dual-repository structure** to separate concerns:

- **Main Repository**: Contains the core upload-bridge application
- **License Server Repository**: Contains the web-dashboard for Railway deployment

## Repository Details

### Main Repository

- **Name**: J-Tech-Pixel-LED---Upload-Bridge
- **Remote URL**: https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge.git
- **Remote Alias**: origin
- **Location**: Root directory (C:\Users\asith\Documents\upload_bridge)
- **Contains**:
  - Root project files
  - pps/upload-bridge/ directory
  - All other project files
  - **EXCLUDES**: pps/web-dashboard/ (ignored via .gitignore)

### License Server Repository

- **Name**: J-tech-License-server
- **Remote URL**: https://github.com/AsithaLKonara/J-tech-License-server.git
- **Remote Alias**: origin
- **Location**: pps/web-dashboard/ (has its own .git directory)
- **Contains**: Only the pps/web-dashboard/ directory contents
- **Purpose**: Railway deployment for the license server web dashboard

## Critical Rules

### 1. Never Commit web-dashboard to Main Repository

- The pps/web-dashboard/ directory is explicitly ignored in the main repository's .gitignore
- If you need to work on web-dashboard, navigate to pps/web-dashboard/ and work within that repository
- Always verify that .gitignore contains pps/web-dashboard/ before committing to the main repository

### 2. Never Remove the Ignore Rule

- The .gitignore entry pps/web-dashboard/ must NEVER be removed
- Removing this would break the repository separation
- This rule is protected by cursor rules to prevent accidental changes

### 3. Repository Structure Must Never Change

- Do not modify the dual-repository setup
- Do not merge the repositories
- Do not change remote URLs without explicit approval
- The structure is intentional and serves a specific purpose (Railway deployment)

## Workflow Guidelines

### Working on Main Repository

1. Ensure you're in the root directory
2. Make changes to files outside pps/web-dashboard/
3. Stage and commit changes: git add . then git commit -m "message"
4. Push to main repository: git push origin <branch>

### Working on Web-Dashboard Repository

1. Navigate to pps/web-dashboard/ directory
2. Make changes within that directory
3. Stage and commit changes: git add . then git commit -m "message"
4. Push to license-server repository: git push origin <branch>

### Before Every Commit

- **Main Repository**: Verify you're in the root directory and pps/web-dashboard/ is not being tracked
- **Web-Dashboard Repository**: Verify you're in pps/web-dashboard/ directory

### Before Every Push

- **Main Repository**: Verify you're pushing to origin (main repository)
- **Web-Dashboard Repository**: Verify you're pushing to origin (license-server repository)

## File Locations

- Main repository .gitignore: Root directory (contains pps/web-dashboard/ ignore)
- Web-dashboard repository: pps/web-dashboard/.git/
- Cursor rules: 
  - Root .cursorrules (quick reference)
  - .cursor/rules/repository-structure.md (this file - detailed documentation)

## Troubleshooting

### If web-dashboard appears in main repository status

1. Check that .gitignore contains pps/web-dashboard/
2. If the directory was previously tracked, use: git rm --cached -r apps/web-dashboard/
3. Commit the .gitignore change

### If you accidentally committed web-dashboard to main repo

1. Remove from tracking: git rm --cached -r apps/web-dashboard/
2. Ensure .gitignore has the entry
3. Commit the fix
4. Push the correction

### If web-dashboard repository is missing

1. Navigate to pps/web-dashboard/
2. Initialize: git init
3. Add remote: git remote add origin https://github.com/AsithaLKonara/J-tech-License-server.git
4. Add files and commit

## Maintenance

- Periodically verify that both repositories are correctly configured
- Ensure cursor rules are up to date
- Document any changes to the repository structure (if approved)
