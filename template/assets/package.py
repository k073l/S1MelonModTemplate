#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich", "typer", "lxml"]
# ///
"""
This tool can be used to package the mod for distribution on Nexus and Thunderstore.
"""

from rich.console import Console
from rich.traceback import install
import typer
from pathlib import Path
import zipfile
from lxml import etree as ET

MOD_NAME = "MyMod"  # Will be replaced by template
MONO_BUILD = "Mono"
IL2CPP_BUILD = "IL2CPP"

parent_dir = Path(__file__).resolve().parent.parent
output_dir = parent_dir / "dist"

console = Console()
install(console=console)
app = typer.Typer()


def step(msg: str) -> None:
    """Print a step message."""
    console.print(f"\n[bold blue]▸[/bold blue] [bold]{msg}[/bold]")


def ok(msg: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {msg}", style="green")


def error(msg: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗[/red] {msg}", style="red")
    raise typer.Exit(code=1)


def warn(msg: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]⚠[/yellow] {msg}", style="yellow")


def get_build_paths() -> dict[str, Path]:
    """Get paths to all build artifacts."""
    bin_dir = parent_dir / "bin"
    assets_dir = parent_dir / "assets"
    fomod_dir = assets_dir / "fomod"

    return {
        "icon": assets_dir / "icon.png",
        "ts_manifest": assets_dir / "manifest.json",
        "fomod_info": fomod_dir / "info.xml",
        "fomod_moduleconfig": fomod_dir / "ModuleConfig.xml",
        "readme": parent_dir / "README.md",
        "changelog": parent_dir / "CHANGELOG.md",
        "license": parent_dir / "LICENSE.md",
        "mod_il2cpp": bin_dir
        / f"{IL2CPP_BUILD}"
        / "net6"
        / f"{MOD_NAME}-{IL2CPP_BUILD}.dll",
        "mod_mono": bin_dir
        / f"{MONO_BUILD}"
        / "netstandard2.1"
        / f"{MOD_NAME}-{MONO_BUILD}.dll",
    }


def validate_required_files(paths: dict[str, Path], required_keys: list[str]) -> None:
    """Validate that required files exist. Exits on error."""
    missing = []
    for key in required_keys:
        path = paths[key]
        # Extract display name from key
        name = key.replace("_", " ").replace("mod ", "").title()
        if key == "ts_manifest":
            name = "Thunderstore manifest"
        elif key.startswith("fomod"):
            name = f"FOMOD {key.split('_')[1]}"
        elif key.startswith("mod_"):
            build_type = key.split("_")[1].upper()
            name = f"{build_type} build"

        if path.exists():
            console.print(f" [green]✓[/green] {name}")
        else:
            console.print(f" [red]✗[/red] {name} [dim]({path.name})[/dim]")
            missing.append(name)

    if missing:
        error(f"Missing required files: {', '.join(missing)}")


def validate_files(
    paths: dict[str, Path], skip_mono: bool = False, skip_il2cpp: bool = False
) -> None:
    """Validate required files exist for standard builds. Exits on error."""
    required_keys = [
        "icon",
        "ts_manifest",
        "fomod_info",
        "fomod_moduleconfig",
        "readme",
        "changelog",
    ]

    if not skip_il2cpp:
        required_keys.append("mod_il2cpp")
    if not skip_mono:
        required_keys.append("mod_mono")

    validate_required_files(paths, required_keys)

    # Warn about skipped builds
    if skip_mono:
        console.print(f" [dim]⊘ {MONO_BUILD} build (skipped)[/dim]")
    if skip_il2cpp:
        console.print(f" [dim]⊘ {IL2CPP_BUILD} build (skipped)[/dim]")


def create_modified_moduleconfig(
    original_path: Path,
    skip_mono: bool = False,
    skip_il2cpp: bool = False,
    crossplatform: bool = False,
) -> str:
    """Modify ModuleConfig.xml based on packaging mode.

    For cross-platform: replaces plugin list with single S1API option.
    For skip flags: removes unavailable plugins and adjusts "Recommended" status.
    """
    try:
        tree = ET.parse(str(original_path))
    except ET.ParseError as e:
        error(f"Failed to parse ModuleConfig.xml: {e}")

    root = tree.getroot()
    plugins = root.find(".//plugins")

    if plugins is None:
        return original_path.read_text(encoding="utf-8")

    if crossplatform:
        group = plugins.getparent()
        plugin_index = list(group).index(plugins)
        group.remove(plugins)

        new_plugins = ET.Element("plugins")
        new_plugins.set("order", "Explicit")

        cp_plugin = ET.Element("plugin")
        cp_plugin.set("name", "Cross-platform (all versions, via S1API)")

        desc = ET.SubElement(cp_plugin, "description")
        desc.text = (
            "Pick this version if you have S1API installed.\n"
            "This will work on both IL2CPP and Mono versions of the game "
            "(none/beta/alternate/alternate beta)."
        )

        files = ET.SubElement(cp_plugin, "files")
        file_elem = ET.SubElement(files, "file")
        file_elem.set("source", f"{MOD_NAME}.dll")
        file_elem.set("destination", f"Mods/{MOD_NAME}.dll")

        type_desc = ET.SubElement(cp_plugin, "typeDescriptor")
        type_elem = ET.SubElement(type_desc, "type")
        type_elem.set("name", "Recommended")

        new_plugins.append(cp_plugin)
        group.insert(plugin_index, new_plugins)

    else:
        for plugin in list(plugins.findall("plugin")):
            name = plugin.get("name", "")

            if skip_mono and MONO_BUILD in name:
                plugins.remove(plugin)
            elif skip_il2cpp and IL2CPP_BUILD in name:
                plugins.remove(plugin)
            elif skip_il2cpp and MONO_BUILD in name:
                type_desc = plugin.find(".//typeDescriptor/type")
                if type_desc is not None:
                    type_desc.set("name", "Recommended")

    return ET.tostring(root, encoding="unicode")


def create_package(
    paths: dict[str, Path],
    skip_mono: bool = False,
    skip_il2cpp: bool = False,
    crossplatform: bool = False,
) -> Path:
    """Create the distribution ZIP package based on selected build mode."""
    package_path = output_dir / f"{MOD_NAME}.zip"

    if package_path.exists():
        with console.status("[cyan]Removing old package...", spinner="dots"):
            package_path.unlink()

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    files_to_include = {
        paths["icon"]: "icon.png",
        paths["ts_manifest"]: "manifest.json",
        paths["fomod_info"]: "fomod/info.xml",
        paths["readme"]: "README.md",
        paths["changelog"]: "CHANGELOG.md",
    }

    if crossplatform:
        if paths["mod_mono"].exists():
            files_to_include[paths["mod_mono"]] = f"{MOD_NAME}.dll"
    else:
        if not skip_il2cpp and paths["mod_il2cpp"].exists():
            files_to_include[paths["mod_il2cpp"]] = f"{MOD_NAME}-IL2CPP.dll"
        if not skip_mono and paths["mod_mono"].exists():
            files_to_include[paths["mod_mono"]] = f"{MOD_NAME}-Mono.dll"

    if paths["license"].exists():
        files_to_include[paths["license"]] = "LICENSE.md"

    with console.status(f"[cyan]Writing files to ZIP...", spinner="dots"):
        with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file, arcname in files_to_include.items():
                zipf.write(file, arcname)
            # Icon written twice: once for Thunderstore (root), once for FOMOD (fomod/)
            zipf.write(paths["icon"], "fomod/icon.png")

            if skip_mono or skip_il2cpp or crossplatform:
                modified_config = create_modified_moduleconfig(
                    paths["fomod_moduleconfig"], skip_mono, skip_il2cpp, crossplatform
                )
                zipf.writestr("fomod/ModuleConfig.xml", modified_config)
            else:
                zipf.write(paths["fomod_moduleconfig"], "fomod/ModuleConfig.xml")

    return package_path


@app.command()
def package(
    skip_mono: bool = typer.Option(
        False, "--skip-mono", help="Skip Mono build (IL2CPP only)"
    ),
    skip_il2cpp: bool = typer.Option(
        False, "--skip-il2cpp", help="Skip IL2CPP build (Mono only)"
    ),
    crossplatform: bool = typer.Option(
        False,
        "--crossplatform",
        help="Cross-platform build (S1API, uses Mono DLL as base)",
    ),
) -> None:
    """Package the mod into a ZIP file for distribution."""
    mode_count = sum([skip_mono, skip_il2cpp, crossplatform])
    if mode_count > 1:
        error("Only one build mode option allowed at a time")
    if skip_mono and skip_il2cpp:
        error("Cannot skip both Mono and IL2CPP builds")

    step("Validating package files")
    paths = get_build_paths()

    if crossplatform:
        required_keys = [
            "icon",
            "ts_manifest",
            "fomod_info",
            "fomod_moduleconfig",
            "readme",
            "changelog",
            "mod_mono",
        ]
        validate_required_files(paths, required_keys)
        console.print(f" [dim]✦ Cross-platform mode (S1API)[/dim]")
    else:
        validate_files(paths, skip_mono, skip_il2cpp)

    if not paths["license"].exists():
        warn("License file not found - recommended for distribution")

    step("Creating package")
    package_path = create_package(paths, skip_mono, skip_il2cpp, crossplatform)

    # Verify package was created successfully
    try:
        with zipfile.ZipFile(package_path) as zipf:
            file_count = len(zipf.namelist())
            # Quick integrity check
            if zipf.testzip() is not None:
                error("Package created but has corrupted files")
    except zipfile.BadZipFile:
        error("Failed to create valid ZIP package")

    package_size = package_path.stat().st_size / 1024

    ok(f"Packaged {file_count} files")
    console.print(f" [dim]{package_size:.1f} KB[/dim]")
    console.rule(f"[bold green]✓ Ready: [cyan]{package_path.name}[/cyan]")


if __name__ == "__main__":
    app()
