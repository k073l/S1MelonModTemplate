# Schedule I MelonLoader Mod Template

This is a template for creating a MelonLoader mod for the game "Schedule I". It includes a basic structure and example code to help you get started.

## Features
- Basic mod structure
- Useful methods for cross-backend compatibility
- Thunderstore and NexusMods packaging script
- Cross-backend compatibility: IL2CPP (none/beta branch) and Mono (alternate/alternate-beta branch)
- Easy build and test process: Select the target configuration, build the mod and the game will be launched automatically (e.g. Debug IL2CPP will build the mod and launch the IL2CPP version of the game with debug options)
- Automatic testing mod loading: Comment/uncomment lines in .csproj to enable/disable automatic loading of often used mods like UnityExplorer, LocalMultiplayer

## Usage
### Prerequisites
- [MelonLoader](https://melonwiki.xyz/) and basic knowledge of [how to use it](https://melonwiki.xyz/#/modders/quickstart)
- .NET SDK (as per MelonLoader requirements)
- C# IDE (e.g. Rider)
- [Schedule I](https://store.steampowered.com/app/3164500) ownership

#### Preparing the directory structure
I recommend following structure:
```
S1-modding
├── common
│   ├── LocalMultiplayer
│   └── UnityExplorer
├── gamefiles
│   ├── Schedule I IL2CPP
│   └── Schedule I Mono
```

`LocalMultiplayer` directory should contain the mod file `.dll` and `.bat` starter.
Example starter:
```bat
start "" "Schedule I.exe" --host --adjust-window --left-offset 0
timeout /t 1
start "" "Schedule I.exe" --join --adjust-window --left-offset 20
```

`UnityExplorer` directory should contain `.dll` files for IL2CPP and Mono versions of the mod.

`gamefiles` directory should contain the game files for IL2CPP and Mono versions of the game. You can use the `Schedule I IL2CPP` and `Schedule I Mono` directories to store the game files for each version.

### Usage
#### Installation
To install this template, use:
```
dotnet new install k073l.S1MelonMod
```

#### Creating a new mod
To create a new mod you can use the new solution wizard:
![solution wizard in Rider](https://raw.githubusercontent.com/k073l/S1MelonModTemplate/master/assets/wizard.png)
Alternatively, you can create a new project using the command line:
```
dotnet new S1MelonMod -n MyNewMod \
  --S1MonoDir "" \
  --S1IL2CPPDir ""
```
#### Parameters
| Name                  | Required | Description                                                                                          |
| --------------------- | -------- | ---------------------------------------------------------------------------------------------------- |
| S1MonoDir             | Yes      | Path to the Mono version of the game.                                                                |
| S1IL2CPPDir           | Yes      | Path to the IL2CPP version of the game.                                                              |
| CommonDir             | No       | Path to the common directory. (helper path, mostly useful as a variable)                             |
| UnityExplorerMono     | No       | Path to the Mono version of the [UnityExplorer](https://github.com/yukieiji/UnityExplorer) mod.      |
| UnityExplorerIL2CPP   | No       | Path to the IL2CPP version of the [UnityExplorer](https://github.com/yukieiji/UnityExplorer) mod.    |
| MultiplayerModMono    | No       | Path to the Mono version of the [LocalMultiplayer](https://github.com/k073l/LocalMultiplayer) mod.   |
| MultiplayerModIL2CPP  | No       | Path to the IL2CPP version of the [LocalMultiplayer](https://github.com/k073l/LocalMultiplayer) mod. |
| MultiplayerModStarter | No       | Path to the [LocalMultiplayer](https://github.com/k073l/LocalMultiplayer) mod starter bat file.      |


You can use parameters to set the paths of other params. For example, you can set the `CommonDir` parameter to the path of the common directory, and then use it to set the paths of the `UnityExplorerMono`, `UnityExplorerIL2CPP`, `MultiplayerModMono`, and `MultiplayerModIL2CPP` parameters. This way, you can keep your configurations readable.

#### Packaging
This template includes Thunderstore and NexusMods packaging script. Once both IL2CPP and Mono builds were built and tested, you can fill out `assets/manifest.json` and drop in your `icon.png`. Then simply run `assets/package-mod.ps1`. You should see 3 zip files in assets directory. Thunderstore package `*-TS.zip` will contain `manifest.json`, `icon.png`, `README.md`, `CHANGELOG.md` and both `.dll` files for IL2CPP and Mono versions of your mod. NexusMods zips are `*-IL2CPP.zip` and `*-Mono.zip`. They contain only the mod files.

##### README.md conversion to NexusMods description
In `assets/` you can find `README.md` to `NexusMods` description conversion script. It will convert the `README.md` file to a format that is compatible with NexusMods description. You can run it using:
`.\assets\convert-readme.ps1`.
This will create a new file `README-nexus.txt` in root of the project. Then, you can copy the content of this file, switch description editor mode to `BBCode`
![bbcode option in description editor](https://raw.githubusercontent.com/k073l/S1MelonModTemplate/master/assets/bbcode.png)
and paste it there. You can switch back to normal mode after pasting using the same `BBCode` button and verify that everything looks good.

**Disclaimer:** `convert-readme.ps1` uses [uv](https://docs.astral.sh/uv) to run the Python script responsible for conversion (Python script is embedded in Powershell). As such, this script will contact uv servers to download the tool, drop files (uv.exe, Python script, temp environment). All data will be cleaned up, but since it's contacting the internet you should verify the contents of the script before running it, to make sure for yourself it's not malicious. [Script behavior analysis on VirusTotal.](https://www.virustotal.com/gui/file/018ef20da353604ac0ad5d12ba321fb1fb5bff83e07cd0e40c13dc2b3bdb15cf/behavior)

### Additional information
Information on S1 modding can be found in the [S1 modding discord](https://discord.gg/9Z5RKEYSzq).

## Bundled methods
#### MelonLogger Extension
`Debug` method allows you to log messages only when mod is built in Debug configuration. Additionally, it automatically logs caller info.
```csharp
private static MelonLogger.Instance _logger = new MelonLogger.Instance("MyMod"); // logger instance needs to be created
_logger.Debug("This message will be logged only in Debug configuration");
```
#### Il2CppList Extension
`ToIl2CppList<T>` makes converting `List<T>` to `Il2CppList<T>` easier.
```csharp
List<int> list = new List<int> { 1, 2, 3 };
Il2CppSystem.Collections.Generic.List<int> il2cppList = list.ToIl2CppList();
```
`ConvertToList<T>` naturally, converts `Il2CppList<T>` to `List<T>`.
```csharp
Il2CppSystem.Collections.Generic.List<int> il2cppList = new Il2CppSystem.Collections.Generic.List<int> { 1, 2, 3 };
List<int> list = il2cppList.ConvertToList();
```
`AsEnumerable<T>` allows you to use LINQ on both Il2Cpp Lists and System Lists.
```csharp
var deliveryVehicle = VehicleManager.Instance.AllVehicles.AsEnumerable().FirstOrDefault(); // works both in il2cpp and mono
// without AsEnumerable we'd need to
#if MONO
var deliveryVehicle = VehicleManager.Instance.AllVehicles.FirstOrDefault();
#else
var deliveryVehicle = VehicleManager.Instance.AllVehicles._items[0];
#endif
```
#### Utils
`FindObjectByName<T>` finds loaded object by name.
```csharp
var sprite = Utils.FindObjectByName<Sprite>("MySprite");
```
`GetAllComponentsInChildrenRecursive<T>` gets all components of type `T` in children of the object.
```csharp
var components = Utils.GetAllComponentsInChildrenRecursive<MyComponent>(myGameObject);
```
`Is<T>` checks and casts object to type `T`.
```csharp
if (Is<MyComponent>(someObj, out var res))
{
    // res is MyComponent
}
```
`GetAllStorableItemDefinitions` returns all storable item definitions from the registry.
```csharp
var allStorableItemDefinitions = Utils.GetAllStorableItemDefinitions();
var item = allStorableItemDefinitions.FirstOrDefault(x => x.ID == "cuke");
```
##### Routines
There are several methods that can be used in `MelonCoroutines.Start(coroutine)`: `WaitForPlayer, WaitForNetwork, WaitForNotNull, WaitForNetworkSingleton`.
Every method is documented using XML docs.
