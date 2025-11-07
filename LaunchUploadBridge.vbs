Set shell = CreateObject("Wscript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
cmd = "pythonw.exe " & Chr(34) & scriptDir & "\main.py" & Chr(34)
On Error Resume Next
shell.Run cmd, 0, False

