# push_to_github.ps1
# Automates Git initialization, repository staging, and pushing to GitHub.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$RepoUrl = ""
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Automated Sales Data Pipeline - GitHub Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check for Git
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "[!] Git is not found in your PATH." -ForegroundColor Yellow
    Write-Host "Attempting to install Git via winget..." -ForegroundColor Yellow
    
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "Running: winget install --id Git.Git -e --source winget" -ForegroundColor Cyan
        & winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
        Write-Host "Git installed! Please restart your terminal/IDE window to refresh PATH, then rerun this script." -ForegroundColor Green
        return
    } else {
        Write-Host "Please download and install Git from: https://git-scm.com/download/win" -ForegroundColor Red
        return
    }
}

# Ensure we are in project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
Write-Host "[*] Working directory: $projectRoot" -ForegroundColor Green

# 2. Check Git Repo Status
if (-not (Test-Path ".git")) {
    Write-Host "[*] Initializing Git repository with default branch 'main'..." -ForegroundColor Cyan
    git init -b main
} else {
    Write-Host "[*] Existing Git repository detected." -ForegroundColor Green
}

# 3. Prompt for Remote URL if not provided
if (-not $RepoUrl) {
    Write-Host ""
    Write-Host "Please enter your GitHub repository remote URL" -ForegroundColor Yellow
    Write-Host "(e.g. https://github.com/<your-username>/sales-data-pipeline.git): " -NoNewline
    $RepoUrl = Read-Host
}

if (-not $RepoUrl) {
    Write-Host "[!] No remote URL provided. Staging and committing locally only." -ForegroundColor Yellow
}

# 4. Stage and Commit
Write-Host "[*] Staging files..." -ForegroundColor Cyan
git add .

$status = git status --porcelain
if ($status) {
    Write-Host "[*] Creating initial commit..." -ForegroundColor Cyan
    git commit -m "feat: initial commit with automated sales pipeline and CI/CD workflows"
} else {
    Write-Host "[*] Working tree clean, nothing new to commit." -ForegroundColor Green
}

# 5. Configure Remote and Push
if ($RepoUrl) {
    $existingRemote = git remote get-url origin 2>$null
    if ($existingRemote) {
        Write-Host "[*] Updating remote 'origin' to: $RepoUrl" -ForegroundColor Cyan
        git remote set-url origin $RepoUrl
    } else {
        Write-Host "[*] Adding remote 'origin': $RepoUrl" -ForegroundColor Cyan
        git remote add origin $RepoUrl
    }

    Write-Host "[*] Renaming branch to main..." -ForegroundColor Cyan
    git branch -M main

    Write-Host "[*] Pushing to GitHub (origin/main)..." -ForegroundColor Cyan
    git push -u origin main

    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host " Successfully uploaded to GitHub!" -ForegroundColor Green
    Write-Host " View your CI/CD pipelines under the 'Actions' tab on GitHub." -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
}
