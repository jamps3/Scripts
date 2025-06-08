# Add-SSHHost.ps1
# Script to manage SSH host entries in the SSH config file

# Define SSH paths
$sshDirectory = "$env:USERPROFILE\.ssh"
$sshConfigPath = "$sshDirectory\config"

# Function to validate if a string is empty or whitespace
function Test-EmptyString {
    param (
        [string]$Value,
        [string]$FieldName
    )
    
    if ([string]::IsNullOrWhiteSpace($Value)) {
        Write-Host "Error: $FieldName cannot be empty." -ForegroundColor Red
        return $true
    }
    return $false
}

# Function to parse SSH config file and extract host entries
function Get-SSHHosts {
    if (-not (Test-Path -Path $sshConfigPath)) {
        return @()
    }
    
    $hosts = @()
    $content = Get-Content -Path $sshConfigPath
    $currentHost = $null
    
    foreach ($line in $content) {
        $line = $line.Trim()
        if ($line -match "^Host\s+(.+)$") {
            if ($currentHost) {
                $hosts += $currentHost
            }
            $currentHost = @{
                Alias = $matches[1]
                HostName = ""
                User = ""
                Port = "22"
            }
        }
        elseif ($currentHost -and $line -match "^(\w+)\s+(.+)$") {
            $key = $matches[1]
            $value = $matches[2]
            if ($currentHost.ContainsKey($key)) {
                $currentHost[$key] = $value
            }
        }
    }
    
    if ($currentHost) {
        $hosts += $currentHost
    }
    
    return $hosts
}

# Function to display SSH hosts
function Show-SSHHosts {
    $hosts = Get-SSHHosts
    
    if ($hosts.Count -eq 0) {
        Write-Host "No SSH hosts configured." -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n=== Configured SSH Hosts ===" -ForegroundColor Cyan
    Write-Host ("{0,-15} {1,-25} {2,-15} {3,-8}" -f "Alias", "Hostname", "User", "Port") -ForegroundColor White
    Write-Host ("-" * 65) -ForegroundColor Gray
    
    foreach ($host in $hosts) {
        $port = if ($host.Port) { $host.Port } else { "22" }
        Write-Host ("{0,-15} {1,-25} {2,-15} {3,-8}" -f $host.Alias, $host.HostName, $host.User, $port) -ForegroundColor White
    }
    
    Write-Host "`nTotal hosts: $($hosts.Count)" -ForegroundColor Gray
    Write-Host "Use 'ssh <alias>' to connect to any host.`n" -ForegroundColor Cyan
}

# Function to remove an SSH host
function Remove-SSHHost {
    $hosts = Get-SSHHosts
    
    if ($hosts.Count -eq 0) {
        Write-Host "No SSH hosts configured to remove." -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n=== Remove SSH Host ===" -ForegroundColor Red
    Show-SSHHosts
    
    $aliasToRemove = Read-Host -Prompt "Enter the alias of the host to remove (or 'cancel' to abort)"
    
    if ($aliasToRemove -eq "cancel" -or [string]::IsNullOrWhiteSpace($aliasToRemove)) {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        return
    }
    
    # Check if the alias exists
    $hostToRemove = $hosts | Where-Object { $_.Alias -eq $aliasToRemove }
    if (-not $hostToRemove) {
        Write-Host "Error: No host found with alias '$aliasToRemove'." -ForegroundColor Red
        return
    }
    
    # Confirm removal
    $confirm = Read-Host -Prompt "Are you sure you want to remove host '$aliasToRemove' ($($hostToRemove.HostName))? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        return
    }
    
    try {
        # Read the entire config file
        $content = Get-Content -Path $sshConfigPath
        $newContent = @()
        $skipLines = $false
        
        foreach ($line in $content) {
            $trimmedLine = $line.Trim()
            
            # Check if this is the start of the host block we want to remove
            if ($trimmedLine -match "^Host\s+(.+)$") {
                if ($matches[1] -eq $aliasToRemove) {
                    $skipLines = $true
                    continue
                } else {
                    $skipLines = $false
                }
            }
            
            # If we encounter another Host block or empty line, stop skipping
            if ($skipLines -and ($trimmedLine -match "^Host\s+" -or [string]::IsNullOrWhiteSpace($trimmedLine))) {
                if ($trimmedLine -match "^Host\s+") {
                    $skipLines = $false
                } else {
                    # Skip empty lines after the removed host
                    continue
                }
            }
            
            # Add line if we're not skipping
            if (-not $skipLines) {
                $newContent += $line
            }
        }
        
        # Write the updated content back to the file
        Set-Content -Path $sshConfigPath -Value $newContent
        
        Write-Host "Successfully removed SSH host '$aliasToRemove'." -ForegroundColor Green
    }
    catch {
        Write-Host "Error removing SSH host: $_" -ForegroundColor Red
    }
}

# Function to show main menu
function Show-Menu {
    Clear-Host
    Write-Host "=== SSH Host Manager ===" -ForegroundColor Cyan
    Write-Host "1. List SSH hosts" -ForegroundColor White
    Write-Host "2. Add new SSH host" -ForegroundColor White
    Write-Host "3. Remove SSH host" -ForegroundColor White
    Write-Host "4. Exit" -ForegroundColor White
    Write-Host "========================" -ForegroundColor Cyan
}

# Function to add a new SSH host
function Add-SSHHost {
    Write-Host "`n=== Add New SSH Host ===" -ForegroundColor Green
    
    # Prompt for user inputs
    $username = Read-Host -Prompt "Enter the username for SSH connection"
    $hostname = Read-Host -Prompt "Enter the hostname or IP address of the SSH server"
    $portInput = Read-Host -Prompt "Enter the port number (press Enter for default port 22)"
    $serverAlias = Read-Host -Prompt "Enter an alias for this SSH connection (will be used as 'ssh <alias>')"
    
    # Validate alias input
    if (Test-EmptyString -Value $serverAlias -FieldName "Server alias") {
        return
    }
    
    # Remove any spaces or special characters from alias for safety
    $serverAlias = $serverAlias -replace '[^a-zA-Z0-9_-]', ''
    if ([string]::IsNullOrWhiteSpace($serverAlias)) {
        Write-Host "Error: Server alias contains only invalid characters. Please use only letters, numbers, hyphens, and underscores." -ForegroundColor Red
        return
    }
    
    # Check if alias already exists
    $existingHosts = Get-SSHHosts
    $existingAlias = $existingHosts | Where-Object { $_.Alias -eq $serverAlias }
    if ($existingAlias) {
        Write-Host "Error: An SSH host with alias '$serverAlias' already exists." -ForegroundColor Red
        return
    }
    
    # Validate inputs
    if ((Test-EmptyString -Value $username -FieldName "Username") -or 
        (Test-EmptyString -Value $hostname -FieldName "Hostname")) {
        return
    }
    
    # Process port input
    $port = 22 # Default SSH port
    if (-not [string]::IsNullOrWhiteSpace($portInput)) {
        if ($portInput -match "^\d+$" -and [int]$portInput -ge 1 -and [int]$portInput -le 65535) {
            $port = [int]$portInput
        } else {
            Write-Host "Error: Port must be a valid number between 1 and 65535." -ForegroundColor Red
            return
        }
    }
    
    # Define SSH paths for this function
    $privateKeyPath = "$sshDirectory\id_ed25519"
    $publicKeyPath = "$sshDirectory\id_ed25519.pub"
    
    # Ensure .ssh directory exists
    if (-not (Test-Path -Path $sshDirectory)) {
        try {
            New-Item -ItemType Directory -Path $sshDirectory -Force | Out-Null
            Write-Host "Created directory: $sshDirectory" -ForegroundColor Green
        }
        catch {
            Write-Host "Error creating SSH directory: $_" -ForegroundColor Red
            return
        }
    }
    
    # Check for existing SSH key
    $keySetupSuccess = $true
    if (-not (Test-Path -Path $privateKeyPath)) {
        Write-Host "No SSH key found at $privateKeyPath" -ForegroundColor Yellow
        $createKey = Read-Host -Prompt "Do you want to generate a new SSH key? (Y/N)"
        
        if ($createKey -eq "Y" -or $createKey -eq "y") {
            try {
                Write-Host "Generating new SSH key pair..." -ForegroundColor Cyan
                
                # Generate key with ssh-keygen
                $email = Read-Host -Prompt "Enter your email (for key comment)"
                $keygenProcess = Start-Process -FilePath "ssh-keygen" -ArgumentList "-t", "ed25519", "-f", "`"$privateKeyPath`"", "-C", "`"$email`"", "-N", "`"`"" -NoNewWindow -PassThru -Wait
                
                if ($keygenProcess.ExitCode -ne 0) {
                    Write-Host "SSH key generation failed. Please check if ssh-keygen is installed." -ForegroundColor Red
                    $keySetupSuccess = $false
                }
                else {
                    Write-Host "SSH key pair generated successfully!" -ForegroundColor Green
                }
            }
            catch {
                Write-Host "Error generating SSH key: $_" -ForegroundColor Red
                $keySetupSuccess = $false
            }
        }
        else {
            Write-Host "Key generation skipped. You'll need to set up keys manually for passwordless login." -ForegroundColor Yellow
            $keySetupSuccess = $false
        }
    }
    
    # Copy public key to remote server (ssh-copy-id equivalent)
    if ($keySetupSuccess -and (Test-Path -Path $publicKeyPath)) {
        $copyKey = Read-Host -Prompt "Do you want to copy your public key to $hostname for passwordless login? (Y/N)"
        
        if ($copyKey -eq "Y" -or $copyKey -eq "y") {
            try {
                Write-Host "Copying public key to $hostname..." -ForegroundColor Cyan
                
                # Read the public key content
                $publicKeyContent = Get-Content -Path $publicKeyPath -Raw
                
                # Format command to add key to authorized_keys
                # Escape the public key content for the remote command
                $escapedPublicKey = $publicKeyContent.Trim().Replace('"', '\"')
                $remoteCommand = "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo `"$escapedPublicKey`" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
                
                # Ask for password for the ssh command
                Write-Host "Please enter the password for $username@$hostname" -ForegroundColor Cyan
                
                # Build the complete SSH command
                $sshArgs = @()
                
                # Add port argument if needed
                if ($port -ne 22) {
                    $sshArgs += "-p"
                    $sshArgs += "$port"
                }
                
                # Add destination
                $sshArgs += "$username@$hostname"
                
                # Add the remote command
                $sshArgs += $remoteCommand
                
                # Execute the SSH command
                $sshProcess = Start-Process -FilePath "ssh" -ArgumentList $sshArgs -NoNewWindow -PassThru -Wait
                
                if ($sshProcess.ExitCode -ne 0) {
                    Write-Host "Failed to copy public key to remote server. You may need to set up passwordless login manually." -ForegroundColor Red
                    $keySetupSuccess = $false
                }
                else {
                    Write-Host "Public key copied successfully! Passwordless login should now work." -ForegroundColor Green
                }
            }
            catch {
                Write-Host "Error copying public key: $_" -ForegroundColor Red
                $keySetupSuccess = $false
            }
        }
        else {
            Write-Host "Key copying skipped. You'll need to manually copy your public key for passwordless login." -ForegroundColor Yellow
            $keySetupSuccess = $false
        }
    }
    
    # Check if the config file exists
    if (-not (Test-Path -Path $sshConfigPath)) {
        Write-Host "SSH config file does not exist at $sshConfigPath" -ForegroundColor Yellow
        $createFile = Read-Host -Prompt "Do you want to create it? (Y/N)"
        
        if ($createFile -eq "Y" -or $createFile -eq "y") {
            try {
                # Create an empty config file
                New-Item -ItemType File -Path $sshConfigPath -Force | Out-Null
                Write-Host "Created SSH config file: $sshConfigPath" -ForegroundColor Green
            }
            catch {
                Write-Host "Error creating SSH config file: $_" -ForegroundColor Red
                return
            }
        }
        else {
            Write-Host "Operation cancelled. SSH config file is required." -ForegroundColor Red
            return
        }
    }
    
    # Check if the file content ends with a blank line
    $fileContent = Get-Content -Path $sshConfigPath -Raw
    $needsNewLine = $false
    
    if ($fileContent) {
        # If the file is not empty and doesn't end with two newlines, add a newline
        if (-not $fileContent.EndsWith("`n`n")) {
            if ($fileContent.EndsWith("`n")) {
                $needsNewLine = $true
            }
            else {
                $needsNewLine = $true
                $fileContent += "`n"
                Set-Content -Path $sshConfigPath -Value $fileContent -NoNewline
            }
        }
    }
    
    # Format the new host entry
    $newHostEntry = "Host $serverAlias`n"
    $newHostEntry += "    HostName $hostname`n"
    $newHostEntry += "    User $username`n"
    # Add port only if it's not the default SSH port (22)
    if ($port -ne 22) {
        $newHostEntry += "    Port $port`n"
    }
    $newHostEntry += "    IdentityFile $env:USERPROFILE\.ssh\id_ed25519`n"
    $newHostEntry += "    IdentitiesOnly yes"
    
    # Add a blank line before the new entry if needed
    if ($needsNewLine) {
        $newHostEntry = "`n" + $newHostEntry
    }
    
    try {
        # Append the new host entry to the config file
        Add-Content -Path $sshConfigPath -Value $newHostEntry
        
        Write-Host "Successfully added new SSH host entry for '$serverAlias'" -ForegroundColor Green
        Write-Host "`n=== SSH Connection Details ===" -ForegroundColor Cyan
        Write-Host "Alias:    $serverAlias" -ForegroundColor White
        Write-Host "Hostname: $hostname" -ForegroundColor White
        Write-Host "Username: $username" -ForegroundColor White
        Write-Host "Port:     $port" -ForegroundColor White
        Write-Host "Key File: $env:USERPROFILE\.ssh\id_ed25519" -ForegroundColor White
        Write-Host "============================`n" -ForegroundColor Cyan
        
        if ($keySetupSuccess) {
            Write-Host "✓ Passwordless login configured successfully!" -ForegroundColor Green
            Write-Host "You can now connect using: ssh $serverAlias" -ForegroundColor Cyan
        } else {
            Write-Host "⚠ Configuration added, but passwordless login setup was not completed." -ForegroundColor Yellow
            Write-Host "You can still connect using: ssh $serverAlias (but you may be prompted for a password)" -ForegroundColor Cyan
        }
    }
    catch {
        Write-Host "Error adding host entry to SSH config file: $_" -ForegroundColor Red
        return
    }

    Write-Host "`nPress any key to continue..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Main Menu Loop
while ($true) {
    Show-Menu
    $choice = Read-Host -Prompt "Please select an option"
    
    switch ($choice) {
        "1" { 
            Show-SSHHosts
            Write-Host "`nPress any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        "2" { Add-SSHHost }
        "3" { 
            Remove-SSHHost
            Write-Host "`nPress any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        "4" { 
            Write-Host "Goodbye!" -ForegroundColor Cyan
            break 
        }
        default { 
            Write-Host "Invalid option. Please try again." -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}
