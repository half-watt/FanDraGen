param(
    [int]$Sample = 0,
    [string]$Prompt = ""
)

if (Test-Path ".venv/Scripts/python.exe") {
    $PythonCmd = (Resolve-Path ".venv/Scripts/python.exe").Path
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} else {
    $PythonCmd = "py"
}

if ($Prompt) {
    & $PythonCmd main.py --prompt "$Prompt"
} else {
    & $PythonCmd main.py --sample $Sample
}