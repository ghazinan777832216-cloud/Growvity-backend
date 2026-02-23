$paths = @(
    "c:\Users\hisham\Desktop\compute_test\parametric-platform\Growvity\backend\Include",
    "c:\Users\hisham\Desktop\compute_test\parametric-platform\Growvity\backend\Lib",
    "c:\Users\hisham\Desktop\compute_test\parametric-platform\Growvity\backend\Scripts",
    "c:\Users\hisham\Desktop\compute_test\parametric-platform\Growvity\backend\pyvenv.cfg",
    "c:\Users\hisham\Desktop\compute_test\parametric-platform\Growvity\backend\cleanup_venv.py"
)

foreach ($path in $paths) {
    if (Test-Path $path) {
        try {
            Remove-Item -Path $path -Recurse -Force -ErrorAction Stop
            Write-Host "Success: Deleted $path"
        } catch {
            Write-Host "Failed: Could not delete $path. It might be in use."
            Write-Host $_.Exception.Message
        }
    } else {
        Write-Host "Not Found: $path"
    }
}
