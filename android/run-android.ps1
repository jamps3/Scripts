param(
    [string]$Module = "app",
    [string]$Variant = "Debug",
    [string]$PackageId
)

$ErrorActionPreference = "Stop"

function Find-Up([string]$name) {
    $dir = (Get-Location).ProviderPath
    while ($dir) {
        $candidate = Join-Path $dir $name
        if (Test-Path -LiteralPath $candidate) { return $candidate }
        $parent = Split-Path -Parent $dir
        if ($parent -eq $dir) { break }
        $dir = $parent
    }
    return $null
}

function Read-TextIfExists([string]$path) {
    if (Test-Path -LiteralPath $path) {
        return Get-Content -LiteralPath $path -Raw
    }
    return $null
}

function Get-AndroidPackageId([string]$root, [string]$module) {
    $moduleDir = Join-Path $root $module
    $gradleFiles = @(
        (Join-Path $moduleDir 'build.gradle.kts'),
        (Join-Path $moduleDir 'build.gradle')
    )

    foreach ($file in $gradleFiles) {
        $text = Read-TextIfExists $file
        if (-not $text) { continue }

        $patterns = @(
            'applicationId\s*=\s*"([^"]+)"',
            "applicationId\s*=\s*'([^']+)'",
            'applicationId\s+"([^"]+)"',
            "applicationId\s+'([^']+)'",
            'namespace\s*=\s*"([^"]+)"',
            "namespace\s*=\s*'([^']+)'",
            'namespace\s+"([^"]+)"',
            "namespace\s+'([^']+)'"
        )

        foreach ($pattern in $patterns) {
            $match = [regex]::Match($text, $pattern)
            if ($match.Success) { return $match.Groups[1].Value }
        }
    }

    $manifest = Join-Path $moduleDir 'src\main\AndroidManifest.xml'
    $manifestText = Read-TextIfExists $manifest
    if ($manifestText) {
        $match = [regex]::Match($manifestText, 'package\s*=\s*"([^"]+)"')
        if ($match.Success) { return $match.Groups[1].Value }
    }

    return $null
}

$gradlew = Find-Up 'gradlew.bat'
if (-not $gradlew) {
    throw "Could not find gradlew.bat in this directory or any parent directory. Run this from inside an Android Gradle project."
}

$root = Split-Path -Parent $gradlew
$task = ":$Module`:install$Variant"

Write-Host "Project: $root"
Write-Host "Running:  .\gradlew.bat $task"
Push-Location $root
try {
    & $gradlew $task
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}

if (-not $PackageId) {
    $PackageId = Get-AndroidPackageId $root $Module
}

if (-not $PackageId) {
    throw "Install finished, but I could not detect the package id. Re-run with: run-android -PackageId com.example.app"
}

$adbCandidates = @(
    (Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'),
    'adb.exe'
)

$adb = $null
foreach ($candidate in $adbCandidates) {
    if ($candidate -eq 'adb.exe') {
        $cmd = Get-Command adb.exe -ErrorAction SilentlyContinue
        if ($cmd) { $adb = $cmd.Source; break }
    }
    elseif (Test-Path -LiteralPath $candidate) {
        $adb = $candidate; break
    }
}

if (-not $adb) {
    throw "Install finished, but adb.exe was not found. Install Android platform-tools or add adb to PATH."
}

Write-Host "Launching: $PackageId"
& $adb shell monkey -p $PackageId 1
exit $LASTEXITCODE

