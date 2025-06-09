#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Migrates all data from root-enia to root-enia2 using rsync

.DESCRIPTION
    This script copies users, nginx configuration, and all data from the source server
    to the destination server using rsync over SSH.

.NOTES
    - Requires rsync to be available (WSL, Cygwin, or native Windows rsync)
    - SSH key authentication should be set up for passwordless access
    - Script should be run with appropriate privileges
#>

param(
    [string]$SourceServer = "root-enia",
    [string]$DestServer = "root-enia2",
    [string]$SSHUser = "root",
    [switch]$DryRun = $false,
    [switch]$Verbose = $false
)

# Color output functions
function Write-Info { param($Message) Write-Host "INFO: $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "SUCCESS: $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "WARNING: $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "ERROR: $Message" -ForegroundColor Red }

# Check if rsync is available
function Test-RsyncAvailable {
    try {
        $null = Get-Command rsync -ErrorAction Stop
        return $true
    }
    catch {
        Write-Error "rsync command not found. Please install rsync (WSL, Cygwin, or native Windows version)"
        return $false
    }
}

# Test SSH connectivity
function Test-SSHConnectivity {
    param([string]$Server, [string]$User)
    
    Write-Info "Testing SSH connectivity to $User@$Server..."
    $testResult = ssh -o ConnectTimeout=10 -o BatchMode=yes "$User@$Server" "echo 'SSH connection successful'" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "SSH connection to $User@$Server successful"
        return $true
    } else {
        Write-Error "SSH connection to $User@$Server failed. Please check SSH keys and connectivity."
        return $false
    }
}

# Execute rsync with common options
function Invoke-RsyncTransfer {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$Description,
        [string[]]$ExtraOptions = @()
    )
    
    Write-Info "Syncing $Description..."
    
    # Base rsync options
    $rsyncOptions = @(
        "-avz",           # archive mode, verbose, compress
        "--progress",     # show progress
        "--stats",       # show transfer statistics
        "--human-readable", # human readable output
        "--partial",     # keep partially transferred files
        "--inplace"      # update destination files in-place
    )
    
    # Add extra options
    $rsyncOptions += $ExtraOptions
    
    # Add dry-run if specified
    if ($DryRun) {
        $rsyncOptions += "--dry-run"
        Write-Warning "DRY RUN MODE - No actual changes will be made"
    }
    
    # Add verbose if specified
    if ($Verbose) {
        $rsyncOptions += "-v"
    }
    
    # Execute rsync
    $rsyncCmd = "rsync " + ($rsyncOptions -join " ") + " `"$Source`" `"$Destination`"
    # Executing rsync command
    
    try {
        Invoke-Expression $rsyncCmd
        if ($LASTEXITCODE -eq 0) {
        } else {
            # Write-Error - sync failed
            return $false
        }
    }
    catch {
        # Write-Error - rsync execution failed
        return $false
    }
    
    return $true
}

# Main migration function
function Start-ServerMigration {
    Write-Host Testing
    # Write-Info SSH User
    
    if ($DryRun) {
        # Write-Warning DRY RUN MODE ENABLED
    }
    
    # Pre-flight checks
    # Write-Info Performing pre-flight checks
    
    if (-not (Test-RsyncAvailable)) {
        return $false
    }
    
    if (-not (Test-SSHConnectivity -Server $SourceServer -User $SSHUser)) {
        return $false
    }
    
    if (-not (Test-SSHConnectivity -Server $DestServer -User $SSHUser)) {
        return $false
    }
    
    # Write-Success Pre-flight checks passed
    
    # Define sync operations
    $syncOperations = @(
        @{
            Source = "$SSHUser@${SourceServer}:/etc/"
            Destination = "$SSHUser@${DestServer}:/etc/"
            Description = "System configuration (/etc)"
            ExtraOptions = @("--exclude=fstab", "--exclude=hostname", "--exclude=hosts")
        },
        @{
            Source = "$SSHUser@${SourceServer}:/home/"
            Destination = "$SSHUser@${DestServer}:/home/"
            Description = "User home directories (/home)"
            ExtraOptions = @()
        },
        @{
            Source = "$SSHUser@${SourceServer}:/root/"
            Destination = "$SSHUser@${DestServer}:/root/"
            Description = "Root home directory (/root)"
            ExtraOptions = @()
        },
        @{
            Source = "$SSHUser@${SourceServer}:/var/www/"
            Destination = "$SSHUser@${DestServer}:/var/www/"
            Description = "Web server data (/var/www)"
            ExtraOptions = @()
        },
        @{
            Source = "$SSHUser@${SourceServer}:/var/log/nginx/"
            Destination = "$SSHUser@${DestServer}:/var/log/nginx/"
            Description = "Nginx logs"
            ExtraOptions = @()
        },
        @{
            Source = "$SSHUser@${SourceServer}:/usr/local/"
            Destination = "$SSHUser@${DestServer}:/usr/local/"
            Description = "Local applications (/usr/local)"
            ExtraOptions = @()
        },
        @{
            Source = "$SSHUser@${SourceServer}:/opt/"
            Destination = "$SSHUser@${DestServer}:/opt/"
            Description = "Optional software (/opt)"
            ExtraOptions = @()
        },
        @{
            Source = "$SSHUser@${SourceServer}:/var/lib/"
            Destination = "$SSHUser@${DestServer}:/var/lib/"
            Description = "Application data (/var/lib)"
            ExtraOptions = @("--exclude=docker", "--exclude=containerd")
        }
    )
    
    # Execute sync operations
    $successCount = 0
    $totalOperations = $syncOperations.Count
    
    foreach ($operation in $syncOperations) {
        Write-Info "\n=== Operation $($successCount + 1) of $totalOperations ==="
        
        $result = Invoke-RsyncTransfer -Source $operation.Source -Destination $operation.Destination -Description $operation.Description -ExtraOptions $operation.ExtraOptions
        
        if ($result) {
            $successCount++
        } else {
            Write-Warning "Continuing with next operation despite failure..."
        }
    }
    
    # Final summary
    Write-Info "\n=== Migration Summary ==="
    Write-Info "Total operations: $totalOperations"
    Write-Info "Successful: $successCount"
    Write-Info "Failed: $($totalOperations - $successCount)"
    
    if ($successCount -eq $totalOperations) {
        Write-Success "All migration operations completed successfully!"
        
        if (-not $DryRun) {
            Write-Info "\nPost-migration recommendations:"
            Write-Info "1. Restart services on $DestServer (nginx, ssh, etc.)"
            Write-Info "2. Update any server-specific configurations"
            Write-Info "3. Test all applications and services"
            Write-Info "4. Update DNS records if needed"
            Write-Info "5. Update monitoring and backup configurations"
        }
    } else {
        Write-Warning "Some operations failed. Please review the output above."
    }
    
    return ($successCount -eq $totalOperations)
}

# Script execution
try {
    Write-Info "Server Migration Script Started"
    Write-Info "Source: $SourceServer"
    Write-Info "Destination: $DestServer"
    Write-Info "Time: $(Get-Date)"
    
    $migrationResult = Start-ServerMigration
    
    if ($migrationResult) {
        Write-Success "Migration completed successfully!"
        exit 0
    } else {
        Write-Error "Migration completed with errors."
        exit 1
    }
}
catch {
    Write-Error "Unexpected error during migration: $_"
    exit 1
}
finally {
    Write-Info "Script execution finished at $(Get-Date)"
}


