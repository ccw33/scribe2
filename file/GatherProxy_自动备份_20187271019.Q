[General]
SyntaxVersion=2
BeginHotkey=121
BeginHotkeyMod=0
PauseHotkey=0
PauseHotkeyMod=0
StopHotkey=123
StopHotkeyMod=0
RunOnce=1
EnableWindow=
MacroID=b77b8527-0730-4401-8014-b2630069c608
Description=GatherProxy_自动备份
Enable=1
AutoRun=0
[Repeat]
Type=0
Number=1
[SetupUI]
Type=2
QUI=
[Relative]
SetupOCXFile=
[Comment]

[Script]
Function click_when_nearbycolor(x, y, color,shutdown)
	MoveTo x, y
	If not color="" Then
        FindCenterColor  x - 50, y - 50, x + 50, y + 50, color, intX, intY
        Dim j
    	j=1
		While not (intX > 0 And intY > 0)
			j = j + 1
			Delay 1000
			FindCenterColor  x - 50, y - 50, x + 50, y + 50, color, intX, intY
			If j > 10 Then 
				TracePrint "找不到"+color+"实际颜色是"+GetPixelColor(x,y) 
				click_when_nearbycolor = 0
				If shutdown = 1 Then 
					Call Plugin.Pic.PrintScreen(0, 0, 1400, 850, "F:\图片\error.jpg")
					MessageBox "找不到"+color+"实际颜色是"+GetPixelColor(x,y) +" 程序结束"
					EndScript
				End If
				Goto done
			End If
		Wend
		MoveTo intX, intY
	End If
	Call Plugin.Pic.PrintScreen(0, 0, 1400, 850, "F:\图片\debug.jpg")
    LeftClick 次数
    Delay 1000
    click_when_nearbycolor=1
    Rem done
End Function

Function click_when_nearbycolor_long_delay(x, y, color,times)
	MoveTo x, y
	If not color = ""  Then 
	 	FindCenterColor  x - 50, y - 50, x + 50, y + 50, color, intX, intY
        Dim j
    	j=1
		While not (intX > 0 And intY > 0)
			j = j + 1
			Delay 1000
			FindCenterColor x - 50, y - 50, x + 50, y + 50, color, intX, intY
			TracePrint "找不到"+color+"实际颜色是"+GetPixelColor(x,y) 
			If j > times Then 
				TracePrint "找不到" + color + "实际颜色是" + GetPixelColor(x, y)
				Call Plugin.Pic.PrintScreen(0, 0, 1400, 850, "F:\图片\error.jpg")
				MessageBox "找不到"+color+"实际颜色是"+GetPixelColor(x,y)+"程序结束"
				EndScript
			End If
		Wend
		MoveTo intX, intY
	End If
	Call Plugin.Pic.PrintScreen(0, 0, 1400, 850, "F:\图片\debug.jpg")
    LeftClick 次数
    Delay 1000
End Function
'==========以下是按键精灵录制的内容==========
//Delay 10000
//MoveTo 1138, 305
//Delay 3266
//LeftDown 1
//Delay 8
//LeftClick 1
//Delay 2
//LeftUp 1
'==========以上是按键精灵录制的内容==========
//MoveTo 679, 527
//GetColor=GetPixelColor(679,527)


//while not GetColor="F5D9A7"
//    MessageBox GetColor
//Delay 1000
//Wend
//LeftClick 次数

Set ws = createObject("WScript.shell")
ws.Run "D:\GatherProxy\GatherProxy.exe"
 
Call click_when_nearbycolor_long_delay(929,326,"178CFF",60) // 免费
Call click_when_nearbycolor(393, 297, "FEF2DA",1)	// Socks only
Call click_when_nearbycolor(277, 342, "FDE2B7",1)// Start checker after gathering complete
Call click_when_nearbycolor(466, 232, "FFFFFF",1)// Proxy Filter
Call click_when_nearbycolor(274, 339, "FDE6BD",1)// Remove Duplicate ID
Call click_when_nearbycolor(585, 228, "FFFFFF",1)// Proxy Checker
Call click_when_nearbycolor(290, 331, "FCFAF9",1)// 取消socks4
Call click_when_nearbycolor(810, 224, "FFFFFF",1)// Export proxy
Call click_when_nearbycolor(274, 290,"",1)// 取消HTTP/Elite
Call click_when_nearbycolor(375, 290,"",1)// 取消HTTP/Anonymous
Call click_when_nearbycolor(512, 290,"",1)// 取消HTTP/Transparent
Call click_when_nearbycolor(658, 290,"",1)// 取消socks4

Dim i
i = 1
While true
	Call click_when_nearbycolor(351, 238, "FFFFFF", 1)// Gather Proxy
	Rem start_again
	Call click_when_nearbycolor(1148, 308, "FAE2B5", 1)// start
	If i > 1 and ok=0 Then 
		Call click_when_nearbycolor(837, 527, "F9E0B2",1)// clear lastest result
	End If
	ok =  click_when_nearbycolor(766, 509, "F9E0B2",0)// No Server Found
	If ok=1 Then 
		Goto start_again
	End If
	Call click_when_nearbycolor_long_delay(811, 510, "F9E0B2",3600)// done
	Call click_when_nearbycolor(814, 224, "FFFFFF",1)// Export proxy
	Call click_when_nearbycolor(1109, 296, "F7DCAC",1)// Save by criteria
	SayString "proxies_" + CStr(i) + ".txt"
	Call click_when_nearbycolor(812, 598, "F9E0B2", 1)// 保存
	save_ok = click_when_nearbycolor(797, 455, "F6DBA9", 0)// 是否覆盖
	Call click_when_nearbycolor(757, 511, "F9E0B2",1)// 确定
	i = i + 1
Wend