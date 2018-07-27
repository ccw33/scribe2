Set ws = createObject("WScript.shell")

s=wscript.scriptfullname
dir0=left(wscript.scriptfullname,instrrev(s,"\")-1) // 当前目录
dir1=left(wscript.scriptfullname,instrrev(dir0,"\")-1) //上一层目录

ws.Run dir1+"/GatherProxy_script.exe"