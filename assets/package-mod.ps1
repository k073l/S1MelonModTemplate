$ModName = "MyMod"

# Define paths
$AssetDir = $PSScriptRoot
$ProjectRoot = Resolve-Path "$AssetDir\.."
$IL2CPPAssembly = Resolve-Path "$ProjectRoot\bin\Debug\net6\$ModName-IL2CPP.dll"
$MonoAssembly = Resolve-Path "$ProjectRoot\bin\Debug\netstandard2.1\$ModName-Mono.dll"
$TSZip = Join-Path $AssetDir "$ModName-TS.zip"
$NexusIL2CPPZip = Join-Path $AssetDir "$ModName-IL2CPP.zip"
$NexusMonoZip = Join-Path $AssetDir "$ModName-Mono.zip"

# Clean up any existing zips
Remove-Item -Path $TSZip, $NexusIL2CPPZip, $NexusMonoZip -ErrorAction SilentlyContinue

# --- Package TS ---
$TSFiles = @(
    "$AssetDir\icon.png",
    "$ProjectRoot\README.md",
    "$ProjectRoot\CHANGELOG.md",
    "$AssetDir\manifest.json",
    $IL2CPPAssembly,
    $MonoAssembly
)
Compress-Archive -Path $TSFiles -DestinationPath $TSZip
Write-Host "Created Thunderstore package: $TSZip"

# --- Package Nexus ---
Compress-Archive -Path $IL2CPPAssembly -DestinationPath $NexusIL2CPPZip
Compress-Archive -Path $MonoAssembly -DestinationPath $NexusMonoZip
Write-Host "Created Nexus zips: $NexusIL2CPPZip and $NexusMonoZip"
