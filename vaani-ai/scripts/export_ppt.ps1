$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open("C:\Users\Admin\Downloads\vaani-ai\NLP_Major_Project_VaaniAI_Presentation.pptx", [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
$pres.SaveAs("C:\Users\Admin\Downloads\vaani-ai\NLP_Major_Project_VaaniAI_Presentation.pdf", 32)
$pres.Close()
$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
Write-Output "PPT_PDF_EXPORT_SUCCESS"
