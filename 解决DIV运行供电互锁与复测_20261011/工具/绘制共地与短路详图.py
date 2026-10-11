from pathlib import Path  # 将修正版图片写到同一交付包。
from html import escape  # 保证 SVG 中的中文和符号正确保存。
from PIL import Image, ImageDraw, ImageFont  # 精确绘制电气端点和触点。

output = Path(__file__).resolve().parents[1] / "接线图"  # 定位接线图目录。
width, height = 2200, 1460  # 上半图画共地，下半图比较正常与短路。
bitmap = Image.new("RGB", (width,height), "white")  # 使用白底保持导线清晰。
draw = ImageDraw.Draw(bitmap)  # 创建 PNG 绘图对象。
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">','<rect width="100%" height="100%" fill="white"/>']  # 同时生成可缩放矢量图。
wire, ink = "#216449", "#1c2733"  # 绿色为导线，深色为元件与文字。

def line(points, color=wire, size=4):  # 画直线或折线。
    draw.line(points,fill=color,width=size)  # PNG 中按端点精确连接。
    coordinates = " ".join(f"{x},{y}" for x,y in points)  # 将同样的端点转换成 SVG 数据。
    svg.append(f'<polyline points="{coordinates}" stroke="{color}" stroke-width="{size}" fill="none"/>')  # SVG 与 PNG 保持相同连通关系。

def text(x,y,content,size=25):  # 每行文字按固定位置写入。
    draw.text((x,y),content,font=ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",size),fill=ink)  # 使用清晰中文字体。
    svg.append(f'<text x="{x}" y="{y+size}" font-family="Microsoft YaHei,sans-serif" font-size="{size}" fill="{ink}">{escape(content)}</text>')  # 写入对应矢量文字。

def dot(x,y):  # 实心点明确表示连接，交叉线不会被误当接点。
    draw.ellipse((x-5,y-5,x+5,y+5),fill=wire)  # PNG 连接点。
    svg.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{wire}"/>')  # SVG 连接点。

def contact(x,y,vertical=False,closed=False):  # 按真实开闭状态画两触点。
    end = (x,y+55) if vertical else (x+65,y)  # 确定第二触点。
    for px,py in [(x,y),end]:  # 画两个空心触点。
        draw.ellipse((px-5,py-5,px+5,py+5),outline=ink,fill="white",width=3)  # PNG 触点。
        svg.append(f'<circle cx="{px}" cy="{py}" r="5" fill="white" stroke="{ink}" stroke-width="3"/>')  # SVG 触点。
    tip = end if closed else ((x+25,y+35) if vertical else (x+45,y-22))  # 闭合时触片真正接到另一触点。
    line([(x,y),tip],ink,3)  # 用导通或可见间隙表示开关状态。

def resistor(x,y,vertical=False):  # 画矩形电阻，端点在矩形边缘。
    coordinates = (x-13,y,x+13,y+95) if vertical else (x,y-13,x+90,y+13)  # 确定横向或竖向电阻边界。
    draw.rectangle(coordinates,fill="white",outline=ink,width=3)  # PNG 电阻。
    x1,y1,x2,y2 = coordinates  # 取矩形坐标用于 SVG。
    svg.append(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" fill="white" stroke="{ink}" stroke-width="3"/>')  # SVG 电阻。

def ground(x,y):  # 画公共零伏网络的接地符号。
    line([(x,y),(x,y+12)])  # 地线到符号顶端。
    for offset,half in [(12,20),(22,13),(32,6)]:  # 三条横线逐渐缩短。
        line([(x-half,y+offset),(x+half,y+offset)])  # 接地符号。

text(60,35,"解决共地端子与 R2 短路位置混淆：按你最新截图编号标注",36)  # 说明修正对象与编号来源。
text(60,100,"你的横向 R2 = CSV 的 R1；你的竖向 R3 = CSV 的 R2。先按位置识别，再操作开关。",27)  # 明确截图与判别表的映射。
text(60,172,"这些端子全部接到同一条公共 GND 母线（0 V）",30)  # 共地定义不是只将两个电压表连在一起。
groups = [  # 将所有必须共地的端子按接线用途列出。
    ["1 V 测试电源","负极 VS_TEST−"],
    ["3 V 运行电源","负极 VS_RUN−"],
    ["3.3 V MCU 电源","负极 BAT2−"],
    ["U1 的 VSS","23 / 35 / 47 脚","VSSA 第 8 脚"],
    ["两只 VSWITCH","控制负端 C−","两只下拉的下端"],
    ["三只电压表","EXC_IN、VA、VB","各自的负端"],
    ["操作按钮接地端","LED 阴极","复位按钮接地端"],
    ["SW4 的下端","BOOT0 下拉下端","均为公共 GND"],
]
for index,labels in enumerate(groups):  # 各组直接连到同一条地线。
    center = 140 + index*270  # 均匀安排地线支路，避免文字互相覆盖。
    for row,label in enumerate(labels):  # 每个端子组按三行以内显示。
        text(center-102,240+row*37,label,23)  # 写清楚是负端、下端或地引脚。
    line([(center,371),(center,465)])  # 该组接到公共母线。
    dot(center,465)  # 母线与支路的电气接点。
line([(60,465),(2140,465)],wire,6)  # 全部端子共享同一条连续地线。
ground(1100,465)  # 公共 GND 母线的接地标志。
text(905,515,"同一 GND 网络，电位为 0 V",26)  # 全图的接地符号都属于此网络。
text(60,565,"R3 下端（SW4 上方）是内部节点：经 SW4 才接地；SW2 下端必须接这个内部节点。",25)  # 点出最容易把短路开关接错的位置。
line([(60,625),(2140,625)],ink,2)  # 分隔共地说明和故障开关详图。

def divider(origin,shorted):  # 画同一电路的正常与竖向电阻短路状态。
    x = origin  # 当前小图的横向偏移。
    title = "CSV DIV4：竖向电阻短路" if shorted else "正常：两只电阻都参与分压"  # 标明测试工况。
    text(x+20,657,title,29)  # 小图标题。
    text(x+20,710,"1 V 检测条件；R2、R3 均先恢复 10 kΩ",22)  # 先恢复标称值，再改变故障开关。
    line([(x+40,800),(x+105,800)])  # 测试输入接 RS。
    resistor(x+105,800)  # RS 限流电阻。
    text(x+92,755,"RS 2 kΩ",22)  # 写限流电阻值。
    line([(x+195,800),(x+250,800),(x+300,800)])  # RS 后是 VA，随后接断路开关。
    dot(x+250,800)  # VA 连接点。
    text(x+230,755,"VA",24)  # ADC 的 PA1 采样节点。
    contact(x+300,800,closed=True)  # SW1 保持闭合。
    text(x+295,830,"SW1 闭合",21)  # 两图都不引入横向电阻断路。
    line([(x+365,800),(x+400,800),(x+420,800)])  # 横向电阻左端位于 SW1 右侧。
    resistor(x+420,800)  # 最新截图中的横向 R2。
    text(x+415,833,"R2 / CSV R1",20)  # 标出物理编号和表格编号。
    text(x+435,863,"10 kΩ",20)  # 正常标称值。
    line([(x+510,800),(x+595,800)])  # 横向电阻右端是 VB。
    dot(x+595,800)  # VB 连接点。
    text(x+575,755,"VB",24)  # ADC 的 PA0 采样节点。
    line([(x+400,800),(x+400,752),(x+435,752)])  # SW5 左端只跨横向电阻。
    contact(x+435,752)  # 本工况 SW5 保持断开。
    text(x+408,760,"SW5 断开",18)  # 在横向旁路触点旁标出编号和状态。
    line([(x+500,752),(x+545,752),(x+545,800)])  # SW5 右端回到横向电阻右侧。
    dot(x+400,800)  # 横向电阻左侧的旁路接点。
    dot(x+545,800)  # 横向电阻右侧的旁路接点。
    line([(x+595,800),(x+595,900)])  # VB 接竖向电阻上端。
    resistor(x+595,900,True)  # 最新截图中的竖向 R3。
    text(x+628,903,"R3 / CSV R2",20)  # 明确用户要做的 CSV R2 故障对应这只电阻。
    text(x+628,938,"10 kΩ",20)  # 短路时保留元件标称值，改闭合旁路。
    line([(x+595,995),(x+595,1040),(x+595,1095)])  # 电阻下端先形成内部节点，再接 SW4。
    dot(x+595,1040)  # 真正的竖向电阻下端接点。
    contact(x+595,1095,True,True)  # 两图的 SW4 都保持闭合。
    text(x+628,1100,"SW4 闭合",21)  # 短路试验不同时引入断路。
    line([(x+595,1150),(x+595,1180)])  # SW4 下端才接公共 GND。
    ground(x+595,1180)  # 被测电路回到公共地。
    line([(x+595,800),(x+795,800),(x+795,905)])  # SW2 上端与竖向电阻上端共接 VB。
    contact(x+795,905,True,shorted)  # 右图闭合 SW2，左图保留可见断开间隙。
    text(x+825,910,"SW2 闭合" if shorted else "SW2 断开",21)  # 在触点旁直接说明状态。
    line([(x+795,960),(x+795,1040),(x+595,1040)])  # SW2 下端接竖向电阻下端，不能直接接 GND。
    text(x+665,1064,"R3_BOTTOM",19)  # 给内部节点起明确网络名。
    text(x+25,1223,"SW5 断开；只改变 SW2，SW1 / SW4 均闭合。",22)  # 防止同时引入多个故障。

divider(60,False)  # 左图给出正常开关状态。
divider(1150,True)  # 右图给出竖向电阻真实短路路径。
text(60,1294,"短路路线：VB → SW2 → R3_BOTTOM → SW4 → GND；SW2 闭合后旁路 R3，R3 两端电压约为 0。",25)  # 用节点解释短路为什么成立。
text(60,1342,"在 1 V 检测阶段，CSV DIV4 预期 VB≈0 mV、VA≈833 mV；实际填写以 ADC 串口报告为准。",25)  # 只给预期值，不伪造实测。
text(60,1390,"MCU 的 VDDA / VDD / VBAT 接 3.3 V 正电源；它们不接 GND。你的复位上拉电阻现在编号 R4。",23)  # 区分地引脚与正电源引脚。
svg.append("</svg>")  # 结束矢量图。
bitmap.save(output / "解决共地端子与R2短路位置混淆.png")  # 保存用户可直接查看的详图。
(output / "解决共地端子与R2短路位置混淆.svg").write_text("\n".join(svg),encoding="utf-8")  # 保存可缩放原图。
print("共地母线与竖向电阻短路对照图已生成。")  # 显示生成结果。
