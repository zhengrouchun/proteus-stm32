from pathlib import Path  # 用交付包内的相对路径保存图片。
from html import escape  # 转义 SVG 中的文字。
from PIL import Image, ImageDraw, ImageFont  # 使用精确绘图生成 PNG，而不是生成可能接错线的示意照片。

root = Path(__file__).resolve().parents[1]  # 定位交付目录。
output = root / "接线图"  # 图片和可缩放 SVG 放到同一个目录。
width, height = 2220, 1430  # 增加短路支路与 MCU 标签之间的接线空间。
bitmap = Image.new("RGB", (width, height), "white")  # 创建白色画布。
draw = ImageDraw.Draw(bitmap)  # 为 PNG 创建绘图对象。
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>']  # 同时生成等价的矢量图。
ink, green, control = "#1c2733", "#216449", "#235c96"  # 黑色表示元件，绿色表示主回路，蓝色表示控制线。

def line(points, color=green, thickness=4):  # 画一根导线，支持折线拐弯。
    draw.line(points, fill=color, width=thickness)  # 写入 PNG 导线。
    data = " ".join(f"{x},{y}" for x, y in points)  # 将坐标转换成 SVG 格式。
    svg.append(f'<polyline points="{data}" fill="none" stroke="{color}" stroke-width="{thickness}"/>')  # 写入 SVG 导线。

def text(x, y, content, size=25, color=ink):  # 写文字，坐标为左上角。
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", size)  # 使用系统中文字体。
    draw.text((x, y), content, font=font, fill=color)  # 写入 PNG 的文字。
    svg.append(f'<text x="{x}" y="{y + size}" font-family="Microsoft YaHei, sans-serif" font-size="{size}" fill="{color}">{escape(content)}</text>')  # 写入 SVG 的文字。

def box(x, y, w, h, color=ink, fill="white", thickness=3):  # 画元件或说明框。
    draw.rectangle((x, y, x+w, y+h), outline=color, fill=fill, width=thickness)  # 写入 PNG 方框。
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" stroke="{color}" fill="{fill}" stroke-width="{thickness}"/>')  # 写入 SVG 方框。

def circle(x, y, r, color=ink, fill="white"):  # 画电源、仪表或连接点。
    draw.ellipse((x-r, y-r, x+r, y+r), outline=color, fill=fill, width=3)  # 写入 PNG 圆形。
    svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" stroke="{color}" fill="{fill}" stroke-width="3"/>')  # 写入 SVG 圆形。

def ground(x, y, color=green):  # 画公共接地符号。
    line([(x,y),(x,y+12)], color)  # 地线接到接地符号顶端。
    for offset, half in [(12,20),(21,13),(30,6)]:  # 用三条递减长度的横线画接地。
        line([(x-half,y+offset),(x+half,y+offset)], color, 3)  # 画每一条接地横线。

def dot(x, y, color=green):  # 标明电气连接点。
    circle(x,y,5,color,color)  # 实心点表示两根线在这里相连。

def resistor(x, y, horizontal=True):  # 画 IEC 矩形电阻符号。
    if horizontal:  # 横向电阻用于 RS、R1。
        box(x,y-14,100,28)  # 电阻的主回路从左右端进入。
    else:  # 竖向电阻用于 R2 和下拉电阻。
        box(x-14,y,28,90)  # 电阻的主回路从上下端进入。

def manual_switch(x, y, vertical=False, closed=False):  # 明确画出触点和实际开闭位置。
    if vertical:  # 竖直放置的开关。
        circle(x,y,5)  # 上触点。
        circle(x,y+55,5)  # 下触点。
        line([(x,y),(x,y+55) if closed else (x+22,y+38)],ink,3)  # 闭合时接到另一触点，断开时保留可见间隙。
    else:  # 水平放置的开关。
        circle(x,y,5)  # 左触点。
        circle(x+65,y,5)  # 右触点。
        line([(x,y),(x+65,y) if closed else (x+48,y-22)],ink,3)  # 明确区分正常闭合与短路支路断开。

def controlled_switch(y, label, net):  # 展示两个主回路端和两个控制端，避免混淆。
    box(340,y-52,180,107)  # 用边框圈出四端器件，内部真实画出开关触点。
    line([(285,y),(370,y),(370,y-18),(395,y-18)])  # 主回路左端通向左触点。
    manual_switch(395,y-18)  # 两个触点和触片表示启动时断开的主回路。
    line([(460,y-18),(490,y-18),(490,y),(585,y)])  # 右触点通向主回路输出。
    text(342,y-90,label+"  VSWITCH",22)  # 把型号放在器件上方，避免覆盖触点。
    circle(430,y+25,13,control)  # 控制电压用圆形控制单元表示，与主回路绝缘。
    text(422,y+13,"V",17,control)  # 控制单元由 C+ 与 C− 的电压驱动。
    line([(390,y+55),(390,y+25),(417,y+25)],control)  # 控制正端只连接控制单元。
    line([(475,y+55),(475,y+25),(443,y+25)],control)  # 控制负端只连接控制单元。
    for dash_y in [y-7,y+1]:  # 虚线表示控制关系，不是导线。
        line([(430,dash_y),(430,dash_y+4)],ink,2)  # 主回路和控制端不能用导线直接连起来。
    text(345,y+32,"C+",18,control)  # 控制正端标在对应引出线左侧。
    text(480,y+32,"C−",18,control)  # 控制负端标在对应引出线右侧。
    line([(390,y+55),(390,y+105)],control)  # 控制正端接 GPIO 控制网络。
    text(222,y+78,net,23,control)  # 相同网络名在 MCU 一侧与此处相连。
    line([(390,y+105),(390,y+120)],control)  # 控制正端同时接下拉电阻。
    box(376,y+120,28,70)  # 缩短下拉符号，为下一只开关名称留出空间。
    text(418,y+140,"100 kΩ",22,control)  # 写下拉电阻数值。
    line([(390,y+190),(390,y+198)],control)  # 下拉电阻另一端去地。
    ground(390,y+198,control)  # 控制地与全电路公共地相连。
    line([(475,y+55),(475,y+62)],control)  # 控制负端直接接公共 GND。
    ground(475,y+62,control)  # 不能把控制负端接到电源输出端。

text(60,34,"解决 DIV 运行供电互锁与复测：对应新固件的接线图",39)  # 标明图的用途。
text(60,93,"绿色：被测电路主回路    蓝色：GPIO 控制    同名网络必须在 Proteus 中连线或放置同名网络标签",24)  # 解释图中网络标签的实际接线方法。

for y, name, volts in [(250,"VS_TEST","1 V"),(570,"VS_RUN","3 V")]:  # 分别画独立的测试和运行电源。
    line([(135,y),(285,y)])  # 电源正端接开关主回路输入。
    line([(135,y),(135,y+32)])  # 连接直流电源的正端。
    circle(135,y+80,48)  # 用直流电源圆形符号表示源。
    text(121,y+38,"+",28)  # 标明上端为正极。
    text(122,y+90,"−",28)  # 标明下端为负极。
    text(58,y-55,name,24)  # 写电源名称。
    text(192,y+35,volts,30)  # 将电压文字与下方控制网络名分开。
    line([(135,y+128),(135,y+145)])  # 电源负端连接公共地。
    ground(135,y+145)  # 两个源和 MCU 共地。
controlled_switch(250,"K_TEST","TEST_ENABLE")  # PB12 控制测试电源。
controlled_switch(570,"K_RUN","RUN_ENABLE")  # PB13 控制运行电源。
line([(585,250),(610,250),(610,570),(585,570)])  # 两路只在各自开关之后汇合。
dot(610,250)  # 电源汇合后的主回路连接点。
text(548,182,"EXC_IN",24)  # 标明 RS 左端的激励输入网络。
line([(610,250),(670,250)])  # 电源汇合节点进入 RS。
resistor(670,250)  # 串联电阻 RS。
text(672,200,"RS  2 kΩ",25)  # 与用户已有电路一致。
line([(770,250),(830,250),(875,250)])  # RS 右端是 VA，之后进入 R1 断路开关。
dot(830,250)  # VA 的取样连接点。
line([(830,250),(830,155)],control)  # VA 引出采样网络。
text(759,118,"DIV_VA",24,control)  # 同名网络接 MCU PA1。
manual_switch(875,250,closed=True)  # 正常位置的 SW1 闭合，断开才模拟横向电阻断路。
text(865,291,"SW1",24)  # 写故障开关编号。
line([(940,250),(965,250)])  # SW1 右端连接 R1 左端。
resistor(965,250)  # 主分压电阻 R1。
text(953,286,"R2 / CSV R1",20)  # 最新截图横向电阻叫 R2，对应判别表的 R1。
text(968,316,"10 kΩ",21)  # 标称值不因并联短路开关闭合而改成零。
line([(1065,250),(1160,250)])  # R1 右端连接 VB。
dot(1160,250)  # VB 的取样连接点。
line([(1160,250),(1160,170),(1290,170)],control)  # VB 引出采样网络。
text(1190,128,"DIV_VB",24,control)  # 同名网络接 MCU PA0。
line([(950,250),(950,168),(987,168)])  # SW5 左端接 SW1 右侧，不跨过 SW1。
manual_switch(987,168)  # SW5 只短接 R1。
line([(1052,168),(1100,168),(1100,250)])  # SW5 右端接 R1 右侧。
dot(950,250)  # 标明 R1 左侧连接点。
dot(1100,250)  # 标明 R1 右侧连接点。
text(984,128,"SW5",23)  # 写 R1 短路开关编号。
line([(1160,250),(1160,360)])  # VB 下接 R2。
resistor(1160,360,False)  # 下分压电阻 R2。
text(1195,361,"R3",25)  # 最新截图竖向电阻叫 R3。
text(1195,393,"CSV R2",21)  # 竖向电阻对应判别表的 R2。
text(1195,425,"10 kΩ",21)  # 本图恢复正常标称值，5 kΩ 属于改值而非短路。
line([(1160,450),(1160,475),(1160,535)])  # 下端节点经过 SW4 后才接地。
manual_switch(1160,535,True,closed=True)  # 正常位置 SW4 闭合，断开模拟竖向电阻断路。
text(1193,552,"SW4",24)  # 写串联断路开关编号。
line([(1160,590),(1160,660)])  # 只有 SW4 下端直接接公共 GND。
ground(1160,660)  # 分压网络公共地。
line([(1160,250),(1330,250),(1330,350)])  # SW2 上端接竖向电阻上端 VB。
manual_switch(1330,350,True)  # 正常时 SW2 断开；闭合才把竖向电阻两端连起来。
text(1360,348,"SW2",23)  # 写竖向电阻的并联短路开关编号。
line([(1330,405),(1330,475),(1160,475)])  # SW2 下端接电阻下端、SW4 上方，不能绕过 SW4 接地。
dot(1160,475)  # 明确 SW2 与竖向电阻下端相连的节点。
text(1227,498,"电阻下端",20)  # 此节点经 SW4 接地，不是固定 GND。
line([(610,570),(680,570),(680,627)])  # EXC_IN 电压表正端接电源汇合点。
circle(680,665,38)  # 用仪表圆表示直流电压表。
text(665,643,"V",32)  # 电压表标记。
line([(680,703),(680,724)])  # 电压表负端接地。
ground(680,724)  # 核验实际测试和运行电压。
text(732,620,"新增电压表",24)  # 电压表用于供电控制验证。
text(732,655,"检测期间约 1 V",23)  # 一伏阶段才允许采样判别。
text(732,691,"正常运行约 3 V",23)  # 三伏阶段保持运行并停止采样。

box(1735,185,420,630)  # 右移 MCU 给并联短路支路留出空间。
text(1760,201,"U1  STM32F103C8",29)  # 标明主控芯片。
pins = [(300,"PA0 / 10","DIV_VB"),(380,"PA1 / 11","DIV_VA"),(490,"PB12 / 25","TEST_ENABLE"),(575,"PB13 / 26","RUN_ENABLE"),(680,"PA4 / 14","RETEST"),(755,"PA5 / 15","STOP")]  # 引脚名称和物理脚号对应用户截图。
for y, pin, net in pins:  # 使用网络名让控制线与主回路清晰分开。
    line([(1680,y),(1735,y)],control)  # MCU 引脚引出到同名网络。
    text(1758,y-17,pin,25,control)  # 写 MCU 引脚名称及脚号。
    text(1548,y-45,net,21,control)  # 在 Proteus 中使用这些同名网络标签。
text(1745,843,"VDD / VDDA / VBAT：3.3 V",23)  # MCU 始终由原来的 BAT2 供电。
text(1745,878,"VSS / VSSA：公共 GND",23)  # 明确所有控制端与被测电路共地。
text(1745,917,"PA9 / 30 → 终端 RXD",23)  # 给串口报告提供显示窗口。
text(1745,952,"终端：115200，8N1",23)  # 与固件串口配置一致。

line([(60,860),(1480,860)],ink,2)  # 用结构性分隔线区分按钮和主回路。
text(60,885,"新增操作按钮与运行指示",29)  # 第二行画人机操作部分。
for x, name, pin in [(170,"SW_RETEST","PA4 / 14"),(535,"SW_STOP","PA5 / 15")]:  # 两个瞬时按钮分别接地。
    text(x-95,948,pin,25,control)  # 写 GPIO 引脚和脚号。
    line([(x,986),(x,1010)],control)  # 输入端连接按钮上触点。
    manual_switch(x,1010,True)  # 瞬时按键按下时闭合。
    line([(x,1065),(x,1112)],control)  # 按钮下触点去地。
    ground(x,1112,control)  # 按下把上拉输入拉低。
    text(x-95,1160,name,23)  # 标明操作按钮名称。
text(65,1210,"两只均用 SW-SPST-MOM；固件内部上拉，按下接地。",23)  # 不与四只保持型故障开关混用。
line([(1010,947),(1010,987)],control)  # RUN_ENABLE 引出到 LED 限流支路。
text(908,909,"RUN_ENABLE / PB13",24,control)  # 指示支路与运行开关控制正端接同一网络。
resistor(1010,987,False)  # 使用 1 kOhm 限流。
text(1050,1009,"1 kΩ",24)  # 写 LED 限流电阻值。
line([(1010,1077),(1010,1093)],control)  # 电阻下端连接 LED 阳极。
line([(994,1095),(1026,1095),(1010,1125),(994,1095)],ink,3)  # 用三角形表示 LED 的导通方向。
line([(993,1127),(1027,1127)],ink,3)  # 下方横线为 LED 阴极。
line([(1025,1100),(1044,1084)],ink,2)  # 向外的线表示发光。
line([(1035,1111),(1054,1095)],ink,2)  # 第二条发光线。
text(1070,1090,"绿色 LED",24)  # LED 只是控制信号指示。
text(1070,1125,"上端阳极，下端阴极",22)  # 避免反接不亮。
line([(1010,1127),(1010,1150)],control)  # LED 阴极接地。
ground(1010,1150,control)  # 与控制地相同。
text(897,1210,"LED 显示控制电平；实际供电另看 EXC_IN 电压表。",22)  # 区分控制输出和物理供电证据。
box(60,1270,2100,125,fill="#f3f5f7",thickness=1)  # 为共地和故障开关说明留足空间。
text(80,1286,"全部接地符号属于同一个 GND：三路电源负端、MCU 地、C−、下拉、LED、按钮和仪表负端。",24)  # 回答哪些端子必须共地。
text(80,1323,"开关目标：RON=0.1 Ω，ROFF=1 TΩ，VON=2.4 V，VOFF=0.9 V；先用 0 V / 3.3 V 验证模型。",23)  # 这些是模型配置目标，需要在实际 Proteus 属性中核验。
text(80,1360,"图示正常位置：SW1、SW4 闭合，SW2、SW5 断开；CSV 的 R2 短路：只闭合 SW2，SW4 仍闭合。",22)  # 正常状态与短路动作都对应真实触点画法。
svg.append("</svg>")  # 结束 SVG 文档。
bitmap.save(output / "解决DIV双电源互锁与复测接线.png")  # 保存便于聊天直接查看的 PNG。
(output / "解决DIV双电源互锁与复测接线.svg").write_text("\n".join(svg),encoding="utf-8")  # 保存可缩放、可进一步编辑的矢量原图。
print("接线 PNG 和 SVG 已生成。")  # 输出完成状态。
