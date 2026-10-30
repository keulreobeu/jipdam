# Excel COM recalculation check (verification #3 of the role-2 workbook).
# Copies the workbook, opens the copy in Excel, CalculateFull, then compares every
# formula cell's recalculated value with the cached value stored in the original.
# Strings must match exactly; numbers within 1e-12. Nothing is saved.
param(
    [Parameter(Mandatory = $true)][string]$Workbook
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path $Workbook).Path
$copy = Join-Path $env:TEMP ("recalc_" + [IO.Path]::GetFileName($source))
Copy-Item $source $copy -Force

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$mismatches = 0
$checked = 0
try {
    $original = $excel.Workbooks.Open($source, 0, $true)   # read-only, no update
    $cached = @{}
    foreach ($sheet in $original.Worksheets) {
        $formulaCells = $null
        try { $formulaCells = $sheet.UsedRange.SpecialCells(-4123) } catch { continue } # xlCellTypeFormulas
        foreach ($cell in $formulaCells) {
            $cached["$($sheet.Name)!$($cell.Address($false, $false))"] = $cell.Value2
        }
    }
    $original.Close($false)

    $recalced = $excel.Workbooks.Open($copy)
    $excel.CalculateFullRebuild()
    foreach ($sheet in $recalced.Worksheets) {
        $formulaCells = $null
        try { $formulaCells = $sheet.UsedRange.SpecialCells(-4123) } catch { continue }
        foreach ($cell in $formulaCells) {
            $key = "$($sheet.Name)!$($cell.Address($false, $false))"
            if (-not $cached.ContainsKey($key)) { continue }
            $before = $cached[$key]
            $after = $cell.Value2
            $checked++
            $ok = $false
            if ($before -is [double] -and $after -is [double]) {
                $ok = [math]::Abs($before - $after) -le 1e-12
            } else {
                $ok = ("$before" -eq "$after")
            }
            if (-not $ok) {
                $mismatches++
                if ($mismatches -le 5) { Write-Output "MISMATCH $key cached=$before recalc=$after" }
            }
        }
    }
    $recalced.Close($false)
} finally {
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    Remove-Item $copy -Force -ErrorAction SilentlyContinue
}
Write-Output ("checked=" + $checked + " mismatches=" + $mismatches)
if ($mismatches -ne 0) { exit 2 }
