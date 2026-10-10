"""生成给 Proteus 9.0 手工搭建电路用的元件图和连接示意图。"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent
FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
BG = "#F6F8FB"
INK = "#182B43"
MUTED = "#587089"
BLUE = "#1F68B4"
GREEN = "#008D73"
ORANGE = "#B66A18"
RED = "#BE3E4B"
WIRE = "#223E5B"
STROKE = "#D7E0EA"


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def text(draw, pos, value, size=25, color=INK, bold=False, anchor=None):
    draw.text(pos, value, font=font(size, bold), fill=color, anchor=anchor)


def line(draw, points, color=WIRE, width=5):
    draw.line(points, fill=color, width=width, joint="curve")


def node(draw, x, y, color=WIRE):
    draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color)


def panel(draw, box, title, subtitle=""):
    draw.rounded_rectangle(box, radius=20, fill="white", outline=STROKE, width=3)
    text(draw, (box[0] + 30, box[1] + 20), title, 34, INK, True)
    if subtitle:
        text(draw, (box[0] + 30, box[1] + 69), subtitle, 22, MUTED)


def resistor(draw, cx, cy, name, value, vertical=False, caption_above=True):
    if vertical:
        line(draw, [(cx, cy - 58), (cx, cy - 42)])
        draw.rectangle((cx - 15, cy - 42, cx + 15, cy + 42), fill="white", outline=WIRE, width=5)
        line(draw, [(cx, cy + 42), (cx, cy + 58)])
        text(draw, (cx + 28, cy - 31), name, 25, BLUE, True)
        text(draw, (cx + 28, cy + 4), value, 23, INK)
    else:
        line(draw, [(cx - 65, cy), (cx - 48, cy)])
        draw.rectangle((cx - 48, cy - 17, cx + 48, cy + 17), fill="white", outline=WIRE, width=5)
        line(draw, [(cx + 48, cy), (cx + 65, cy)])
        direction = -73 if caption_above else 35
        text(draw, (cx, cy + direction), name + "  " + value, 23, BLUE, True, "mm")


def switch(draw, cx, cy, name, control=None, vertical=False, manual=False):
    if vertical:
        line(draw, [(cx, cy - 59), (cx, cy - 26)])
        line(draw, [(cx, cy + 26), (cx, cy + 59)])
        draw.ellipse((cx - 6, cy - 32, cx + 6, cy - 20), fill=WIRE)
        draw.ellipse((cx - 6, cy + 20, cx + 6, cy + 32), fill=WIRE)
        line(draw, [(cx - 4, cy - 27), (cx + 19, cy + 17)], width=4)
        text(draw, (cx + 26, cy - 30), name, 22, ORANGE, True)
        if control:
            text(draw, (cx + 26, cy + 5), control, 19, MUTED)
    else:
        line(draw, [(cx - 68, cy), (cx - 28, cy)])
        line(draw, [(cx + 28, cy), (cx + 68, cy)])
        draw.ellipse((cx - 34, cy - 6, cx - 22, cy + 6), fill=WIRE)
        draw.ellipse((cx + 22, cy - 6, cx + 34, cy + 6), fill=WIRE)
        line(draw, [(cx - 28, cy), (cx + 17, cy - 20)], width=4)
        text(draw, (cx, cy - 54), name, 22, ORANGE, True, "mm")
        if control:
            text(draw, (cx, cy + 30), control, 19, MUTED, False, "mm")


def capacitor(draw, cx, cy, name, value):
    line(draw, [(cx, cy - 65), (cx, cy - 17)])
    line(draw, [(cx - 28, cy - 17), (cx + 28, cy - 17)], width=6)
    line(draw, [(cx - 28, cy + 17), (cx + 28, cy + 17)], width=6)
    line(draw, [(cx, cy + 17), (cx, cy + 65)])
    text(draw, (cx + 45, cy - 40), name, 24, BLUE, True)
    text(draw, (cx + 45, cy - 4), value, 23)
    text(draw, (cx - 42, cy - 37), "+", 25, RED, True)


def ground(draw, x, y):
    line(draw, [(x, y - 30), (x, y)], width=4)
    line(draw, [(x - 25, y), (x + 25, y)], width=4)
    line(draw, [(x - 17, y + 10), (x + 17, y + 10)], width=4)
    line(draw, [(x - 8, y + 20), (x + 8, y + 20)], width=4)


def source(draw, cx, cy, name, value):
    draw.ellipse((cx - 46, cy - 46, cx + 46, cy + 46), fill="white", outline=WIRE, width=5)
    text(draw, (cx, cy - 9), "+", 27, BLUE, True, "mm")
    text(draw, (cx, cy + 18), "−", 26, BLUE, True, "mm")
    text(draw, (cx - 62, cy - 90), f"{name}  {value}", 23, BLUE, True)


def tag(draw, x, y, label, color=BLUE):
    width = max(78, int(len(label) * 15 + 25))
    draw.rounded_rectangle((x, y - 20, x + width, y + 20), radius=7, fill="#EAF3FB", outline="#9BC4E9", width=2)
    text(draw, (x + 12, y), label, 20, color, True, "lm")
    return width


def title(draw, name, subtitle, width):
    text(draw, (50, 33), name, 50, INK, True)
    text(draw, (52, 103), subtitle, 25, MUTED)
    line(draw, [(50, 153), (width - 50, 153)], STROKE, 3)


def icon(draw, box, kind):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    if kind == "chip":
        draw.rectangle((cx - 45, cy - 37, cx + 45, cy + 37), fill="#EAF3FB", outline=WIRE, width=4)
        for step in [-25, -8, 9, 26]:
            line(draw, [(cx - 60, cy + step), (cx - 45, cy + step)], width=3)
            line(draw, [(cx + 45, cy + step), (cx + 60, cy + step)], width=3)
        text(draw, (cx, cy), "M3", 24, BLUE, True, "mm")
    elif kind == "res":
        resistor(draw, cx, cy, "", "", False)
    elif kind == "cap":
        line(draw, [(cx, cy - 54), (cx, cy - 17)])
        line(draw, [(cx - 28, cy - 17), (cx + 28, cy - 17)], width=5)
        line(draw, [(cx - 28, cy + 17), (cx + 28, cy + 17)], width=5)
        line(draw, [(cx, cy + 17), (cx, cy + 54)])
    elif kind == "cap_elec":
        capacitor(draw, cx, cy, "", "")
    elif kind == "cell":
        line(draw, [(cx, cy - 55), (cx, cy - 16)])
        line(draw, [(cx - 30, cy - 16), (cx + 30, cy - 16)], width=6)
        line(draw, [(cx - 17, cy + 16), (cx + 17, cy + 16)], width=6)
        line(draw, [(cx, cy + 16), (cx, cy + 55)])
    elif kind == "vswitch":
        switch(draw, cx, cy - 13, "")
        line(draw, [(cx - 17, cy + 27), (cx - 17, cy + 45)], BLUE, 3)
        line(draw, [(cx + 17, cy + 27), (cx + 17, cy + 45)], BLUE, 3)
        text(draw, (cx - 17, cy + 52), "+", 18, BLUE, True, "mm")
        text(draw, (cx + 17, cy + 52), "−", 18, BLUE, True, "mm")
    elif kind in ("switch", "button"):
        switch(draw, cx, cy, "")
    elif kind == "led":
        draw.polygon([(cx - 25, cy - 25), (cx - 25, cy + 25), (cx + 20, cy)], outline=WIRE, fill="white")
        line(draw, [(cx + 20, cy - 30), (cx + 20, cy + 30)], width=4)
        line(draw, [(cx - 55, cy), (cx - 25, cy)], width=4)
        line(draw, [(cx + 20, cy), (cx + 55, cy)], width=4)
        for y in [-32, -14]:
            line(draw, [(cx + 10, cy + y), (cx + 40, cy + y - 25)], GREEN, 3)
    elif kind == "display":
        draw.rounded_rectangle((cx - 66, cy - 44, cx + 66, cy + 44), 7, fill="#DCEBE8", outline=WIRE, width=4)
        draw.rectangle((cx - 52, cy - 28, cx + 52, cy + 28), fill="#103A4E")
        text(draw, (cx, cy), "OLED", 20, "white", True, "mm")
    elif kind == "memory":
        draw.rectangle((cx - 55, cy - 34, cx + 55, cy + 34), fill="#EAF3FB", outline=WIRE, width=4)
        text(draw, (cx, cy), "I²C", 22, BLUE, True, "mm")
    elif kind == "terminal":
        draw.rectangle((cx - 62, cy - 42, cx + 62, cy + 42), fill="#223E5B", outline=WIRE, width=3)
        text(draw, (cx - 48, cy - 15), "> 454mV", 18, "#BDECD4")
    elif kind == "meter":
        draw.ellipse((cx - 42, cy - 42, cx + 42, cy + 42), fill="white", outline=WIRE, width=4)
        text(draw, (cx, cy), "V", 28, BLUE, True, "mm")
    else:
        draw.rounded_rectangle((cx - 63, cy - 42, cx + 63, cy + 42), 8, fill="#EAF3FB", outline=WIRE, width=4)
        text(draw, (cx, cy), kind, 21, BLUE, True, "mm")


def draw_catalog():
    image = Image.new("RGB", (2400, 2220), BG)
    draw = ImageDraw.Draw(image)
    title(draw, "Proteus 9.0 元件搜索图册", "蓝色粗体为在本机 LIB 文件中核对过的搜索词；图标为清晰示意，不是 Proteus 截屏。", 2400)
    parts = [
        ("STM32F103C8", "主控 U1 · 现有图上已经放置", "1 个；片内 HSI 8 MHz", "chip"),
        ("RES", "通用电阻 · 改 Value 得到各阻值", "2k、10k、100Ω、1k、4.7k", "res"),
        ("CAP", "无极性电容 · 供电去耦", "100nF；靠近 MCU 电源", "cap"),
        ("CAP-ELEC", "有极性电容 · RC 被测电容", "10µF；正端接 RC_VB", "cap_elec"),
        ("CELL", "直流电源 · 修改 Value", "1V 测试 / 3V 运行 / 3.3V MCU", "cell"),
        ("VSWITCH", "电压控制模拟开关", "5 个；PB0/PB1/PB10/PB11/PB12", "vswitch"),
        ("SW-SPST", "手动故障注入开关", "DIV 4 个 + RC 4 个", "switch"),
        ("SW-SPST-MOM", "瞬时按键 · 复位及操作", "5 个：复位、模板、检测、记录、停止", "button"),
        ("LED-GREEN", "正常运行灯", "1 个；串联 1k 电阻", "led"),
        ("LED-RED", "故障/超范围灯", "1 个；串联 1k 电阻", "led"),
        ("OLED12864I2C", "I²C 图形显示屏", "1 个；PB6=SCL，PB7=SDA", "display"),
        ("24LC256", "I²C 非易失存储", "1 个；记录最近 8 条", "memory"),
        ("VIRTUAL TERMINAL", "仿真串口观察窗", "1 个；PA9 TX → RX", "terminal"),
        ("DC VOLTMETER", "电压表 · 先核对节点", "2 个；并联 VA / VB", "meter"),
        ("OSCILLOSCOPE", "示波器 · 观察 RC 波形", "1 个；验证 50/55 ms", "OSC"),
        ("LOGIC ANALYSER", "逻辑分析仪 · 查互锁与标记", "1 个；看供电和时刻", "LA"),
    ]
    for index, (name, purpose, value, kind) in enumerate(parts):
        col, row = index % 2, index // 2
        left, top = 50 + col * 1180, 190 + row * 250
        draw.rounded_rectangle((left, top, left + 1120, top + 225), radius=18, fill="white", outline=STROKE, width=3)
        draw.rounded_rectangle((left + 18, top + 22, left + 210, top + 195), radius=12, fill="#F0F5FA")
        icon(draw, (left + 35, top + 43, left + 193, top + 175), kind)
        text(draw, (left + 235, top + 33), name, 33, BLUE, True)
        text(draw, (left + 235, top + 93), purpose, 24, INK)
        text(draw, (left + 235, top + 145), value, 23, MUTED)
    image.save(OUT / "解决Proteus9元件型号与搜索词不明确的问题.png")


def draw_first_div():
    image = Image.new("RGB", (2600, 1500), BG)
    draw = ImageDraw.Draw(image)
    title(draw, "第一步：DIV 三工况最小验证原理图", "按当前 U1 裸片继续搭建；先取得 ADC 实测值，再加运行电源和 RC。", 2600)
    panel(draw, (50, 190, 1700, 1010), "被测分压电路", "正常 / R1断路 / R2短路，只改变开关状态")
    source(draw, 180, 590, "B1 CELL", "1 V")
    line(draw, [(180, 544), (180, 455), (385, 455)])
    resistor(draw, 465, 455, "RD_S", "2 kΩ")
    line(draw, [(530, 455), (680, 455)])
    node(draw, 680, 455)
    text(draw, (680, 393), "DIV_VA ≈ 909 mV", 27, GREEN, True, "mm")
    switch(draw, 825, 455, "S1 R1断路")
    line(draw, [(680, 455), (757, 455)])
    line(draw, [(893, 455), (960, 455)])
    resistor(draw, 1080, 455, "RD_1", "10 kΩ")
    line(draw, [(960, 455), (1015, 455)])
    line(draw, [(1145, 455), (1330, 455)])
    node(draw, 1330, 455)
    text(draw, (1330, 393), "DIV_VB ≈ 455 mV", 27, GREEN, True, "mm")
    line(draw, [(1330, 455), (1330, 577)])
    resistor(draw, 1330, 665, "RD_2", "10 kΩ", True)
    line(draw, [(1330, 723), (1330, 825)])
    ground(draw, 1330, 835)
    line(draw, [(1330, 455), (1530, 455), (1530, 590)])
    switch(draw, 1530, 660, "S2 R2短路", vertical=True, manual=True)
    line(draw, [(1530, 719), (1530, 825), (1330, 825)])
    line(draw, [(180, 636), (180, 825), (1330, 825)])
    text(draw, (190, 875), "操作：S1默认闭合；S2默认断开。测试R1断路时只断S1；测试R2短路时恢复S1再合S2。", 25, INK)
    panel(draw, (1740, 190, 2550, 1010), "U1 STM32F103C8", "与你截图中已放置的芯片一致")
    draw.rectangle((1870, 310, 2380, 810), fill="#EAF3FB", outline=WIRE, width=5)
    text(draw, (2125, 386), "STM32F103C8", 33, BLUE, True, "mm")
    text(draw, (2125, 435), "Cortex-M3 · HSI 8 MHz", 24, INK, False, "mm")
    for y, label, number, tag_name in [(540, "PA0 / ADC IN0", "10", "DIV_VB"), (610, "PA1 / ADC IN1", "11", "DIV_VA")]:
        line(draw, [(1775, y), (1870, y)])
        tag(draw, 1750, y - 49, tag_name)
        text(draw, (1900, y - 16), f"{number}  {label}", 25)
    text(draw, (1840, 725), "VDD / VDDA / VBAT → 3.3 V", 24, INK)
    text(draw, (1840, 765), "VSS / VSSA → GND", 24, INK)
    panel(draw, (50, 1050, 2550, 1450), "必须同时补齐的最小系统", "截图中的 U1 只有裸片；以下接线决定能否可靠启动和采到电压。")
    points = [
        (100, 1185, "VDD 24/36/48", "3.3 V；隐藏电源脚/同名电源网"),
        (690, 1185, "VDDA 9 / VSSA 8", "3.3 V / GND；模拟供电"),
        (1340, 1185, "VBAT 1 / BOOT0 44", "VBAT→3.3 V；BOOT0→10k→GND"),
        (1940, 1185, "NRST 7", "10k上拉；复位键下拉"),
    ]
    for x, y, head, body in points:
        text(draw, (x, y), head, 26, BLUE, True)
        text(draw, (x, y + 65), body, 24, INK)
    text(draw, (100, 1350), "所有电源负极与 MCU 地共地；HSI 8 MHz 时 OSCIN 5 / OSCOUT 6 暂时不接晶振。", 25, RED, True)
    image.save(OUT / "解决DIV三工况最小电路如何接线的问题.png")


def draw_networks():
    image = Image.new("RGB", (2800, 2140), BG)
    draw = ImageDraw.Draw(image)
    title(draw, "完整原理图（二）：DIV 与 RC 测试网络", "同名蓝色网络标签在主控页连接；K1—K5 为 VSWITCH，S1—S8 为 SW-SPST。", 2800)
    panel(draw, (45, 180, 2755, 1080), "DIV · 直流分压", "先完成此框三工况，再补齐九工况。故障开关一次只改变一个状态。")
    source(draw, 180, 435, "B1 CELL", "1 V")
    source(draw, 180, 650, "B2 CELL", "3 V")
    line(draw, [(180, 389), (180, 330), (365, 330)])
    switch(draw, 475, 330, "K1 VSWITCH", "PB0=DIV_TEST")
    line(draw, [(543, 330), (740, 330), (740, 550)])
    line(draw, [(180, 604), (180, 540), (365, 540)])
    switch(draw, 475, 540, "K2 VSWITCH", "PB10=DIV_RUN")
    line(draw, [(543, 540), (740, 540)])
    node(draw, 740, 540)
    line(draw, [(180, 481), (75, 481), (75, 545)])
    ground(draw, 75, 555)
    line(draw, [(180, 696), (180, 810)])
    ground(draw, 180, 820)
    line(draw, [(740, 550), (740, 670), (1000, 670)])
    resistor(draw, 1110, 670, "RD_S", "2 kΩ")
    line(draw, [(1000, 670), (1045, 670)])
    line(draw, [(1175, 670), (1330, 670)])
    node(draw, 1330, 670)
    tag(draw, 1278, 600, "PA1 DIV_VA")
    line(draw, [(1330, 670), (1392, 670)])
    switch(draw, 1460, 670, "S1 R1开路")
    line(draw, [(1528, 670), (1615, 670)])
    node(draw, 1615, 670)
    resistor(draw, 1750, 670, "RD_1", "10 kΩ")
    line(draw, [(1615, 670), (1685, 670)])
    line(draw, [(1815, 670), (1980, 670)])
    node(draw, 1980, 670)
    tag(draw, 1930, 600, "PA0 DIV_VB")
    line(draw, [(1615, 670), (1615, 495), (1682, 495)])
    switch(draw, 1750, 495, "S2 R1短路")
    line(draw, [(1818, 495), (1980, 495), (1980, 670)])
    line(draw, [(1980, 670), (1980, 713)])
    switch(draw, 1980, 775, "S3 R2开路", vertical=True)
    line(draw, [(1980, 834), (1980, 887)])
    resistor(draw, 1980, 945, "RD_2", "10 kΩ", vertical=True)
    line(draw, [(1980, 1003), (1980, 1024)])
    ground(draw, 1980, 1035)
    line(draw, [(1980, 670), (2300, 670), (2300, 715)])
    switch(draw, 2300, 790, "S4 R2短路", vertical=True)
    line(draw, [(2300, 849), (2300, 1030), (1980, 1030)])
    panel(draw, (45, 1120, 2755, 2090), "RC · 定时阶跃", "放电→断开放电→1 V 阶跃→50 ms 读 VB→55 ms 按需读 VA。")
    source(draw, 180, 1335, "B3 CELL", "1 V")
    source(draw, 180, 1540, "B4 CELL", "3 V")
    line(draw, [(180, 1289), (180, 1240), (365, 1240)])
    switch(draw, 475, 1240, "K3 VSWITCH", "PB1=RC_TEST")
    line(draw, [(543, 1240), (740, 1240), (740, 1460)])
    line(draw, [(180, 1494), (180, 1445), (365, 1445)])
    switch(draw, 475, 1445, "K4 VSWITCH", "PB11=RC_RUN")
    line(draw, [(543, 1445), (740, 1445)])
    node(draw, 740, 1445)
    line(draw, [(180, 1381), (75, 1381), (75, 1430)])
    ground(draw, 75, 1440)
    line(draw, [(180, 1586), (180, 1740)])
    ground(draw, 180, 1750)
    line(draw, [(740, 1460), (740, 1620), (1000, 1620)])
    resistor(draw, 1110, 1620, "RR_S", "2 kΩ")
    line(draw, [(1000, 1620), (1045, 1620)])
    line(draw, [(1175, 1620), (1330, 1620)])
    node(draw, 1330, 1620)
    tag(draw, 1270, 1550, "PA3 RC_VA")
    line(draw, [(1330, 1620), (1392, 1620)])
    switch(draw, 1460, 1620, "S5 R开路")
    line(draw, [(1528, 1620), (1615, 1620)])
    node(draw, 1615, 1620)
    resistor(draw, 1750, 1620, "RR_1", "10 kΩ")
    line(draw, [(1615, 1620), (1685, 1620)])
    line(draw, [(1815, 1620), (1980, 1620)])
    node(draw, 1980, 1620)
    tag(draw, 1930, 1550, "PA2 RC_VB")
    line(draw, [(1615, 1620), (1615, 1440), (1682, 1440)])
    switch(draw, 1750, 1440, "S6 R短路")
    line(draw, [(1818, 1440), (1980, 1440), (1980, 1620)])
    line(draw, [(1980, 1620), (1980, 1660)])
    switch(draw, 1980, 1725, "S7 C开路", vertical=True)
    line(draw, [(1980, 1784), (1980, 1810)])
    capacitor(draw, 1980, 1875, "CR_1", "10 µF")
    line(draw, [(1980, 1940), (1980, 1985)])
    ground(draw, 1980, 1990)
    line(draw, [(1980, 1620), (2250, 1620), (2250, 1660)])
    switch(draw, 2250, 1725, "S8 C短路", vertical=True)
    line(draw, [(2250, 1784), (2250, 1985), (1980, 1985)])
    line(draw, [(1980, 1620), (2500, 1620), (2500, 1660)])
    switch(draw, 2500, 1725, "K5 放电", "PB12", vertical=True)
    line(draw, [(2500, 1784), (2500, 1792)])
    resistor(draw, 2500, 1875, "RDIS", "100 Ω", vertical=True)
    line(draw, [(2500, 1933), (2500, 1985), (2250, 1985)])
    image.save(OUT / "解决DIV与RC最终测试网络如何连接的问题.png")


def draw_controller():
    image = Image.new("RGB", (2800, 2060), BG)
    draw = ImageDraw.Draw(image)
    title(draw, "完整原理图（一）：U1 供电、时钟与外设", "按当前 Proteus 9.0 的 STM32F103C8 裸片画；网络名对应另一张 DIV/RC 测试网络图。", 2800)
    panel(draw, (40, 185, 810, 1040), "电源 / 启动 / 复位", "B5 CELL=3.3 V；所有 GND 共地")
    source(draw, 170, 420, "B5 CELL", "3.3 V")
    line(draw, [(170, 374), (170, 320), (380, 320)])
    tag(draw, 395, 320, "VDD 24/36/48")
    tag(draw, 395, 384, "VDDA 9")
    tag(draw, 395, 448, "VBAT 1")
    line(draw, [(170, 466), (170, 635)])
    ground(draw, 170, 645)
    tag(draw, 395, 525, "VSS 23/35/47")
    tag(draw, 395, 589, "VSSA 8")
    text(draw, (95, 717), "BOOT0 44 → 10 kΩ → GND", 26, INK, True)
    text(draw, (95, 773), "NRST 7 → 10 kΩ → 3.3 V", 26, INK, True)
    text(draw, (95, 829), "NRST 7 → 按键 → GND", 26, INK, True)
    text(draw, (95, 885), "VDD×3、VDDA 各并 100 nF", 25, BLUE)
    text(draw, (95, 931), "OSCIN 5 / OSCOUT 6 暂空", 25, GREEN, True)
    panel(draw, (845, 185, 1940, 1530), "U1 STM32F103C8 · 裸片", "引脚数字对应你截图中的芯片；先用 HSI 8 MHz")
    draw.rectangle((1060, 300, 1700, 1415), fill="#EAF3FB", outline=WIRE, width=5)
    text(draw, (1380, 354), "STM32F103C8", 42, BLUE, True, "mm")
    text(draw, (1380, 407), "LQFP48 / HSI 8 MHz", 26, INK, False, "mm")
    left_pins = [
        (490, "10 PA0  ADC0", "DIV_VB"), (555, "11 PA1  ADC1", "DIV_VA"),
        (620, "12 PA2  ADC2", "RC_VB"), (685, "13 PA3  ADC3", "RC_VA"),
        (785, "14 PA4", "模板键"), (850, "15 PA5", "检测/复测键"),
        (915, "16 PA6", "记录键"), (980, "17 PA7", "停止键"),
        (1080, "30 PA9 TX", "终端 RX"),
    ]
    for y, pin, net in left_pins:
        line(draw, [(940, y), (1060, y)])
        text(draw, (1080, y - 15), pin, 24, INK)
        tag(draw, 855, y - 46, net)
    right_pins = [
        (490, "18 PB0", "K1 DIV_TEST"), (555, "19 PB1", "K3 RC_TEST"),
        (620, "21 PB10", "K2 DIV_RUN"), (685, "22 PB11", "K4 RC_RUN"),
        (750, "25 PB12", "K5 RC_DISCH"), (850, "42 PB6", "SCL"),
        (915, "43 PB7", "SDA"), (1015, "26 PB13", "绿灯"),
        (1080, "27 PB14", "红灯"), (1180, "41 PB5", "阶跃标记"),
        (1245, "29 PA8", "VB标记"), (1310, "32 PA11", "VA标记"),
    ]
    for y, pin, net in right_pins:
        line(draw, [(1700, y), (1795, y)])
        text(draw, (1450, y - 15), pin, 23, INK)
        tag(draw, 1805, y - 46, net)
    panel(draw, (1980, 185, 2760, 1040), "I²C / 显示 / 存储", "同一总线；SCL/SDA 各上拉 4.7 kΩ 至 3.3 V")
    draw.rounded_rectangle((2050, 350, 2685, 565), 14, fill="#E7F3EF", outline=GREEN, width=4)
    text(draw, (2080, 385), "U2 OLED12864I2C", 31, GREEN, True)
    text(draw, (2080, 438), "2 VCC=3.3V   1 GND=地", 24)
    text(draw, (2080, 485), "3 SCL=PB6     4 SDA=PB7", 24)
    draw.rounded_rectangle((2050, 620, 2685, 925), 14, fill="#EAF3FB", outline=BLUE, width=4)
    text(draw, (2080, 657), "U3 24LC256", 31, BLUE, True)
    text(draw, (2080, 711), "8 VCC=3.3V   4 VSS=地", 23)
    text(draw, (2080, 759), "6 SCL=PB6     5 SDA=PB7", 23)
    text(draw, (2080, 807), "1/2/3 A0/A1/A2=地", 23)
    text(draw, (2080, 855), "7 WP=地（允许写入）", 23)
    panel(draw, (40, 1080, 810, 1980), "四个操作按键", "SW-SPST-MOM：一端接 GPIO，一端接 GND")
    for idx, (pin, label) in enumerate([("PA4", "模板"), ("PA5", "检测/复测"), ("PA6", "记录"), ("PA7", "停止")]):
        y = 1240 + idx * 158
        tag(draw, 120, y, pin)
        switch(draw, 440, y, f"{label}键")
        text(draw, (600, y - 18), "→ GND", 24)
    text(draw, (90, 1888), "GPIO 设置为上拉输入；按下读 0。", 25, GREEN, True)
    panel(draw, (845, 1570, 2760, 1980), "输出、调试与控制要求", "这些电路在采样后更新；LCD 刷新或存储写入不要插入 50/55 ms 窗口。")
    text(draw, (915, 1690), "PB13 → 1 kΩ → LED-GREEN → GND", 26, GREEN, True)
    text(draw, (915, 1760), "PB14 → 1 kΩ → LED-RED → GND", 26, RED, True)
    text(draw, (915, 1830), "PA9 TX → VIRTUAL TERMINAL 的 RX；终端共地。", 25)
    text(draw, (915, 1900), "K1—K5 控制输入各加 10 kΩ 下拉；控制负端接地。", 25, BLUE)
    image.save(OUT / "解决STM32F103C8供电时钟外设如何连接的问题.png")


if __name__ == "__main__":
    draw_catalog()
    draw_first_div()
    draw_networks()
    draw_controller()
    for path in OUT.glob("解决*.png"):
        print(path.name, path.stat().st_size)
