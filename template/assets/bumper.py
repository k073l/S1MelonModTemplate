#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich", "typer"]
# ///
"""
This tool can be used to bump version numbers and update descriptions
"""

from pathlib import Path
from rich.console import Console
from rich.traceback import install
import typer
import json
import re
import xml.etree.ElementTree as ET

app = typer.Typer()
console = Console()
install(console=console)


def step(msg: str) -> None:
    """Print a step message."""
    console.print(f"\n[bold blue]▸[/bold blue] [bold]{msg}[/bold]")


def ok(msg: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {msg}", style="green")


def is_semver(version: str) -> bool:
    """Check if version string is valid semantic versioning (X.Y.Z)."""
    pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    return re.match(pattern, version) is not None


# Files to update with their field names for each property
FILES = {
    "MainMod.cs": {
        "version": "Version",
        "description": "Description",
        "author": "Author",
    },
    "assets/manifest.json": {"version": "version_number", "description": "description"},
    "assets/fomod/info.xml": {
        "version": "Version",
        "description": "Description",
        "author": "Author",
    },
}


def update_json(filepath: str, key: str, val: str) -> bool:
    """Update a JSON file at the given key with the given value. Returns True if successful."""
    try:
        if not Path(filepath).exists():
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        data[key] = val
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except (json.JSONDecodeError, KeyError, IOError) as e:
        console.log(f"[red]Error: {e}[/red]")
        return False


def update_xml(filepath: str, tag: str, val: str) -> bool:
    """Update an XML file at the given tag with the given value. Returns True if successful."""
    try:
        if not Path(filepath).exists():
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        root = ET.fromstring(content)
        element = root.find(tag)
        if element is not None:
            element.text = val
            tree = ET.ElementTree(root)
            tree.write(filepath, encoding="utf-8", xml_declaration=True)
            return True
        else:
            return False
    except ET.ParseError as e:
        console.log(f"[red]Error: {e}[/red]")
        return False


def update_cs(filepath: str, field: str, val: str) -> bool:
    """Update a C# const field with the given value. Returns True if successful."""
    try:
        if not Path(filepath).exists():
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        # Match: public const string FieldName = "old_value";
        pattern = rf'(public const string {field} = )"[^"]*"'
        replacement = rf'\1"{val}"'
        updated = re.sub(pattern, replacement, content)
        if updated == content:
            return False
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(updated)
        return True
    except IOError as e:
        console.log(f"[red]Error: {e}[/red]")
        return False


@app.command()
def version(version: str = typer.Argument(..., help="The new version number to set")):
    """Bump the version number in the specified files."""
    if not is_semver(version):
        console.print(
            f"[yellow]⚠[/yellow] [yellow]Invalid version format: {version}[/yellow]"
        )
        console.print(
            f"[dim]Expected semantic versioning (e.g., 1.0.0, 2.1.3-alpha)[/dim]"
        )

    step(f"Setting version to [cyan]{version}[/cyan]")
    updated_count = 0
    for filepath, keys in FILES.items():
        ext = filepath.split(".")[-1]
        success = False
        with console.status(f"[cyan]Updating {filepath}...", spinner="dots"):
            match ext:
                case "json":
                    success = update_json(filepath, keys["version"], version)
                case "xml":
                    success = update_xml(filepath, keys["version"], version)
                case "cs":
                    success = update_cs(filepath, keys["version"], version)
        if success:
            ok(f"[cyan]{filepath}[/cyan]")
            updated_count += 1
    console.rule(f"[bold green]✓ Updated {updated_count}/{len(FILES)} file(s)")


@app.command()
def description(
    description: str = typer.Argument(..., help="The new description to set")
):
    """Update the mod description in the specified files."""
    step(f"Setting description to [cyan]{description}[/cyan]")
    updated_count = 0
    for filepath, keys in FILES.items():
        ext = filepath.split(".")[-1]
        success = False
        with console.status(f"[cyan]Updating {filepath}...", spinner="dots"):
            match ext:
                case "cs":
                    success = update_cs(filepath, keys["description"], description)
                case "json":
                    success = update_json(filepath, keys["description"], description)
                case "xml":
                    success = update_xml(filepath, keys["description"], description)
        if success:
            ok(f"[cyan]{filepath}[/cyan]")
            updated_count += 1
    console.rule(f"[bold green]✓ Updated {updated_count}/{len(FILES)} file(s)")


@app.command()
def author(author: str = typer.Argument(..., help="The new author name to set")):
    """Update the mod author in FOMOD info.xml and MainMod.cs."""
    step(f"Setting author to [cyan]{author}[/cyan]")
    updated_count = 0
    for filepath, keys in FILES.items():
        if "author" not in keys:
            continue
        ext = filepath.split(".")[-1]
        success = False
        with console.status(f"[cyan]Updating {filepath}...", spinner="dots"):
            match ext:
                case "cs":
                    success = update_cs(filepath, keys["author"], author)
                case "xml":
                    success = update_xml(filepath, keys["author"], author)
        if success:
            ok(f"[cyan]{filepath}[/cyan]")
            updated_count += 1
    console.rule(f"[bold green]✓ Updated {updated_count} file(s)")


if __name__ == "__main__":
    app()
