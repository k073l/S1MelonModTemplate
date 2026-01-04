#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich", "typer"]
# ///
r"""
Post-build helper for S1 mods: kill running game, clean mods dir, copy extras,
copy the built mod, and launch (with Wine/Proton support on non-Windows).

Windows usage:
    python postbuild.py MyMod.dll "C:/Games/S1/Mods" "C:/Games/S1/Schedule I.exe"

macOS/Linux with Wine:
    python postbuild.py MyMod.dll ~/Games/S1/Mods ~/Games/S1/Schedule\ I.exe \
        --wine-binary wine64 --wine-prefix ~/.wine

Proton (Steam on Linux):
    python postbuild.py MyMod.dll \
        ~/.steam/steam/steamapps/compatdata/APPID/pfx/drive_c/.../Mods \
        ~/.steam/steam/steamapps/compatdata/APPID/pfx/drive_c/.../Schedule\ I.exe \
        --wine-binary ~/.steam/steam/steamapps/common/Proton\ 9.0/proton \
        --wine-prefix ~/.steam/steam/steamapps/compatdata/APPID/pfx
"""

import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.traceback import install as rich_traceback_install


def _supports_unicode() -> bool:
    """Check if the console supports Unicode output."""
    try:
        encoding = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
        return encoding.lower() not in ["cp1250", "cp437", "ascii"]
    except Exception:
        return True


# Create console with appropriate settings based on Unicode support
if _supports_unicode():
    console = Console()
else:
    # For limited encodings, disable all markup and colors
    console = Console(markup=False, highlight=False, force_terminal=False)

rich_traceback_install(show_locals=False)


def info(msg: str) -> None:
    if _supports_unicode():
        try:
            console.print(f"[dim cyan]→[/dim cyan] {msg}", style="cyan")
        except Exception:
            console.print(f"[dim cyan]>[/dim cyan] {msg}", style="cyan")
    else:
        print(f"> {msg}")


def warn(msg: str) -> None:
    if _supports_unicode():
        try:
            console.print(f"[yellow]⚠[/yellow] {msg}", style="yellow")
        except Exception:
            console.print(f"[yellow]![/yellow] {msg}", style="yellow")
    else:
        print(f"! {msg}")


def error(msg: str) -> None:
    if _supports_unicode():
        try:
            console.print(f"[bold red]✗[/bold red] {msg}", style="red")
        except Exception:
            console.print(f"[bold red]x[/bold red] {msg}", style="red")
    else:
        print(f"x {msg}")


def ok(msg: str) -> None:
    if _supports_unicode():
        try:
            console.print(f"[green]✓[/green] {msg}", style="green")
        except Exception:
            console.print(f"[green]+[/green] {msg}", style="green")
    else:
        print(f"+ {msg}")


def step(msg: str) -> None:
    if _supports_unicode():
        try:
            console.print(f"\n[bold blue]▸[/bold blue] [bold]{msg}[/bold]")
        except Exception:
            console.print(f"\n[bold blue]o[/bold blue] [bold]{msg}[/bold]")
    else:
        # Plain ASCII output for limited encodings
        print(f"\no {msg}")


def clean_mods_dir(mods_dir_path: Path) -> None:
    """Clean the mods directory before copying new mods."""
    step("Cleaning mods directory")
    if not mods_dir_path.exists():
        info("Mods directory doesn't exist, will be created")
        return

    with console.status("[cyan]Removing old mods...", spinner="line"):
        for item in mods_dir_path.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except Exception as e:
                warn(f"Failed to remove {item.name}: {e}")

    ok("Mods directory cleaned")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_item(
    src: Path,
    dst_dir: Path,
    progress: Optional[Progress] = None,
    task_id: Optional[int] = None,
) -> None:
    """Copy a file or directory to destination directory."""
    target = dst_dir / src.name
    if progress is None:
        info(f"Copying [cyan]{src.name}[/cyan] to [blue]{dst_dir}[/blue]")
    if src.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src, target)
    else:
        shutil.copy2(src, target)
    if progress and task_id is not None:
        progress.advance(task_id)


def find_subdir_case_insensitive(parent: Path, name: str) -> Optional[Path]:
    """Find a subdirectory with case-insensitive name matching."""
    if not parent.exists():
        return None
    name_lower = name.lower()
    for item in parent.iterdir():
        if item.is_dir() and item.name.lower() == name_lower:
            return item
    return None


def copy_structured_mod(mod_path: Path, dst_mods_dir: Path) -> None:
    """Copy structured mod with Mods/Plugins/UserLibs subdirectories to game directories.

    Given dst_mods_dir = <game_dir>/Mods:
    - Mods/* -> <game_dir>/Mods/
    - Plugins/* -> <game_dir>/Plugins/
    - UserLibs/* -> <game_dir>/UserLibs/
    """
    mod_path = mod_path.resolve()
    if not mod_path.exists():
        warn(f"Mod not found: [yellow]{mod_path}[/yellow]")
        return

    info(f"Copying [cyan]{mod_path.name}[/cyan] structure")

    mods_subdir = find_subdir_case_insensitive(mod_path, "Mods")
    if mods_subdir:
        for item in mods_subdir.iterdir():
            try:
                if item.is_file():
                    shutil.copy2(item, dst_mods_dir / item.name)
                elif item.is_dir():
                    target = dst_mods_dir / item.name
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
            except Exception as e:
                warn(f"Failed to copy {item.name}: {e}")

    plugins_subdir = find_subdir_case_insensitive(mod_path, "Plugins")
    if plugins_subdir:
        plugins_dst = dst_mods_dir.parent / "Plugins"
        plugins_dst.mkdir(parents=True, exist_ok=True)
        for item in plugins_subdir.iterdir():
            try:
                if item.is_file():
                    shutil.copy2(item, plugins_dst / item.name)
                elif item.is_dir():
                    target = plugins_dst / item.name
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
            except Exception as e:
                warn(f"Failed to copy {item.name}: {e}")

    userlibs_subdir = find_subdir_case_insensitive(mod_path, "UserLibs")
    if userlibs_subdir:
        userlibs_dst = dst_mods_dir.parent / "UserLibs"
        userlibs_dst.mkdir(parents=True, exist_ok=True)
        for item in userlibs_subdir.iterdir():
            try:
                if item.is_file():
                    shutil.copy2(item, userlibs_dst / item.name)
                elif item.is_dir():
                    target = userlibs_dst / item.name
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
            except Exception as e:
                warn(f"Failed to copy {item.name}: {e}")


def copy_mod_item(
    mod_path: Path,
    dst_dir: Path,
    skip_if_exists: bool = False,
    show_timestamp: bool = False,
) -> bool:
    """Copy a mod - handles single DLL files, flat folders, and structured mods.

    Returns True if copied, False if skipped.
    """
    mod_path = mod_path.resolve()
    if not mod_path.exists():
        warn(f"Mod not found: [yellow]{mod_path}[/yellow]")
        return False

    if show_timestamp and mod_path.is_file():
        mtime = datetime.fromtimestamp(mod_path.stat().st_mtime)
        info(f"  [dim]Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

    if mod_path.is_file():
        target = dst_dir / mod_path.name
        if skip_if_exists and target.exists():
            info(f"[dim]Skipping [cyan]{mod_path.name}[/cyan] (already exists)[/dim]")
            return False
        info(f"Copying mod file [cyan]{mod_path.name}[/cyan]")
        try:
            shutil.copy2(mod_path, target)
            return True
        except Exception as e:
            warn(f"Failed to copy {mod_path.name}: {e}")
            return False

    has_structure = any(
        find_subdir_case_insensitive(mod_path, subdir) is not None
        for subdir in ["Mods", "Plugins", "UserLibs"]
    )

    if has_structure:
        if skip_if_exists:
            mods_subdir = find_subdir_case_insensitive(mod_path, "Mods")
            if mods_subdir:
                has_existing = any(
                    (dst_dir / item.name).exists() for item in mods_subdir.iterdir()
                )
                if has_existing:
                    info(
                        f"[dim]Skipping [cyan]{mod_path.name}[/cyan] (already exists)[/dim]"
                    )
                    return False
        info(f"Copying structured mod [cyan]{mod_path.name}[/cyan]")
        copy_structured_mod(mod_path, dst_dir)
        return True
    else:
        target = dst_dir / mod_path.name
        if skip_if_exists and target.exists():
            info(f"[dim]Skipping [cyan]{mod_path.name}[/cyan] (already exists)[/dim]")
            return False
        info(f"Copying mod folder [cyan]{mod_path.name}[/cyan]")
        try:
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(mod_path, target)
            return True
        except Exception as e:
            warn(f"Failed to copy {mod_path.name}: {e}")
            return False


def _is_windows() -> bool:
    return os.name == "nt"


def _find_wineserver(wine_prefix: Optional[str] = None) -> Optional[str]:
    """Find wineserver binary. Checks for Proton-style wineserver first, then PATH."""
    if wine_prefix:
        prefix_path = Path(wine_prefix)
        proton_wineserver = prefix_path / "dist" / "bin" / "wineserver"
        if proton_wineserver.exists():
            return str(proton_wineserver)

    result = subprocess.run(
        ["which", "wineserver"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()

    return None


def kill_processes(
    exe_name: str,
    wait_seconds: float,
    use_wine: bool = False,
    wine_prefix: Optional[str] = None,
) -> None:
    """Kill game processes. Uses wineserver -k on Unix for graceful Wine shutdown."""
    step(f"Terminating [yellow]{exe_name}[/yellow]")

    if _is_windows():
        with console.status(f"[cyan]Sending termination signal...", spinner="line"):
            subprocess.run(
                ["taskkill", "/F", "/IM", exe_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
    else:
        wineserver = _find_wineserver(wine_prefix)

        with console.status(f"[cyan]Shutting down Wine processes...", spinner="line"):
            if wineserver:
                env = os.environ.copy()
                if wine_prefix:
                    env["WINEPREFIX"] = wine_prefix
                subprocess.run(
                    [wineserver, "-k"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                time.sleep(0.5)

            subprocess.run(
                ["pkill", "-f", exe_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )

    wait_for_exit(exe_name, wait_seconds, use_wine, wine_prefix)


def wait_for_exit(
    exe_name: str,
    wait_seconds: float,
    use_wine: bool = False,
    wine_prefix: Optional[str] = None,
) -> None:
    """Wait for process to exit, with timeout."""
    deadline = time.time() + wait_seconds + 2.0
    with console.status(f"[cyan]Waiting for process to exit...", spinner="line"):
        while time.time() < deadline:
            if not is_running(exe_name, use_wine, wine_prefix):
                ok(f"[yellow]{exe_name}[/yellow] stopped")
                return
            time.sleep(0.2)
    warn(f"[yellow]{exe_name}[/yellow] may still be running")


def is_running(
    exe_name: str, use_wine: bool = False, wine_prefix: Optional[str] = None
) -> bool:
    """Check if process is running. On Unix, checks for Wine processes running the exe."""
    if _is_windows():
        res = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}"],
            capture_output=True,
            text=True,
            check=False,
        )
        return exe_name.lower() in res.stdout.lower()

    try:
        result = subprocess.run(
            ["pgrep", "-a", "-f", exe_name],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and exe_name in result.stdout
    except Exception:
        return False


def launch_game(
    exe_path: Path,
    args: List[str],
    use_wine: bool,
    wine_binary: str,
    wine_prefix: Optional[str],
    working_dir: Path,
) -> None:
    """Launch the game executable, with Wine support on Unix."""
    env = os.environ.copy()
    cmd: List[str]
    if use_wine:
        if wine_prefix:
            env["WINEPREFIX"] = wine_prefix
        env["WINEDLLOVERRIDES"] = "version=n,b"
        cmd = [wine_binary, str(exe_path), *args]
    else:
        cmd = [str(exe_path), *args]

    step(f"Launching game: [dim]{' '.join(cmd)}[/dim]")
    subprocess.Popen(
        cmd,
        cwd=working_dir,
        env=env,
    )


def copy_user_mods(
    mod_list: List[str],
    base: Path,
    mods_dir_path: Path,
    force_copy: bool = False,
    show_timestamps: bool = False,
) -> int:
    """Copy user-specified mods with progress tracking. Returns count copied."""
    if not mod_list:
        return 0

    step("Copying requested mods")
    valid_mods = []
    for mod_entry in mod_list:
        mod_path = (
            (base / mod_entry).resolve()
            if not Path(mod_entry).is_absolute()
            else Path(mod_entry)
        )
        if not mod_path.exists():
            warn(f"Mod not found: [yellow]{mod_path}[/yellow]")
            continue
        valid_mods.append(mod_path)

    copied_count = 0
    if valid_mods:
        with Progress(
            SpinnerColumn(spinner="line"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Copying mods...", total=len(valid_mods))
            for mod_path in valid_mods:
                progress.update(task, description=f"[cyan]Copying {mod_path.name}")
                if copy_mod_item(
                    mod_path,
                    mods_dir_path,
                    skip_if_exists=not force_copy,
                    show_timestamp=show_timestamps,
                ):
                    copied_count += 1
                progress.advance(task)

    return copied_count


def copy_multiplayer_mods(
    mp_mod: str, mp_starter: str, mods_dir_path: Path, force_copy: bool = False
) -> int:
    """Copy multiplayer mod DLL to Mods/ and starter script to game directory.

    Returns count of items copied.
    """
    step("Copying multiplayer extras")
    count = 0

    mp_mod_path = Path(mp_mod).resolve()
    if not mp_mod_path.exists():
        warn(f"Multiplayer mod not found: [yellow]{mp_mod}[/yellow]")
    else:
        with console.status("[cyan]Copying multiplayer mod...", spinner="line"):
            if copy_mod_item(mp_mod_path, mods_dir_path, skip_if_exists=not force_copy):
                ok("Multiplayer mod copied")
                count += 1
            else:
                ok("Multiplayer mod already present")

    starter_src = Path(mp_starter).resolve()
    if not starter_src.exists():
        warn(f"Multiplayer starter not found: [yellow]{mp_starter}[/yellow]")
    else:
        starter_dst = mods_dir_path.parent / starter_src.name
        if not starter_dst.exists() or force_copy:
            with console.status("[cyan]Copying multiplayer starter...", spinner="line"):
                try:
                    shutil.copy2(starter_src, starter_dst)
                    ok("Multiplayer starter copied")
                    count += 1
                except Exception as e:
                    warn(f"Failed to copy multiplayer starter: {e}")
        else:
            ok("Multiplayer starter already present")

    return count


def copy_library_mods(
    s1api_path: Optional[str],
    unity_explorer_path: Optional[str],
    mods_dir_path: Path,
    force_copy: bool = False,
) -> int:
    """Copy library mods (S1API, UnityExplorer). Returns count copied."""
    count = 0

    if s1api_path:
        step("Copying S1API")
        with console.status("[cyan]Copying S1API...", spinner="line"):
            if copy_mod_item(
                Path(s1api_path).resolve(),
                mods_dir_path,
                skip_if_exists=not force_copy,
            ):
                count += 1

    if unity_explorer_path:
        step("Copying UnityExplorer")
        with console.status("[cyan]Copying UnityExplorer...", spinner="line"):
            if copy_mod_item(
                Path(unity_explorer_path).resolve(),
                mods_dir_path,
                skip_if_exists=not force_copy,
            ):
                count += 1

    return count


app = typer.Typer()


@app.command()
def main(
    target: str = typer.Argument(..., help="Built mod file to copy."),
    mods_dir: str = typer.Argument(..., help="Destination mods directory."),
    exe_path: str = typer.Argument(..., help="Game executable path."),
    project_dir: str = typer.Option(".", help="Project directory for relative paths."),
    wait_seconds: float = typer.Option(1.0, help="Seconds to wait after kill."),
    launch_delay: float = typer.Option(
        0.0, help="Seconds to wait before launching game."
    ),
    mod: List[str] = typer.Option([], help="Extra mod to copy (repeatable)."),
    mp_mod: Optional[str] = typer.Option(None, help="Path to multiplayer mod folder."),
    mp_starter: Optional[str] = typer.Option(None, help="Path to multiplayer starter."),
    s1api_path: Optional[str] = typer.Option(None, help="Path to S1API mod folder."),
    unity_explorer_path: Optional[str] = typer.Option(
        None, help="Path to UnityExplorer mod folder."
    ),
    debug: bool = typer.Option(False, help="Launch with melonloader debug flags."),
    clean: bool = typer.Option(False, help="Clean mods directory before copying."),
    no_launch: bool = typer.Option(False, help="Skip game launch after copying."),
    force_copy: bool = typer.Option(
        False, help="Force copy all mods even if they exist."
    ),
    show_timestamps: bool = typer.Option(False, help="Show mod file timestamps."),
    wine_binary: str = typer.Option("wine", help="Wine binary (for non-Windows)."),
    wine_prefix: Optional[str] = typer.Option(None, help="Wine prefix (non-Windows)."),
) -> None:
    """Post-build helper for S1 mods.

    Kills running game, copies mods, and launches game.
    Supports Windows (native), macOS/Linux (Wine), and Proton.

    Multiplayer mode automatically enabled when both --mp-mod and --mp-starter provided.
    """
    base = Path(project_dir).resolve()
    mods_dir_path = Path(mods_dir).resolve()
    target_path = Path(target).resolve()
    exe_path_obj = Path(exe_path).resolve()
    exe_name = exe_path_obj.name
    use_wine = not _is_windows()

    if not target_path.exists():
        error(f"Target not found: [yellow]{target_path}[/yellow]")
        raise typer.Exit(code=1)

    multiplayer = bool(mp_mod and mp_starter)

    if mp_mod and not mp_starter:
        error(
            "Multiplayer mod provided but starter missing. Provide both --mp-mod and --mp-starter"
        )
        raise typer.Exit(code=1)
    if mp_starter and not mp_mod:
        error(
            "Multiplayer starter provided but mod missing. Provide both --mp-mod and --mp-starter"
        )
        raise typer.Exit(code=1)

    if use_wine:
        wine_type = "Proton" if "proton" in wine_binary.lower() else "Wine"
        info(f"Using {wine_type} configuration:")
        info(f"  Binary: {wine_binary}")
        info(f"  Prefix: {wine_prefix or '(default)'}")

        if not Path(wine_binary).exists():
            error(f"{wine_type} binary not found: {wine_binary}")
            raise typer.Exit(code=1)

    ensure_dir(mods_dir_path)

    total_copied = 0

    kill_processes(exe_name, wait_seconds, use_wine, wine_prefix)

    if clean:
        clean_mods_dir(mods_dir_path)

    total_copied += copy_user_mods(
        mod, base, mods_dir_path, force_copy, show_timestamps
    )

    if multiplayer:
        total_copied += copy_multiplayer_mods(
            mp_mod, mp_starter, mods_dir_path, force_copy
        )

    total_copied += copy_library_mods(
        s1api_path, unity_explorer_path, mods_dir_path, force_copy
    )

    step("Copying built mod")
    with console.status(
        f"[cyan]Copying [yellow]{target_path.name}[/yellow]...", spinner="line"
    ):
        copy_item(target_path, mods_dir_path)
    total_copied += 1

    if no_launch:
        info("Skipping game launch (--no-launch)")
        if _supports_unicode():
            console.print(f"\n[dim]Copied {total_copied} items total[/dim]")
            try:
                console.rule("[bold green]✓ Post-build completed successfully")
            except Exception:
                console.rule("[bold green]+ Post-build completed successfully")
        else:
            print(f"\nCopied {total_copied} items total")
            print("+ Post-build completed successfully")
        return

    if launch_delay > 0:
        step(f"Waiting {launch_delay}s before launch")
        time.sleep(launch_delay)

    launch_args = []
    if debug:
        launch_args.extend(["--melonloader.debug"])

    if not multiplayer:
        launch_game(
            exe_path=exe_path_obj,
            args=launch_args,
            use_wine=use_wine,
            wine_binary=wine_binary,
            wine_prefix=wine_prefix,
            working_dir=exe_path_obj.parent,
        )
    else:
        step("Launching multiplayer starter")
        starter_path = mods_dir_path.parent / Path(mp_starter).name

        if _is_windows():
            subprocess.Popen(
                ["cmd", "/k", str(starter_path), *launch_args],
                cwd=mods_dir_path.parent,
                creationflags=subprocess.CREATE_NEW_CONSOLE
                | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
            )
        else:
            subprocess.Popen(
                [str(starter_path)],
                cwd=mods_dir_path.parent,
                start_new_session=True,
            )

    if _supports_unicode():
        console.print(f"\n[dim]Copied {total_copied} items total[/dim]")
        try:
            console.rule("[bold green]✓ Post-build completed successfully")
        except Exception:
            console.rule("[bold green]+ Post-build completed successfully")
    else:
        print(f"\nCopied {total_copied} items total")
        print("+ Post-build completed successfully")


if __name__ == "__main__":
    app()
