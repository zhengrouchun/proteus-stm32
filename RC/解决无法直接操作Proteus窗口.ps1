param([string]$Actions) # 接收按顺序执行的窗口操作，操作范围仅限本次RC原理图。
Add-Type -AssemblyName System.Windows.Forms # 使用按键发送、剪贴板和屏幕尺寸接口。
Add-Type -AssemblyName System.Drawing # 使用屏幕截图接口，保留真实软件画面。
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class RcWindow {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); // 使用真实屏幕像素，避免高分屏截图被裁切。
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr window); // 激活指定Proteus窗口。
    [DllImport("user32.dll")] public static extern IntPtr GetLastActivePopup(IntPtr window); // 优先激活当前器件或属性对话框，避免输入误发到原理图。
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr window, int mode); // 将窗口最大化以便准确接线。
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y); // 将鼠标定位到指定屏幕坐标。
    [DllImport("user32.dll")] public static extern void mouse_event(uint flag, uint x, uint y, uint data, UIntPtr extra); // 发送鼠标按下与松开事件。
}
'@ # 上面声明的接口只用于操作原生Proteus窗口，不修改工程二进制格式。
[RcWindow]::SetProcessDPIAware() | Out-Null # 将鼠标坐标与截图尺寸统一为真实屏幕像素。
$rcScale = [Windows.Forms.Screen]::PrimaryScreen.Bounds.Width / 1996 # 将预览图的横纵坐标换算到本机3200像素宽的屏幕。
foreach ($action in (ConvertFrom-Json $Actions)) { # 严格按照调用方给出的顺序执行操作。
    if ($null -ne $action.x) { $action.x = [int]($action.x * $rcScale); $action.y = [int]($action.y * $rcScale); Write-Output ($action.kind + ' pixel=' + $action.x + ',' + $action.y + ' scale=' + $rcScale) } # 鼠标动作使用预览截图坐标输入，并记录实际坐标供核对。
    switch ($action.kind) { # 根据动作名称选择窗口操作。
        'focus' { $rcHandle = (Get-Process -Id $action.id).MainWindowHandle; [RcWindow]::ShowWindow($rcHandle,3) | Out-Null; $rcPopup = [RcWindow]::GetLastActivePopup($rcHandle); [RcWindow]::SetForegroundWindow($rcPopup) | Out-Null } # 数值3是Windows定义的最大化窗口模式；优先激活正在编辑的对话框。
        'click' { [RcWindow]::SetCursorPos($action.x,$action.y) | Out-Null; [RcWindow]::mouse_event(2,0,0,0,[UIntPtr]::Zero); [RcWindow]::mouse_event(4,0,0,0,[UIntPtr]::Zero) } # 标志2和4分别表示左键按下及松开；其余零值是不使用的事件参数。
        'right' { [RcWindow]::SetCursorPos($action.x,$action.y) | Out-Null; [RcWindow]::mouse_event(8,0,0,0,[UIntPtr]::Zero); [RcWindow]::mouse_event(16,0,0,0,[UIntPtr]::Zero) } # 标志8和16分别表示右键按下及松开。
        'move' { [RcWindow]::SetCursorPos($action.x,$action.y) | Out-Null } # 移动鼠标，使Proteus显示正在放置的器件或连线。
        'keys' { [Windows.Forms.SendKeys]::SendWait($action.value) } # 发送菜单快捷键和编辑按键。
        'text' { [Windows.Forms.Clipboard]::SetText($action.value); [Windows.Forms.SendKeys]::SendWait('^v') } # 通过粘贴准确输入文件名、器件名与电路参数。
        'wait' { Start-Sleep -Milliseconds $action.ms } # 等待软件完成对话框或仿真初始化。
    } # 结束动作分支。
    Start-Sleep -Milliseconds 650 # 给高分屏原生窗口留出处理每个动作的时间，避免对话框尚未出现就输入。
} # 结束本批动作。
$rcBounds = [Windows.Forms.Screen]::PrimaryScreen.Bounds # 读取主屏幕尺寸。
$rcScreen = [Drawing.Bitmap]::new($rcBounds.Width,$rcBounds.Height) # 创建与主屏幕同尺寸的截图画布。
$rcGraphics = [Drawing.Graphics]::FromImage($rcScreen) # 获取画布的绘图接口。
$rcGraphics.CopyFromScreen($rcBounds.Location,[Drawing.Point]::Empty,$rcBounds.Size) # 读取真实桌面画面，供后续核对器件与导线。
$rcScreen.Save((Join-Path $PSScriptRoot '检查Proteus当前桌面.png')) # 将本次检查截图统一保存到RC目录。
$rcGraphics.Dispose() # 释放绘图接口。
$rcScreen.Dispose() # 释放截图画布资源。
