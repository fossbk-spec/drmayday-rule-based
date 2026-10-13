# Thiết lập máy mới cho drmayday-rule-based (Windows PowerShell 5.1+).
# Chạy tại thư mục gốc repo:
#   powershell -ExecutionPolicy Bypass -File tools\setup_machine.ps1            # venv + dependency + test
#   powershell -ExecutionPolicy Bypass -File tools\setup_machine.ps1 -ForCodex  # thêm: Python trong thư mục sandbox Codex đọc được
param(
    [string]$Python = "python",
    [switch]$ForCodex,
    [string]$ToolsDir = "",
    [string]$VenvPath = ".venv"
)
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

$basePrefix = (& $Python -c "import sys; print(sys.base_prefix)").Trim()
$version = (& $Python -c "import sys; print('%d%d' % sys.version_info[:2])").Trim()
Write-Host "Python gốc: $basePrefix (3.$($version.Substring(1)))"

$venvPython = $Python
if ($ForCodex) {
    # Sandbox Codex trên Windows không đọc được Python trong %LOCALAPPDATA%:
    # copy runtime vào thư mục cạnh repo rồi tạo venv từ bản copy.
    if (-not $ToolsDir) { $ToolsDir = Join-Path (Split-Path -Parent $Repo) ".tools" }
    $target = Join-Path $ToolsDir "python$version"
    if (-not (Test-Path (Join-Path $target "python.exe"))) {
        Write-Host "Copy Python sang $target"
        robocopy $basePrefix $target /E /XD __pycache__ site-packages /NFL /NDL /NJH /NJS /NP /R:1 /W:1 | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy thất bại ($LASTEXITCODE)" }
        New-Item -ItemType Directory -Force (Join-Path $target "Lib\site-packages") | Out-Null
    }
    $venvPython = Join-Path $target "python.exe"
}

if (Test-Path $VenvPath) {
    Write-Host "Đã có $VenvPath - giữ nguyên (xóa thư mục này nếu muốn tạo lại)."
} else {
    & $venvPython -m venv $VenvPath
}
$py = Join-Path $VenvPath "Scripts\python.exe"
& $py -m pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "pip install thất bại" }

$env:PYTHONDONTWRITEBYTECODE = "1"
& $py -X utf8 -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) { throw "Test thất bại" }
& $py -X utf8 tools\check_packages.py
& $py -X utf8 tools\build_fields.py --check

Write-Host ""
Write-Host "Xong. Chạy demo: $py -m streamlit run main.py"
Write-Host "Tiếp tục với Claude Code: mở thư mục repo và dán câu lệnh trong docs/HANDOFF.md mục 0."
if ($ForCodex) {
    Write-Host "Kiểm tra Codex (tùy chọn, ~20k token):"
    Write-Host '  codex exec -s read-only -C . "Run: .venv\Scripts\python.exe -X utf8 -m unittest discover -s tests ; reply with the last line only"'
}
