#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["md2bbcode", "rich", "typer"]
# ///
"""
This script converts a Markdown README file to BBCode format suitable for Nexus Mods.
"""

from md2bbcode.main import process_readme
from rich.console import Console
from rich.traceback import install
import typer
import re
import os
from pathlib import Path
from typing import Optional


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
    console.print(f"[bold red]✗[/bold red] {msg}", style="red")


def fix_headings(bbcode: str) -> str:
    """Convert generic HEADING tags to Nexus-compatible size tags."""
    bbcode = re.sub(r"\[HEADING=1\](.*?)\[/HEADING\]", r"[size=5]\1[/size]", bbcode)
    bbcode = re.sub(r"\[HEADING=2\](.*?)\[/HEADING\]", r"[size=4]\1[/size]", bbcode)
    bbcode = re.sub(r"\[HEADING=3\](.*?)\[/HEADING\]", r"[b]\1[/b]", bbcode)
    return bbcode


def fix_image_alt_text(bbcode: str) -> str:
    """Remove alt text from image tags (not supported by Nexus)."""
    return re.sub(r'\[img alt=".*?"\](.*?)\[/img\]', r"[img]\1[/img]", bbcode)


def fix_ordered_lists(bbcode: str) -> str:
    """Convert [list=1] ordered lists to manual numbering (Nexus doesn't support ordered lists)."""
    # Preserve unordered lists temporarily
    preserved = {}

    def preserve(match):
        key = f"__LISTBLOCK_{len(preserved)}__"
        preserved[key] = match.group(0)
        return key

    bbcode = re.sub(r"\[list\](.*?)\[/list\]", preserve, bbcode, flags=re.DOTALL)

    # Convert ordered lists to manual numbering
    def convert_numbered(match):
        raw = match.group(1)
        lines = []
        count = 1
        for part in re.split(r"\[\*\]", raw)[1:]:  # skip empty before first [*]
            part = part.strip()
            if "[list]" in part:
                # Flatten inner bullet list
                sub_items = re.findall(r"\[\*\](.*?)\n?", part, re.DOTALL)
                main_text = part.split("[list]")[0].strip()
                lines.append(f"{count}. {main_text}")
                for sub in sub_items:
                    lines.append(f"    - {sub.strip()}")
            else:
                lines.append(f"{count}. {part.strip()}")
            count += 1
        return "\n".join(lines)

    bbcode = re.sub(
        r"\[list=1\](.*?)\[/list\]", convert_numbered, bbcode, flags=re.DOTALL
    )

    # Restore preserved bullet lists
    for key, val in preserved.items():
        bbcode = bbcode.replace(key, val)

    return bbcode


def fix_inline_code(bbcode: str) -> str:
    """Convert inline code tags to italics (Nexus doesn't support inline code)."""
    return re.sub(
        r"\[icode\](.*?)\[/icode\]", r"[i][font=Courier New]\1[/font][/i]", bbcode
    )


def fix_code_blocks(bbcode: str) -> str:
    """Removes language specifier, changes to lowercase 'code' tag."""
    return re.sub(
        r"\[code=.*?\](.*?)\[/code\]",
        r"[code]\1[/code]",
        bbcode,
        flags=re.DOTALL | re.IGNORECASE,
    )


def better_youtube_links(bbcode: str) -> str:
    """Convert YouTube video links to rich embed format."""
    # youtu.be/VIDEO_ID format
    pattern1 = r"\[url=(https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})[^\]]*)\][^\[]*\[/url\]"
    bbcode = re.sub(pattern1, r"[youtube]\2[/youtube]", bbcode)

    # youtube.com/watch?v=VIDEO_ID format
    pattern2 = r"\[url=(https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})[^\]]*)\][^\[]*\[/url\]"
    bbcode = re.sub(pattern2, r"[youtube]\2[/youtube]", bbcode)

    return bbcode


def fix_tables(bbcode: str) -> str:
    """Convert BBCode tables to monospaced grids inside [code]."""

    def convert_bbcode_table(match):
        block = match.group(1)
        rows_raw = re.findall(
            r"\[TR\](.*?)\[/TR\]", block, flags=re.DOTALL | re.IGNORECASE
        )
        parsed: list[tuple[bool, list[str]]] = []

        for row_raw in rows_raw:
            cells: list[str] = []
            header_row = False
            for cell_match in re.finditer(
                r"\[(TH|TD)\](.*?)\[/\1\]", row_raw, flags=re.DOTALL | re.IGNORECASE
            ):
                tag = cell_match.group(1).upper()
                cell_text = re.sub(r"\s+", " ", cell_match.group(2).strip())
                cells.append(cell_text)
                header_row = header_row or tag == "TH"
            if cells:
                parsed.append((header_row, cells))

        if not parsed:
            return match.group(0)  # give up; return original block

        col_count = max(len(cells) for _, cells in parsed)
        widths = [0] * col_count
        for _, cells in parsed:
            for idx, cell in enumerate(cells):
                widths[idx] = max(widths[idx], len(cell))

        def fmt_row(cells: list[str]) -> str:
            return "  ".join(
                (cells[idx] if idx < len(cells) else "").ljust(widths[idx])
                for idx in range(col_count)
            ).rstrip()

        lines: list[str] = ["[code]"]
        header_idx = next(
            (i for i, (is_header, _) in enumerate(parsed) if is_header), None
        )

        if header_idx is not None:
            header_cells = parsed[header_idx][1]
            lines.append(fmt_row(header_cells))
            lines.append("  ".join("-" * w for w in widths))
            body_iter = (
                cells for j, (is_header, cells) in enumerate(parsed) if j != header_idx
            )
        else:
            body_iter = (cells for _, cells in parsed)

        for cells in body_iter:
            lines.append(fmt_row(cells))

        lines.append("[/code]")
        return "\n".join(lines)

    return re.sub(
        r"\[TABLE\](.*?)\[/TABLE\]",
        convert_bbcode_table,
        bbcode,
        flags=re.DOTALL | re.IGNORECASE,
    )


def fix_horizontal_rules(bbcode: str) -> str:
    """Replace unsupported [hr] tags with blank lines for visual separation."""
    return re.sub(r"\[hr\]\[/hr\]", "\n\n", bbcode)


FIXES = [
    fix_headings,
    fix_image_alt_text,
    fix_ordered_lists,
    fix_inline_code,
    fix_code_blocks,
    better_youtube_links,
    fix_tables,
    fix_horizontal_rules,
]


def apply_nexusmods_fixes(bbcode: str) -> str:
    """Apply all registered BBCode fixes for Nexus Mods compatibility."""
    for fix_func in FIXES:
        bbcode = fix_func(bbcode)
    return bbcode


@app.command()
def main(
    readme_path: str = typer.Argument(
        "README.md",
        help="Path to input Markdown README file.",
    ),
    output_path: str = typer.Argument(
        "README.bbcode",
        help="Path to output BBCode file.",
    ),
) -> None:
    """Convert a Markdown README file to BBCode format suitable for Nexus Mods."""

    # Try to find README.md if default path doesn't exist
    readme_file = Path(readme_path)
    if not readme_file.exists() and readme_path == "README.md":
        parent_readme = Path("..") / readme_path
        if parent_readme.exists():
            readme_file = parent_readme
        else:
            error(f"Input file '[yellow]{readme_path}[/yellow]' not found.")
            raise typer.Exit(code=1)
    elif not readme_file.exists():
        error(f"Input file '[yellow]{readme_path}[/yellow]' not found.")
        raise typer.Exit(code=1)

    markdown_text = readme_file.read_text(encoding="utf-8")

    step("Converting README to BBCode")
    with console.status("[cyan]Processing markdown...", spinner="dots"):
        bbcode_output = process_readme(markdown_text)
        bbcode_output_fixed = apply_nexusmods_fixes(bbcode_output)

    Path(output_path).write_text(bbcode_output_fixed, encoding="utf-8")

    ok(
        f"Converted [bold yellow]{readme_file}[/bold yellow] to Nexus-compatible BBCode at [bold blue]{output_path}[/bold blue]"
    )


if __name__ == "__main__":
    app()
