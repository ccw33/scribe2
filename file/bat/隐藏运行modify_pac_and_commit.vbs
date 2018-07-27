Set ws = createObject("WScript.shell")

s=wscript.scriptfullname
'当前目录
dir0=left(wscript.scriptfullname,instrrev(s,"\")-1)
'上一层目录
dir1=left(wscript.scriptfullname,instrrev(dir0,"\")-1)

ws.run dir0+"\modify_pac_and_commit.bat",0