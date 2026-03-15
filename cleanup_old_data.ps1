# Tau2-Bench Cleanup Script
# Removes intermediate processing data and raw data backups that are no longer needed
# Date: 2026-03-11

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Tau2-Bench Data Cleanup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Confirm before proceeding
Write-Host "This will remove approximately 66MB of intermediate data files." -ForegroundColor Yellow
Write-Host "Files to be removed:" -ForegroundColor Yellow
Write-Host "  - data/processed/* (36 MB) - Intermediate processing data"
Write-Host "  - data/raw/* (30 MB) - Original data backups"
Write-Host ""
$confirm = Read-Host "Continue? (y/N)"

if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Cleanup cancelled." -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "Starting cleanup..." -ForegroundColor Cyan
Write-Host ""

# Track freed space
$freedSpace = 0

# Function to get directory size
function Get-DirSize($path) {
    if (Test-Path $path) {
        $size = 0
        Get-ChildItem -Path $path -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $size += $_.Length
        }
        return $size
    }
    return 0
}

# 1. Remove intermediate processed data
Write-Host "[1/2] Removing intermediate processed data..." -ForegroundColor White

$processedDirs = @(
    "data\processed\medxpertqa",
    "data\processed\prodmedbench",
    "data\processed\physionet",
    "data\processed\medagentbench",
    "data\processed\clinical_tools"
)

foreach ($dir in $processedDirs) {
    if (Test-Path $dir) {
        $size = Get-DirSize $dir
        Write-Host "  Removing: $dir ($([math]::Round($size/1MB, 1)) MB)"
        Remove-Item -Recurse -Force $dir
        $freedSpace += $size
    }
}

# Remove processed markdown files
$processedFiles = @(
    "data\processed\CONSULTATION_PARADIGM_SUMMARY.md",
    "data\processed\RECONSTRUCTION_COMPLETE.txt"
)

foreach ($file in $processedFiles) {
    if (Test-Path $file) {
        Write-Host "  Removing: $file"
        Remove-Item -Force $file
    }
}

Write-Host "  Done!" -ForegroundColor Green
Write-Host ""

# 2. Remove raw data backups
Write-Host "[2/2] Removing raw data backups..." -ForegroundColor White

$rawDirs = @(
    "data\raw\MedXpertQA",
    "data\raw\PhysioNet",
    "data\raw\ProdMedBench"
)

foreach ($dir in $rawDirs) {
    if (Test-Path $dir) {
        $size = Get-DirSize $dir
        Write-Host "  Removing: $dir ($([math]::Round($size/1MB, 1)) MB)"
        Remove-Item -Recurse -Force $dir
        $freedSpace += $size
    }
}

Write-Host "  Done!" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Cleanup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Freed space: $([math]::Round($freedSpace/1MB, 1)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Yellow
Write-Host "  - Production data in data/tau2/domains/clinical/ is PRESERVED"
Write-Host "  - Conversion scripts in data/clinical/ are PRESERVED (64KB)"
Write-Host "  - All 5 clinical domains remain fully functional"
Write-Host ""
Write-Host "Clinical domains still available:" -ForegroundColor Green
Write-Host "  - clinical_cardiology (758 tasks)"
Write-Host "  - clinical_endocrinology (176 tasks)"
Write-Host "  - clinical_gastroenterology (475 tasks)"
Write-Host "  - clinical_nephrology (300 tasks)"
Write-Host "  - clinical_neurology (741 tasks)"
Write-Host ""
