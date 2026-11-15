param([Parameter(Mandatory=$true)][string]$PdfPath,[Parameter(Mandatory=$true)][string]$OutputDirectory)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null=[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null=[Windows.Data.Pdf.PdfDocument,Windows.Data.Pdf,ContentType=WindowsRuntime]
$null=[Windows.Storage.Streams.InMemoryRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]
$null=[Windows.Storage.Streams.DataReader,Windows.Storage.Streams,ContentType=WindowsRuntime]
$taskMethod=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 } | Select-Object -First 1
$actionMethod=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and -not $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 } | Select-Object -First 1
function AwaitResult($operation,$type) { $task=$taskMethod.MakeGenericMethod($type).Invoke($null,@($operation)); $task.GetAwaiter().GetResult() }
$inputFile=(Resolve-Path -LiteralPath $PdfPath).Path
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$outputFolder=(Resolve-Path -LiteralPath $OutputDirectory).Path
$file=AwaitResult ([Windows.Storage.StorageFile]::GetFileFromPathAsync($inputFile)) ([Windows.Storage.StorageFile])
$pdf=AwaitResult ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
for($i=0;$i -lt $pdf.PageCount;$i++) {
    $page=$pdf.GetPage($i)
    $stream=New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    $options=New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $options.DestinationWidth=1000
    $task=$actionMethod.Invoke($null,@($page.RenderToStreamAsync($stream,$options)))
    $null=$task.GetAwaiter().GetResult()
    $reader=[Windows.Storage.Streams.DataReader]::new($stream.GetInputStreamAt(0))
    $null=AwaitResult ($reader.LoadAsync([uint32]$stream.Size)) ([uint32])
    $bytes=New-Object byte[] $stream.Size
    $reader.ReadBytes($bytes)
    [IO.File]::WriteAllBytes((Join-Path $outputFolder ('page_{0:000}.png' -f ($i+1))),$bytes)
    $reader.Dispose();$stream.Dispose();$page.Dispose()
}
Write-Output "Rendered $($pdf.PageCount) pages."
