# Save current root directory
$root = Get-Location
$backendFrontendFolder = Join-Path -Path $root -ChildPath "backend\home\frontend"
$frontendBuildFolder = Join-Path -Path $root -ChildPath "frontend\out"

# Change directory to the frontend folder
cd frontend

# Install dependencies
npm install

# Build the frontend
npm run build

# Check if the build was successful
if ($LASTEXITCODE -ne 0) {
    Write-Host "Stopped Build Script: Failed to build the frontend"
    exit 1
}

# Change directory back to the root folder
cd $root

# Remove the old build files from the backend folder
# Exclude the test html files [test_websocket_transcription.html, test_websocket.html] from being deleted
# Exclude static folder from being deleted
Get-ChildItem -Path $backendFrontendFolder -Recurse -Exclude test_websocket_transcription.html, test_websocket.html, static | Remove-Item -Recurse -Force

# Copy the built files to the backend folder
Get-ChildItem -Path $frontendBuildFolder -Recurse | ForEach-Object {
    $destinationPath = $_.FullName -replace [regex]::Escape($frontendBuildFolder), [regex]::Escape($backendFrontendFolder)
    if ($_.PSIsContainer -and $_.Name -eq 'static') {
        # Skip copying the static folder itself
        return
    }
    Copy-Item -Path $_.FullName -Destination $destinationPath -Recurse
}