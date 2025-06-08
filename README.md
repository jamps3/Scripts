# SSH Management PowerShell Scripts

This repository contains PowerShell scripts for SSH connection management and server migration tasks.

## Add-SSHHost.ps1 - SSH Connection Setup

PowerShell script to create a passwordless SSH login.

Script asks for:
```
user
hostname
port(optional)
```
it creates a SSH key (if it doesn't exist yet) and an alias (ssh *user*) for effortless SSH login.

## Migrate-Server.ps1 - Server Migration Tool

Comprehensive PowerShell script that migrates all data from one SSH server to another using rsync.

### Key Features:

1. **Comprehensive Migration**: Copies all essential server components:
   - System configuration (`/etc/`) - excluding server-specific files like fstab, hostname, hosts
   - User home directories (`/home/`)
   - Root home directory (`/root/`)
   - Web server data (`/var/www/`)
   - Nginx logs and configuration
   - Local applications (`/usr/local/`)
   - Optional software (`/opt/`)
   - Application data (`/var/lib/`) - excluding Docker containers

2. **Safety Features**:
   - Pre-flight checks for rsync availability and SSH connectivity
   - Dry-run mode to test before actual migration
   - Excludes potentially problematic files (fstab, hostname, Docker containers)
   - Progress reporting and error handling

3. **Usage Options**:
   ```powershell
   # Basic usage (dry run first recommended)
   .\Migrate-Server.ps1 -DryRun
   
   # Actual migration
   .\Migrate-Server.ps1
   
   # With custom parameters
   .\Migrate-Server.ps1 -SourceServer "source-server" -DestServer "dest-server" -SSHUser "root" -Verbose
   ```

### Prerequisites:

1. **rsync**: Must be available (through WSL, Cygwin, or native Windows rsync)
2. **SSH Keys**: Set up passwordless SSH authentication between your machine and both servers
3. **Network Access**: Both servers must be accessible via SSH

### Usage:

1. **Test first** (recommended):
   ```powershell
   .\Migrate-Server.ps1 -DryRun
   ```

2. **Run the actual migration**:
   ```powershell
   .\Migrate-Server.ps1
   ```

The script includes comprehensive error handling, progress reporting, and post-migration recommendations. It will automatically test connectivity before starting and provide a detailed summary of all operations.
