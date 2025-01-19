$scriptDir = [System.IO.Path]::GetDirectoryName([System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName)
$pythonFilePath = Join-Path -Path $scriptDir -ChildPath "main.py"

if (Test-Path -Path $pythonFilePath) {
    Start-Process "python3" -ArgumentList $pythonFilePath -WindowStyle Hidden
} else {
    Write-Error "The file 'main.py' does not exist at the specified path."
}
