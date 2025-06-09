# SSH Management PowerShell Scripts

This repository contains PowerShell scripts for SSH connection management and server migration tasks.

## Add-SSHHost.ps1 - SSH Connection Setup

PowerShell script to create a passwordless SSH login.

Script asks for:
```
user
hostname
port(optional)
alias
```
it creates a SSH key (if it doesn't exist yet) and an alias (ssh *alias*) for effortless SSH login.

```
./Add-SSHHost.ps1
=== SSH Host Manager ===
1. List SSH hosts
2. Add new SSH host
3. Remove SSH host
4. Exit
========================
Please select an option: 1

=== Configured SSH Hosts ===
Alias           Hostname                  User            Port    
-----------------------------------------------------------------
user            1.2.3.4                   user            22      
boss            123.123.123.123           root            22      

Total hosts: 3
Use 'ssh <alias>' to connect to any host.


Press any key to continue...
=== SSH Host Manager ===
1. List SSH hosts
2. Add new SSH host
3. Remove SSH host
4. Exit
========================
Please select an option: 2

=== Add New SSH Host ===
Enter the username for SSH connection: user
Enter the hostname or IP address of the SSH server: user.inter.net
Enter the port number (press Enter for default port 22): 
Enter an alias for this SSH connection (will be used as 'ssh <alias>'): userinter
Do you want to copy your public key to user.inter.net for passwordless login? (Y/N): Y
Copying public key to user.inter.net...
Please enter the password for user@user.inter.net
The authenticity of host 'user.inter.net (1.2.3.4)' can't be established.
ED25519 key fingerprint is SHA256:zGasdfrF/nhLKs0QM4asdfUFFSDlasdf9ov/nwasdfA.
This host key is known by the following other names/addresses:
    C:\Users\user/.ssh/known_hosts:2: 1.2.3.4
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added 'user.inter.net' (ED25519) to the list of known hosts.
Public key copied successfully! Passwordless login should now work.
Successfully added new SSH host entry for 'userinter'

=== SSH Connection Details ===
Alias:    userinter
Hostname: user.inter.net
Username: user
Port:     22
Key File: C:\Users\user\.ssh\id_ed25519
============================

✓ Passwordless login configured successfully!
You can now connect using: ssh userinter

Press any key to continue...
=== SSH Host Manager ===
1. List SSH hosts
2. Add new SSH host
3. Remove SSH host
4. Exit
========================
Please select an option: 1

=== Configured SSH Hosts ===
Alias           Hostname                  User            Port    
-----------------------------------------------------------------
user            1.2.3.4                   user            22      
boss            123.123.123.123           root            22      
userinter       user.inter.net            user            22      

Total hosts: 4
Use 'ssh <alias>' to connect to any host.


Press any key to continue...
```

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
=======
