import os
import re
import platform
import subprocess
import sys

# Detect operating system
IS_WINDOWS = platform.system() == 'Windows'

# Define SSH paths
ssh_directory = os.path.join(os.path.expanduser('~'), '.ssh')
ssh_config_path = os.path.join(ssh_directory, 'config')

# Platform-specific clear screen function
def clear_screen():
    """Clear the terminal screen based on the operating system."""
    if IS_WINDOWS:
        os.system('cls')
    else:
        os.system('clear')

# Get platform-specific file permissions
def get_ssh_permissions():
    """Get appropriate file permissions for SSH files based on platform."""
    if IS_WINDOWS:
        return None  # Windows doesn't use Unix-style permissions
    else:
        return {
            'ssh_dir': 0o700,   # rwx------
            'config': 0o600,    # rw-------
            'private_key': 0o600,  # rw-------
            'public_key': 0o644    # rw-r--r--
        }

# Set file permissions if on Unix-like system
def set_file_permissions(filepath, perm_type):
    """Set appropriate file permissions on Unix-like systems."""
    if not IS_WINDOWS:
        perms = get_ssh_permissions()
        if perms and perm_type in perms:
            os.chmod(filepath, perms[perm_type])

def test_empty_string(value, field_name):
    """Return True if the string is empty or whitespace, otherwise False."""
    if not value.strip():
        print(f"Error: {field_name} cannot be empty.")
        return True
    return False

def get_ssh_hosts():
    """Parse SSH config file and extract host entries."""
    if not os.path.exists(ssh_config_path):
        return []

    hosts = []
    current_host = None

    with open(ssh_config_path, 'r') as f:
        for line in f:
            line = line.strip()
            match = re.match(r'^Host\s+(.+)$', line)
            if match:
                if current_host:
                    hosts.append(current_host)
                current_host = {
                    "Alias": match.group(1),
                    "HostName": "",
                    "User": "",
                    "Port": "22",
                    "IdentityFile": "",
                    "LocalForward": ""
                }
            elif current_host:
                # Match any key-value pair
                kv_match = re.match(r'^(\w+)\s+(.+)$', line)
                if kv_match:
                    key, value = kv_match.groups()
                    if key in current_host:
                        current_host[key] = value
                    # Handle LocalForward (can have multiple values)
                    elif key == "LocalForward":
                        # Parse value - SSH config format: "local_port remote_host:remote_port"
                        parts = value.split()
                        if len(parts) >= 2:
                            # Format: "local_port remote_host:remote_port"
                            formatted = parts[0] + " " + parts[1]
                        else:
                            formatted = value
                        if current_host["LocalForward"]:
                            current_host["LocalForward"] += "; " + formatted
                        else:
                            current_host["LocalForward"] = formatted

    if current_host:
        hosts.append(current_host)

    return hosts

def show_ssh_hosts():
    """Display SSH hosts."""
    hosts = get_ssh_hosts()

    if not hosts:
        print("No SSH hosts configured.")
        return

    print("\n=== Configured SSH Hosts ===")
    print(f"{'Alias':<15} {'Hostname':<25} {'User':<15} {'Port':<8} {'Key File':<50}")
    print("-" * 115)

    for host in hosts:
        # Get the key file path, or show default/none
        key_file = host.get('IdentityFile', '')
        if not key_file:
            key_file = "(default SSH keys)"
        else:
            # Check if the key file exists
            if os.path.exists(key_file):
                key_status = "✓"
            else:
                key_status = "✗"
            key_file = f"{key_status} {key_file}"
        
        print(f"{host['Alias']:<15} {host['HostName']:<25} {host['User']:<15} {host['Port']:<8} {key_file:<50}")

    print(f"\nTotal hosts: {len(hosts)}")
    print("Legend: ✓ = Key file exists, ✗ = Key file missing")
    print("Use 'ssh <alias>' to connect to any host.\n")

def remove_ssh_host():
    """Remove an SSH host."""
    hosts = get_ssh_hosts()

    if not hosts:
        print("No SSH hosts configured to remove.")
        return

    print("\n=== Remove SSH Host ===")
    show_ssh_hosts()

    alias_to_remove = input("Enter the alias of the host to remove (or 'cancel' to abort): ").strip()

    if alias_to_remove.lower() == 'cancel' or not alias_to_remove:
        print("Operation cancelled.")
        return

    host_to_remove = next((host for host in hosts if host['Alias'] == alias_to_remove), None)

    if not host_to_remove:
        print(f"Error: No host found with alias '{alias_to_remove}'.")
        return

    confirm = input(f"Are you sure you want to remove host '{alias_to_remove}'? (Y/N): ").strip().lower()

    if confirm != 'y':
        print("Operation cancelled.")
        return

    try:
        with open(ssh_config_path, 'r') as file:
            content = file.readlines()

        new_content = []
        skip_lines = False

        for line in content:
            trimmed_line = line.strip()
            if re.match(r'^Host\s+(.+)$', trimmed_line):
                if re.match(r'^Host\s+(.+)$', trimmed_line).group(1) == alias_to_remove:
                    skip_lines = True
                    continue
                else:
                    skip_lines = False

            if not skip_lines:
                new_content.append(line)

        with open(ssh_config_path, 'w') as file:
            file.writelines(new_content)

        print(f"Successfully removed SSH host '{alias_to_remove}'.")
    except Exception as e:
        print(f"Error removing SSH host: {e}")

def add_ssh_host():
    """Add a new SSH host."""
    print("\n=== Add New SSH Host ===")

    username = input("Enter the username for SSH connection: ").strip()
    hostname = input("Enter the hostname or IP address of the SSH server: ").strip()
    port_input = input("Enter the port number (press Enter for default port 22): ").strip()
    server_alias = input("Enter an alias for this SSH connection: ").strip()

    if test_empty_string(server_alias, "Server alias"):
        return

    server_alias = re.sub(r'[^a-zA-Z0-9_-]', '', server_alias)

    if not server_alias:
        print("Error: Server alias contains only invalid characters.")
        return

    existing_hosts = get_ssh_hosts()

    if any(host['Alias'] == server_alias for host in existing_hosts):
        print(f"Error: An SSH host with alias '{server_alias}' already exists.")
        return

    if test_empty_string(username, "Username") or test_empty_string(hostname, "Hostname"):
        return

    port = 22
    if port_input and port_input.isdigit() and 1 <= int(port_input) <= 65535:
        port = int(port_input)
    elif port_input:
        print("Error: Port must be a valid number between 1 and 65535.")
        return

    # Ask about port forwarding
    local_forward = ""
    add_port_forward = input("Would you like to set up port forwarding? (y/n): ").strip().lower()
    if add_port_forward == 'y':
        local_port = input("Enter local port (e.g., 3000): ").strip()
        remote_host = input("Enter remote host to forward to (e.g., localhost): ").strip()
        remote_port = input("Enter remote port (e.g., 3000): ").strip()
        
        if local_port.isdigit() and remote_port.isdigit():
            # SSH config format: LocalForward local_port remote_host:remote_port
            local_forward = f"{local_port} {remote_host}:{remote_port}"
            print(f"Port forwarding configured: local {local_port} -> {remote_host}:{remote_port}")
        else:
            print("Error: Ports must be valid numbers. Port forwarding not configured.")

    if not os.path.exists(ssh_directory):
        os.makedirs(ssh_directory)
        set_file_permissions(ssh_directory, 'ssh_dir')
        print(f"Created SSH directory: {ssh_directory}")

    private_key_path = os.path.join(ssh_directory, 'id_ed25519')
    public_key_path = private_key_path + '.pub'

    if not os.path.exists(private_key_path):
        print(f"No SSH key found at {private_key_path}")
        create_keys = input("No SSH key found! Would you like to generate one? (y/n): ").strip().lower()
        if create_keys == 'y':
            email = input("Enter your email for the SSH key comment: ").strip()
            try:
                # Create a new key pair
                subprocess.run([
                    'ssh-keygen',
                    '-t', 'ed25519',
                    '-f', private_key_path,
                    '-C', email,
                    '-N', ''  # No passphrase
                ], check=True)
                print("SSH key pair generated successfully!")
                
                # Set proper file permissions for the generated keys (Unix-like systems only)
                set_file_permissions(private_key_path, 'private_key')
                set_file_permissions(public_key_path, 'public_key')
                
                # Ask if user wants to copy the public key to the remote server
                copy_key = input(f"Would you like to copy the public key to {hostname} for passwordless login? (y/n): ").strip().lower()
                if copy_key == 'y':
                    if not IS_WINDOWS:
                        # Use ssh-copy-id on Unix-like systems
                        try:
                            ssh_copy_cmd = ['ssh-copy-id', '-i', public_key_path]
                            if port != 22:
                                ssh_copy_cmd.extend(['-p', str(port)])
                            ssh_copy_cmd.append(f"{username}@{hostname}")
                            
                            print(f"Copying public key to {hostname}...")
                            subprocess.run(ssh_copy_cmd, check=True)
                            print("Public key copied successfully! Passwordless login should now work.")
                        except subprocess.CalledProcessError as e:
                            print(f"Error copying public key: {e}")
                            print("You may need to copy the public key manually.")
                        except FileNotFoundError:
                            print("ssh-copy-id not found. You may need to copy the public key manually.")
                            print(f"To copy manually, run: cat {public_key_path} and add it to ~/.ssh/authorized_keys on the remote server.")
                    else:
                        # On Windows, use alternative method to copy the public key
                        try:
                            print(f"Copying public key to {hostname}...")
                            
                            # Create the SSH command to copy the public key
                            ssh_cmd = ['ssh']
                            if port != 22:
                                ssh_cmd.extend(['-p', str(port)])
                            ssh_cmd.extend([f"{username}@{hostname}", 
                                          "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"])
                            
                            # Read the public key content
                            with open(public_key_path, 'r') as key_file:
                                public_key_content = key_file.read().strip()
                            
                            # Use PowerShell/CMD to pipe the key content to SSH
                            if IS_WINDOWS:
                                # Use PowerShell to pipe the content
                                ps_cmd = f'Get-Content "{public_key_path}" | ssh'
                                if port != 22:
                                    ps_cmd += f' -p {port}'
                                ps_cmd += f' {username}@{hostname} "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"'
                                
                                result = subprocess.run(['powershell', '-Command', ps_cmd], 
                                                       capture_output=True, text=True)
                                
                                if result.returncode == 0:
                                    print("Public key copied successfully! Passwordless login should now work.")
                                else:
                                    print(f"Error copying public key: {result.stderr}")
                                    print("Falling back to manual instructions...")
                                    raise subprocess.CalledProcessError(result.returncode, ps_cmd)
                                    
                        except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
                            print(f"Automatic key copying failed: {e}")
                            print(f"\nTo enable passwordless login manually:")
                            print(f"Public key location: {public_key_path}")
                            print(f"\nOption 1 - Use PowerShell:")
                            print(f'Get-Content "{public_key_path}" | ssh {username}@{hostname} "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"')
                            print(f"\nOption 2 - Copy manually:")
                            print(f"1. Copy the contents of {public_key_path}")
                            print(f"2. SSH to {hostname} and add it to ~/.ssh/authorized_keys")
                
            except subprocess.CalledProcessError as e:
                print(f"Error generating key: {e}")
            except FileNotFoundError:
                print("Error: ssh-keygen not found. Please install OpenSSH or Git for Windows.")
    elif os.path.exists(public_key_path):
        # SSH key exists, ask if user wants to copy it to the remote server
        copy_existing_key = input(f"SSH key exists. Would you like to copy it to {hostname} for passwordless login? (y/n): ").strip().lower()
        if copy_existing_key == 'y':
            if not IS_WINDOWS:
                # Use ssh-copy-id on Unix-like systems
                try:
                    ssh_copy_cmd = ['ssh-copy-id', '-i', public_key_path]
                    if port != 22:
                        ssh_copy_cmd.extend(['-p', str(port)])
                    ssh_copy_cmd.append(f"{username}@{hostname}")
                    
                    print(f"Copying existing public key to {hostname}...")
                    subprocess.run(ssh_copy_cmd, check=True)
                    print("Public key copied successfully! Passwordless login should now work.")
                except subprocess.CalledProcessError as e:
                    print(f"Error copying public key: {e}")
                    print("You may need to copy the public key manually.")
                except FileNotFoundError:
                    print("ssh-copy-id not found. You may need to copy the public key manually.")
                    print(f"To copy manually, run: cat {public_key_path} and add it to ~/.ssh/authorized_keys on the remote server.")
            else:
                # On Windows, use alternative method to copy the existing public key
                try:
                    print(f"Copying existing public key to {hostname}...")
                    
                    # Use PowerShell to pipe the content
                    ps_cmd = f'Get-Content "{public_key_path}" | ssh'
                    if port != 22:
                        ps_cmd += f' -p {port}'
                    ps_cmd += f' {username}@{hostname} "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"'
                    
                    result = subprocess.run(['powershell', '-Command', ps_cmd], 
                                           capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print("Public key copied successfully! Passwordless login should now work.")
                    else:
                        print(f"Error copying public key: {result.stderr}")
                        print("Falling back to manual instructions...")
                        raise subprocess.CalledProcessError(result.returncode, ps_cmd)
                        
                except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
                    print(f"Automatic key copying failed: {e}")
                    print(f"\nTo enable passwordless login manually:")
                    print(f"Public key location: {public_key_path}")
                    print(f"\nOption 1 - Use PowerShell:")
                    print(f'Get-Content "{public_key_path}" | ssh {username}@{hostname} "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"')
                    print(f"\nOption 2 - Copy manually:")
                    print(f"1. Copy the contents of {public_key_path}")
                    print(f"2. SSH to {hostname} and add it to ~/.ssh/authorized_keys")

    # Create SSH config file if it doesn't exist
    if not os.path.exists(ssh_config_path):
        with open(ssh_config_path, 'w') as file:
            file.write('')
        set_file_permissions(ssh_config_path, 'config')
        print(f"Created SSH config file: {ssh_config_path}")

    needs_new_line = False

    if os.path.exists(ssh_config_path):
        with open(ssh_config_path, 'r') as file:
            file_content = file.read()

        if file_content and not file_content.endswith('\n\n'):
            if not file_content.endswith('\n'):
                needs_new_line = True
                file_content += '\n'
                with open(ssh_config_path, 'w') as file:
                    file.write(file_content)

    new_host_entry = f"Host {server_alias}\n"
    new_host_entry += f"    HostName {hostname}\n"
    new_host_entry += f"    User {username}\n"
    if port != 22:
        new_host_entry += f"    Port {port}\n"
    if local_forward:
        new_host_entry += f"    LocalForward {local_forward}\n"
    new_host_entry += f"    IdentityFile {private_key_path}\n"
    new_host_entry += "    IdentitiesOnly yes\n"

    if needs_new_line:
        new_host_entry = "\n" + new_host_entry

    with open(ssh_config_path, 'a') as file:
        file.write(new_host_entry)

    print(f"Successfully added new SSH host entry for '{server_alias}'")
    print(f"\n=== SSH Connection Details ===")
    print(f"Alias:    {server_alias}")
    print(f"Hostname: {hostname}")
    print(f"Username: {username}")
    print(f"Port:     {port}")
    if local_forward:
        print(f"Forward:  localhost:{local_forward}")
    print(f"Key File: {private_key_path}")
    print("============================\n")

def ssh_with_port_forwarding():
    """Connect to SSH host with port forwarding (interactive mode)."""
    hosts = get_ssh_hosts()

    if not hosts:
        print("No SSH hosts configured. Please add a host first.")
        return

    print("\n=== SSH with Port Forwarding ===")
    show_ssh_hosts()

    # Show hosts with their index numbers
    print("\nSelect a host to connect with port forwarding:")
    for i, host in enumerate(hosts, 1):
        print(f"{i}. {host['Alias']} ({host['User']}@{host['HostName']})")

    try:
        selection = input("\nEnter the number of the host (or 'cancel' to abort): ").strip()
        
        if selection.lower() == 'cancel' or not selection:
            print("Operation cancelled.")
            return

        host_index = int(selection) - 1
        if host_index < 0 or host_index >= len(hosts):
            print("Invalid selection.")
            return

        selected_host = hosts[host_index]
        
        # Get connection details
        hostname = selected_host['HostName']
        username = selected_host['User']
        port = selected_host.get('Port', '22')
        
        # If port is not set or empty, default to 22
        if not port:
            port = '22'
            
        # If host already has LocalForward configured, offer to use it
        existing_forward = selected_host.get('LocalForward', '')
        use_existing = False
        if existing_forward:
            use_existing_input = input(
                f"This host has port forwarding configured: {existing_forward}\n"
                f"Use this configuration? (y/n): "
            ).strip().lower()
            use_existing = use_existing_input == 'y'

        if use_existing and existing_forward:
            # Parse existing forward config - format: "local_port remote_host:remote_port"
            parts = existing_forward.split(';')[0].strip().split()
            if len(parts) >= 2:
                local_port = parts[0]
                # Split remote_host:remote_port
                remote_parts = parts[1].split(':')
                if len(remote_parts) >= 2:
                    remote_host = remote_parts[0]
                    remote_port = remote_parts[1]
                else:
                    print("Invalid existing port forwarding configuration.")
                    return
            else:
                print("Invalid existing port forwarding configuration.")
                return
        else:
            # Get new port forwarding details
            print("\nEnter port forwarding details:")
            local_port = input("Local port (e.g., 3000): ").strip()
            remote_host = input("Remote host to forward to (e.g., localhost): ").strip()
            remote_port = input("Remote port (e.g., 3000): ").strip()

            if not local_port or not remote_host or not remote_port:
                print("Error: All port forwarding fields are required.")
                return

            # Validate ports
            if not local_port.isdigit() or not remote_port.isdigit():
                print("Error: Ports must be valid numbers.")
                return

        # Build and execute SSH command with port forwarding
        if IS_WINDOWS:
            # On Windows, use cmd.exe
            ssh_cmd = f'ssh -L {local_port}:{remote_host}:{remote_port}'
            if port != '22':
                ssh_cmd += f' -p {port}'
            ssh_cmd += f' {username}@{hostname}'
            
            print(f"\nConnecting with port forwarding: {local_port} -> {remote_host}:{remote_port}")
            print(f"Command: {ssh_cmd}\n")
            os.system(ssh_cmd)
        else:
            # On Unix-like systems
            ssh_cmd = ['ssh', '-L', f'{local_port}:{remote_host}:{remote_port}']
            if port != '22':
                ssh_cmd.extend(['-p', port])
            ssh_cmd.append(f'{username}@{hostname}')
            
            print(f"\nConnecting with port forwarding: {local_port} -> {remote_host}:{remote_port}")
            print(f"Command: {' '.join(ssh_cmd)}\n")
            subprocess.run(ssh_cmd)

    except ValueError:
        print("Invalid input. Please enter a valid number.")
    except Exception as e:
        print(f"Error: {e}")

def show_menu():
    """Show main menu."""
    platform_name = "Windows" if IS_WINDOWS else platform.system()
    print(f"=== SSH Host Manager ({platform_name}) ===")
    print("1. List SSH hosts")
    print("2. Add new SSH host")
    print("3. Remove SSH host")
    print("4. SSH with Port Forwarding")
    print("5. Exit")

def main():
    """Main menu loop."""
    while True:
        show_menu()
        choice = input("Please select an option: ").strip()

        if choice == '1':
            show_ssh_hosts()
            input("\nPress any key to continue...")
        elif choice == '2':
            add_ssh_host()
            input("\nPress any key to continue...")
        elif choice == '3':
            remove_ssh_host()
            input("\nPress any key to continue...")
        elif choice == '4':
            ssh_with_port_forwarding()
            input("\nPress any key to continue...")
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
