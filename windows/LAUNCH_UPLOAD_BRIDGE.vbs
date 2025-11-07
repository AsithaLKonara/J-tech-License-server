Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
batchPath = fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), "LAUNCH_UPLOAD_BRIDGE.bat")
If fso.FileExists(batchPath) Then
  WshShell.Run Chr(34) & batchPath & Chr(34), 0, False
End If
Set WshShell = Nothing
Set fso = Nothing


