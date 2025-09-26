#!/usr/bin/env python3
import sys
import os
import platform

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the SSHHosts module
import SSHHosts

def test_basic_functionality():
    """Test basic functionality of the SSH host manager."""
    print(f"Testing SSH Host Manager on {platform.system()}")
    print(f"Python version: {sys.version}")
    print(f"SSH directory: {SSHHosts.ssh_directory}")
    print(f"SSH config path: {SSHHosts.ssh_config_path}")
    print(f"Is Windows: {SSHHosts.IS_WINDOWS}")
    
    # Test platform detection
    if SSHHosts.IS_WINDOWS:
        print("✓ Windows platform detected correctly")
    else:
        print("✓ Non-Windows platform detected correctly")
    
    # Test SSH permissions function
    perms = SSHHosts.get_ssh_permissions()
    if SSHHosts.IS_WINDOWS:
        if perms is None:
            print("✓ Windows permissions correctly return None")
        else:
            print("✗ Windows permissions should return None")
    else:
        if perms and 'ssh_dir' in perms:
            print("✓ Unix permissions correctly returned")
        else:
            print("✗ Unix permissions not returned correctly")
    
    # Test get_ssh_hosts function
    try:
        hosts = SSHHosts.get_ssh_hosts()
        print(f"✓ get_ssh_hosts() returned {len(hosts)} hosts")
    except Exception as e:
        print(f"✗ get_ssh_hosts() failed: {e}")
    
    # Test validation functions
    if SSHHosts.test_empty_string("", "test"):
        print("✓ Empty string validation works")
    else:
        print("✗ Empty string validation failed")

    if SSHHosts.test_empty_string("valid", "test"):
        print("✗ Non-empty string validation failed")
    else:
        print("✓ Non-empty string validation works")
    
    print("\nBasic functionality test completed!")

if __name__ == "__main__":
    test_basic_functionality()
