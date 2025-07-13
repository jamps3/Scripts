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
                    "Port": "22"
                }
            elif current_host and re.match(r'^(\w+)\s+(.+)$', line):
                key, value = re.match(r'^(\w+)\s+(.+)$', line).groups()
                if key in current_host:
                    current_host[key] = value

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
    print(f"{'Alias':<15} {'Hostname':<25} {'User':<15} {'Port':<8}")
    print("-" * 65)

    for host in hosts:
        print(f"{host['Alias']:<15} {host['HostName']:<25} {host['User']:<15} {host['Port']:<8}")

    print(f"\nTotal hosts: {len(hosts)}")
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

    if not os.path.exists(ssh_directory):
        os.makedirs(ssh_directory)
        set_file_permissions(ssh_directory, 'ssh_dir')
        print(f"Created SSH directory: {ssh_directory}")

    private_key_path = os.path.join(ssh_directory, 'id_ed25519')
    public_key_path = private_key_path + '.pub'

    if not os.path.exists(private_key_path):
        print(f"No SSH key found at {private_key_path}")
        if not IS_WINDOWS:
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
                    
                    # Set proper file permissions for the generated keys
                    set_file_permissions(private_key_path, 'private_key')
                    set_file_permissions(public_key_path, 'public_key')
                    
                    # Ask if user wants to copy the public key to the remote server
                    copy_key = input(f"Would you like to copy the public key to {hostname} for passwordless login? (y/n): ").strip().lower()
                    if copy_key == 'y':
                        try:
                            # Use ssh-copy-id to copy the public key
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
                            print(f"To copy manually, run: cat {public_key_path} and add it to {os.path.join('~', '.ssh', 'authorized_keys')} on the remote server.")
                    
                except subprocess.CalledProcessError as e:
                    print(f"Error generating key: {e}")
    elif not IS_WINDOWS and os.path.exists(public_key_path):
        # SSH key exists, ask if user wants to copy it to the remote server
        copy_existing_key = input(f"SSH key exists. Would you like to copy it to {hostname} for passwordless login? (y/n): ").strip().lower()
        if copy_existing_key == 'y':
            try:
                # Use ssh-copy-id to copy the existing public key
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
                print(f"To copy manually, run: cat {public_key_path} and add it to {os.path.join('~', '.ssh', 'authorized_keys')} on the remote server.")

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
    print(f"Key File: {private_key_path}")
    print("============================\n")

def show_menu():
    """Show main menu."""
    platform_name = "Windows" if IS_WINDOWS else platform.system()
    print(f"=== SSH Host Manager ({platform_name}) ===")
    print("1. List SSH hosts")
    print("2. Add new SSH host")
    print("3. Remove SSH host")
    print("4. Exit")

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
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()

