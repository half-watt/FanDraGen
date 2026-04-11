if (Test-Path ".venv/Scripts/python.exe") {
	$PythonCmd = (Resolve-Path ".venv/Scripts/python.exe").Path
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
	$PythonCmd = "python"
} else {
	$PythonCmd = "py"
}

& $PythonCmd -m pytest -q