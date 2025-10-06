# SSH Management Scripts (Python/PowerShell)

This repository contains Python and PowerShell scripts for optionally passwordless SSH connection management.

## SSHHosts.py - SSH Connection Setup, Python version

![SSHHosts.py screenshot 1](https://github.com/jamps3/Scripts/blob/master/ssh/SSHHosts.png)
![SSHHosts.py screenshot 2](https://github.com/jamps3/Scripts/blob/master/ssh/SSHHosts_2.png)

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

=======
