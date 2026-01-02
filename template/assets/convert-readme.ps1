$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$uvInstallScript = "$root\uv-install.ps1"
$uvExe = "$root\uv.exe"
$envDir = "$root\.temp_env"
$pythonScript = "$root\convert_readme.py"
$reqPackage = "md2bbcode"
$readmePath = "$root\..\README.md"
$nexusReadmePath = "$root\..\README-nexus.txt"

# Download uv install script and run it locally
if (-not (Test-Path $uvExe)) {
    Write-Host "Downloading uv install script..."
    Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -UseBasicParsing -OutFile $uvInstallScript
    Write-Host "Installing uv via script..."
    & powershell -ExecutionPolicy Bypass -File $uvInstallScript
    
    $homeUvPath = "$env:USERPROFILE\.local\bin\uv.exe"
    if (Test-Path $homeUvPath) {
        Copy-Item $homeUvPath $uvExe -Force
        # Optionally clean up user install
        Remove-Item $homeUvPath -Force -ErrorAction SilentlyContinue
        Remove-Item "$env:USERPROFILE\.local\bin\uvx.exe" -Force -ErrorAction SilentlyContinue
    } else {
        throw "Failed to install uv.exe"
    }
    Remove-Item $uvInstallScript -Force
}

# Write Python script to disk
@"
"""
This script converts a Markdown README file to BBCode format suitable for Nexus Mods.
"""
from md2bbcode.main import process_readme
import re

readme_path = r'''$readmePath'''
output_path = r'''$nexusReadmePath'''

def fix_bbcode_for_nexusmods(bbcode: str) -> str:
    # fix headings
    bbcode = re.sub(r'\[HEADING=1\](.*?)\[/HEADING\]', r'[size=5]\1[/size]', bbcode)
    bbcode = re.sub(r'\[HEADING=2\](.*?)\[/HEADING\]', r'[size=4]\1[/size]', bbcode)
    bbcode = re.sub(r'\[HEADING=3\](.*?)\[/HEADING\]', r'[b]\1[/b]', bbcode)

    # remove alt text
    bbcode = re.sub(r'\[img alt=".*?"\](.*?)\[/img\]', r'[img]\1[/img]', bbcode)

    # preserve unordered lists
    preserved = {}
    def preserve(match):
        key = f"__LISTBLOCK_{len(preserved)}__"
        preserved[key] = match.group(0)
        return key
    bbcode = re.sub(r'\[list\](.*?)\[/list\]', preserve, bbcode, flags=re.DOTALL)

    # convert ordered lists to manual numbering
    def convert_numbered(match):
        raw = match.group(1)
        lines = []
        count = 1
        for part in re.split(r'\[\*\]', raw)[1:]:  # skip empty before first [*]
            part = part.strip()
            if '[list]' in part:
                # flatten inner bullet list
                sub_items = re.findall(r'\[\*\](.*?)\n?', part, re.DOTALL)
                main_text = part.split('[list]')[0].strip()
                lines.append(f'{count}. {main_text}')
                for sub in sub_items:
                    lines.append(f'    - {sub.strip()}')
            else:
                lines.append(f'{count}. {part.strip()}')
            count += 1
        return '\n'.join(lines)

    bbcode = re.sub(r'\[list=1\](.*?)\[/list\]', convert_numbered, bbcode, flags=re.DOTALL)

    # restore preserved bullet lists
    for key, val in preserved.items():
        bbcode = bbcode.replace(key, val)

    return bbcode

with open(readme_path, "r", encoding="utf-8") as file:
    markdown_text = file.read()
    bbcode_output = process_readme(markdown_text)
    bbcode_output_fixed = fix_bbcode_for_nexusmods(bbcode_output)

with open(output_path, "w", encoding="utf-8") as out:
    out.write(bbcode_output_fixed)
"@ | Set-Content -Encoding UTF8 $pythonScript

if (-not (Test-Path $readmePath)) {
    throw "README.md not found"
}

# Use embedded Python from uv (not Store)
Write-Host "Creating virtual environment with embedded Python..."
& $uvExe venv $envDir --python 3.12
& "$envDir\Scripts\python.exe" -m ensurepip --upgrade
& "$envDir\Scripts\python.exe" -m pip install --upgrade pip
& "$envDir\Scripts\python.exe" -m pip install $reqPackage

# Run converter
Write-Host "`nRunning converter..."
& "$envDir\Scripts\python.exe" $pythonScript

# Cleanup
Write-Host "`nCleaning up..."
Remove-Item $envDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $pythonScript -Force -ErrorAction SilentlyContinue
Remove-Item $uvExe -Force

Write-Host "`n✅ Done. Output saved to $nexusReadmePath"
