# Add-SSHHost.ps1
# Script to add a new SSH host entry to the SSH config file

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

# Prompt for user inputs
$username = Read-Host -Prompt "Enter the username for SSH connection"
$hostname = Read-Host -Prompt "Enter the hostname or IP address of the SSH server"
$portInput = Read-Host -Prompt "Enter the port number (press Enter for default port 22)"

# Validate inputs
if ((Test-EmptyString -Value $username -FieldName "Username") -or 
    (Test-EmptyString -Value $hostname -FieldName "Hostname")) {
    exit 1
}

# Process port input
$port = 22 # Default SSH port
if (-not [string]::IsNullOrWhiteSpace($portInput)) {
    if ($portInput -match "^\d+$" -and [int]$portInput -ge 1 -and [int]$portInput -le 65535) {
        $port = [int]$portInput
    } else {
        Write-Host "Error: Port must be a valid number between 1 and 65535." -ForegroundColor Red
        exit 1
    }
}

# Define SSH paths
$sshDirectory = "$env:USERPROFILE\.ssh"
$sshConfigPath = "$sshDirectory\config"
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
        exit 1
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
            exit 1
        }
    }
    else {
        Write-Host "Operation cancelled. SSH config file is required." -ForegroundColor Red
        exit 1
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
$newHostEntry = "Host $username`n"
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
    
    Write-Host "Successfully added new SSH host entry for '$username'" -ForegroundColor Green
    
    if ($keySetupSuccess) {
        Write-Host "You can now connect using: ssh $username" -ForegroundColor Cyan
    } else {
        Write-Host "Configuration added, but passwordless login setup was not completed." -ForegroundColor Yellow
        Write-Host "You can still connect using: ssh $username (but you may be prompted for a password)" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "Error adding host entry to SSH config file: $_" -ForegroundColor Red
    exit 1
}

