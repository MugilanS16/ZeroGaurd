param (
    [string]$DocxPath,
    [string]$PdfPath
)

$resolvedDocx = (Resolve-Path $DocxPath).Path
if (-not $PdfPath) {
    $PdfPath = [System.IO.Path]::ChangeExtension($resolvedDocx, ".pdf")
} else {
    $PdfPath = [System.IO.Path]::GetFullPath($PdfPath)
}

Write-Host "Opening Word..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    Write-Host "Converting $resolvedDocx to $PdfPath..."
    $doc = $word.Documents.Open($resolvedDocx)
    # 17 = wdFormatPDF
    $doc.SaveAs([ref]$PdfPath, [ref]17)
    $doc.Close()
    Write-Host "Successfully generated PDF: $PdfPath"
} catch {
    Write-Error $_.Exception.Message
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
