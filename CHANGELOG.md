# Changelog

## 2.0.0
- Restructure the template
- Migrate helper scripts and post-build logic to Python with uv package manager
- Add bumper script for updating version, description, and author across multiple files
- Add cross-platform support for building with Wine/Proton on Linux and macOS
- Add fomod support - better packaging for NexusMods
- Refactor and improve packaging script for creating distribution zip for Thunderstore and NexusMods
- Refactor and improve README to NexusMods BBCode conversion script
- Migrate to MelonDebug, but keep Logger.Debug extension for convenience
- Add ToNativeList<T> extension method
- Add GetHierarchyPath extension method
- Add GetOrAddComponent<T> extension method
- Add DrawDebugVisuals extension method
- Add WaitForCondition coroutine with timeout support
- Remove WaitForNotNull and WaitForNetworkSingleton coroutines in favor of WaitForCondition
- Bump SwapperPlugin version to 1.2.2
## 1.3.0
- Fix assembly paths in packaging script
## 1.2.1
- Added icon
- Added tags
## 1.2.0
- Added README.md to NexusMods description conversion script
## 1.1.0
- Improved formatting
- Added XML docs to Debug logger extension
- Added AsEnumerable<T> extension method
- Added 2 new WaitFor* routines
- Added a packaging script for Thunderstore and NexusMods
