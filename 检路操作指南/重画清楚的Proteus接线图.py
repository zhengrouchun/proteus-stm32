"""把当前 Proteus 元件按三个搭建阶段画成可读的接线参考图。"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIRECTORY = Path(__file__).resolve().parent
FONT_REGULAR = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
BACKGROUND = "#F9F9F3"
GRID_COLOR = "#E9EBE1"
WIRE_COLOR = "#24733C"
SYMBOL_COLOR = "#533039"
TEXT_COLOR = "#172A39"
BLUE = "#1C5EAA"
ORANGE = "#A7551E"
GRAY = "#52616D"


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def label(draw, x, y, words, size=29, color=TEXT_COLOR, bold=False, anchor=None):
    draw.text((x, y), words, font=font(size, bold), fill=color, anchor=anchor)


def wire(draw, points, width=6):
    draw.line(points, fill=WIRE_COLOR, width=width, joint="curve")


def dot(draw, x, y):
    draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=WIRE_COLOR)


def ground(draw, x, y):
    wire(draw, [(x, y - 34), (x, y)])
    draw.line((x - 26, y, x + 26, y), fill=WIRE_COLOR, width=6)
    draw.line((x - 17, y + 11, x + 17, y + 11), fill=WIRE_COLOR, width=5)
    draw.line((x - 8, y + 22, x + 8, y + 22), fill=WIRE_COLOR, width=4)


def power(draw, x, y, name="3.3V"):
    wire(draw, [(x, y), (x, y - 45)])
    draw.polygon([(x, y - 67), (x - 19, y - 44), (x + 19, y - 44)], fill=WIRE_COLOR)
    label(draw, x + 27, y - 76, name, 25, WIRE_COLOR, True)


def resistor(draw, x, y, name, value, vertical=False):
    if vertical:
        wire(draw, [(x, y - 75), (x, y - 48)])
        draw.rectangle((x - 18, y - 48, x + 18, y + 48), fill=BACKGROUND, outline=SYMBOL_COLOR, width=6)
        wire(draw, [(x, y + 48), (x, y + 75)])
        label(draw, x + 32, y - 48, name, 27, TEXT_COLOR, True)
        label(draw, x + 32, y - 9, value, 27)
    else:
        wire(draw, [(x - 80, y), (x - 55, y)])
        draw.rectangle((x - 55, y - 18, x + 55, y + 18), fill=BACKGROUND, outline=SYMBOL_COLOR, width=6)
        wire(draw, [(x + 55, y), (x + 80, y)])
        label(draw, x, y - 82, name, 29, TEXT_COLOR, True, "mm")
        label(draw, x, y - 48, value, 27, GRAY, False, "mm")


def switch(draw, x, y, name, vertical=False, closed=False):
    if vertical:
        wire(draw, [(x, y - 80), (x, y - 31)])
        wire(draw, [(x, y + 31), (x, y + 80)])
        draw.ellipse((x - 7, y - 37, x + 7, y - 23), fill=SYMBOL_COLOR)
        draw.ellipse((x - 7, y + 23, x + 7, y + 37), fill=SYMBOL_COLOR)
        draw.line((x, y - 30, x if closed else x + 24, y + 30 if closed else y + 20), fill=SYMBOL_COLOR, width=6)
        label(draw, x + 32, y - 30, name, 28, ORANGE, True)
    else:
        wire(draw, [(x - 85, y), (x - 34, y)])
        wire(draw, [(x + 34, y), (x + 85, y)])
        draw.ellipse((x - 41, y - 7, x - 27, y + 7), fill=SYMBOL_COLOR)
        draw.ellipse((x + 27, y - 7, x + 41, y + 7), fill=SYMBOL_COLOR)
        draw.line((x - 34, y, x + 34 if closed else x + 24, y if closed else y - 35), fill=SYMBOL_COLOR, width=6)
        label(draw, x, y - 94, name, 28, ORANGE, True, "mm")


def cell(draw, x, y, name, voltage):
    wire(draw, [(x, y - 78), (x, y - 27)])
    draw.line((x - 39, y - 27, x + 39, y - 27), fill=SYMBOL_COLOR, width=7)
    draw.line((x - 23, y + 4, x + 23, y + 4), fill=SYMBOL_COLOR, width=7)
    wire(draw, [(x, y + 4), (x, y + 78)])
    label(draw, x + 56, y - 54, name, 29, TEXT_COLOR, True)
    label(draw, x + 56, y - 15, voltage, 28)
    label(draw, x - 44, y - 72, "+", 26, ORANGE, True)
    label(draw, x - 43, y + 9, "−", 27, ORANGE, True)


def capacitor(draw, x, y, name, value):
    wire(draw, [(x, y - 77), (x, y - 20)])
    draw.line((x - 37, y - 20, x + 37, y - 20), fill=SYMBOL_COLOR, width=7)
    draw.line((x - 37, y + 20, x + 37, y + 20), fill=SYMBOL_COLOR, width=7)
    wire(draw, [(x, y + 20), (x, y + 77)])
    label(draw, x + 48, y - 36, name, 28, TEXT_COLOR, True)
    label(draw, x + 48, y + 3, value, 27)


def tag(draw, x, y, name, left=False):
    if left:
        draw.polygon([(x, y - 18), (x - 35, y), (x, y + 18)], fill=BACKGROUND, outline=WIRE_COLOR)
        label(draw, x - 48, y, name, 27, BLUE, True, "rm")
    else:
        draw.polygon([(x, y - 18), (x + 35, y), (x, y + 18)], fill=BACKGROUND, outline=WIRE_COLOR)
        label(draw, x + 46, y, name, 27, BLUE, True, "lm")


def canvas(width, height, title, subtitle):
    image = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for x in range(0, width, 40):
        draw.line((x, 0, x, height), fill=GRID_COLOR, width=1)
    for y in range(0, height, 40):
        draw.line((0, y, width, y), fill=GRID_COLOR, width=1)
    draw.rectangle((0, 0, width, 185), fill="#E9EEF0")
    label(draw, 70, 45, title, 57, TEXT_COLOR, True)
    label(draw, 74, 118, subtitle, 30, GRAY)
    return image, draw


def save(image, filename):
    image.save(OUTPUT_DIRECTORY / filename, optimize=True)


def draw_first_stage():
    # 首轮电压表测试采用独立纯模拟电路，避免无固件的MCU阻止仿真启动。
    image, draw = canvas(2400, 1530, "首轮 DIV 电压测试｜独立纯分压工程", "先另存工程副本，在副本中删除 U1 和不用的数字模型；只断开 U1 导线不能消除缺程序报错")
    cell(draw, 200, 800, "BAT1", "1V")
    wire(draw, [(200, 722), (200, 450), (360, 450)])
    resistor(draw, 440, 450, "RS / R5", "2kΩ")
    wire(draw, [(520, 450), (650, 450), (815, 450)])
    dot(draw, 650, 450)
    label(draw, 650, 390, "VA", 35, BLUE, True, "mm")
    switch(draw, 900, 450, "SW1闭合：正常", closed=True)
    wire(draw, [(985, 450), (1030, 450)])
    resistor(draw, 1110, 450, "R1", "10kΩ")
    wire(draw, [(1190, 450), (1400, 450), (1910, 450)])
    dot(draw, 1400, 450)
    dot(draw, 1650, 450)
    label(draw, 1400, 390, "VB", 35, BLUE, True, "mm")
    wire(draw, [(1650, 450), (1650, 645)])
    resistor(draw, 1650, 720, "R2", "10kΩ", vertical=True)
    wire(draw, [(1650, 795), (1650, 1100)])
    wire(draw, [(1910, 450), (1910, 640)])
    switch(draw, 1910, 720, "SW3断开", vertical=True)
    label(draw, 1960, 790, "R2短路开关", 27, ORANGE)
    wire(draw, [(1910, 800), (1910, 1100)])
    wire(draw, [(200, 878), (200, 1100), (1910, 1100)])
    for meter_x, meter_name in [(650, "表A：测VA"), (1400, "表B：测VB")]:
        wire(draw, [(meter_x, 450), (meter_x, 780)])
        draw.ellipse((meter_x - 70, 780, meter_x + 70, 920), fill="#FFFFFF", outline=SYMBOL_COLOR, width=6)
        label(draw, meter_x, 850, "V", 43, TEXT_COLOR, True, "mm")
        label(draw, meter_x - 35, 745, "+", 28, ORANGE, True)
        label(draw, meter_x - 35, 925, "−", 28, ORANGE, True)
        label(draw, meter_x + 95, 835, meter_name, 28, BLUE, True)
        wire(draw, [(meter_x, 920), (meter_x, 1100)])
        dot(draw, meter_x, 1100)
    dot(draw, 1650, 1100)
    wire(draw, [(1040, 1100), (1040, 1160)])
    ground(draw, 1040, 1160)
    label(draw, 95, 1260, "正常：SW1闭合、SW3断开 → VA≈0.909V、VB≈0.455V", 32, BLUE, True)
    label(draw, 95, 1320, "R1断路：SW1断开、SW3断开 → VA≈1V、VB≈0V", 32, BLUE, True)
    label(draw, 95, 1380, "R2短路：SW1闭合、SW3闭合 → VA≈0.833V、VB≈0V", 32, BLUE, True)
    label(draw, 95, 1450, "SW1和SW3均用SW-SPST；上面是接线参考图，实际读数需运行后记录。", 27, GRAY)
    save(image, "解决第一步DIV元件摆放与连线看不清的问题.png")
    save(image, "解决未指定程序文件导致DIV仿真无法启动的问题.png")

def draw_mcu_stage():
    image, draw = canvas(3100, 1680, "第1张补图｜U1最小系统：3.3V、复位、BOOT0、ADC与指示灯", "这张图按你图二的电源线和接地画法展开；实际 Proteus U1 的VDD/VSS引脚可能隐藏")
    cell(draw, 270, 540, "BAT2", "3.3V")
    wire(draw, [(270, 462), (270, 285), (2100, 285)])
    wire(draw, [(270, 618), (270, 790)])
    ground(draw, 270, 790)
    label(draw, 350, 235, "3.3V母线：与U1隐藏VDD同名", 31, BLUE, True)

    wire(draw, [(620, 285), (620, 465)])
    capacitor(draw, 620, 542, "C1", "100nF")
    ground(draw, 620, 700)
    wire(draw, [(620, 619), (620, 700)])

    draw.rectangle((1110, 360, 1640, 1410), fill="#ECEEDC", outline=SYMBOL_COLOR, width=7)
    label(draw, 1375, 395, "U1 STM32F103C8", 36, TEXT_COLOR, True, "mm")
    wire(draw, [(1375, 285), (1375, 360)])
    dot(draw, 1375, 285)
    label(draw, 1405, 310, "VDD 24/36/48（隐藏）", 27, BLUE, True)
    wire(draw, [(1375, 1410), (1375, 1480)])
    ground(draw, 1375, 1480)
    label(draw, 1410, 1450, "VSS 23/35/47（隐藏）", 27, BLUE, True)

    left_pins = [
        (540, "PA0 / 10", "DIV_VB"),
        (615, "PA1 / 11", "DIV_VA"),
        (810, "PB13 / 26", "绿灯"),
        (975, "PB14 / 27", "红灯"),
        (1160, "PA9 / 30", "TX")
    ]
    for y, pin_text, _ in left_pins:
        wire(draw, [(1020, y), (1110, y)])
        label(draw, 1130, y - 20, pin_text, 28)
    tag(draw, 1020, 540, "DIV_VB", left=True)
    tag(draw, 1020, 615, "DIV_VA", left=True)

    wire(draw, [(1020, 810), (880, 810)])
    resistor(draw, 800, 810, "R_LED_G", "1kΩ")
    wire(draw, [(720, 810), (590, 810)])
    draw.ellipse((530, 780, 590, 840), fill="#71D573", outline=SYMBOL_COLOR, width=5)
    draw.polygon([(577, 793), (577, 827), (549, 810)], fill=SYMBOL_COLOR)
    draw.line((544, 792, 544, 828), fill=SYMBOL_COLOR, width=5)
    wire(draw, [(530, 810), (470, 810), (470, 850)])
    ground(draw, 470, 850)
    label(draw, 405, 730, "D1绿", 27, TEXT_COLOR, True)

    wire(draw, [(1020, 975), (880, 975)])
    resistor(draw, 800, 975, "R_LED_R", "1kΩ")
    wire(draw, [(720, 975), (590, 975)])
    draw.ellipse((530, 945, 590, 1005), fill="#F27878", outline=SYMBOL_COLOR, width=5)
    draw.polygon([(577, 958), (577, 992), (549, 975)], fill=SYMBOL_COLOR)
    draw.line((544, 957, 544, 993), fill=SYMBOL_COLOR, width=5)
    wire(draw, [(530, 975), (470, 975), (470, 1015)])
    ground(draw, 470, 1015)
    label(draw, 405, 895, "D2红", 27, TEXT_COLOR, True)

    wire(draw, [(1020, 1160), (680, 1160)])
    tag(draw, 680, 1160, "TERMINAL_RXD", left=True)
    label(draw, 250, 1220, "虚拟终端 RXD 接PA9；发送由固件负责", 27, GRAY)

    right_pins = [(530, "NRST / 7"), (720, "VDDA / 9"), (810, "VBAT / 1"), (900, "VSSA / 8"), (1130, "BOOT0 / 44")]
    for y, pin_text in right_pins:
        label(draw, 1440, y - 20, pin_text, 28)
        wire(draw, [(1640, y), (1760, y)])
    wire(draw, [(1760, 530), (2070, 530)])
    dot(draw, 1950, 530)
    wire(draw, [(1950, 285), (1950, 355)])
    resistor(draw, 1950, 430, "R_RESET", "10kΩ", vertical=True)
    wire(draw, [(1950, 505), (1950, 530)])
    wire(draw, [(2070, 530), (2290, 530), (2290, 630)])
    switch(draw, 2290, 710, "SW2复位按钮", vertical=True)
    wire(draw, [(2290, 790), (2290, 830)])
    ground(draw, 2290, 830)
    label(draw, 2390, 625, "按下NRST接地", 27, ORANGE, True)

    wire(draw, [(1760, 720), (1870, 720)])
    power(draw, 1870, 720, "3.3V / VDD")
    wire(draw, [(1760, 810), (2010, 810)])
    power(draw, 2010, 810, "3.3V / VDD")
    wire(draw, [(1760, 900), (1870, 900), (1870, 950)])
    ground(draw, 1870, 950)
    wire(draw, [(1760, 1130), (1950, 1130), (1950, 1160)])
    resistor(draw, 1950, 1235, "R_BOOT", "10kΩ", vertical=True)
    wire(draw, [(1950, 1310), (1950, 1360)])
    ground(draw, 1950, 1360)
    label(draw, 1550, 1530, "BOOT0需低电平，才能从用户Flash启动", 25, ORANGE, True)

    draw.rounded_rectangle((2290, 1010, 3020, 1460), radius=22, fill="#FFFFFF", outline="#CED7D3", width=4)
    label(draw, 2340, 1040, "时钟设置", 32, TEXT_COLOR, True)
    label(draw, 2340, 1110, "HSI：8MHz", 29, BLUE, True)
    label(draw, 2340, 1170, "HSE：关闭", 29)
    label(draw, 2340, 1230, "PLL：关闭", 29)
    label(draw, 2340, 1290, "PD0/PD1：暂不接晶振", 29)
    label(draw, 2340, 1350, "U1属性 Clock=8MHz", 29, ORANGE, True)
    label(draw, 110, 1580, "图中LED圆圈是简化画法；在Proteus按LED阳极/阴极标记接，不能只凭圆圈方向判断。", 28, GRAY)
    save(image, "解决STM32最小系统供电复位BOOT0实际接线不清的问题.png")


def draw_rc_stage():
    image, draw = canvas(3000, 1810, "第2张｜DIV通过后再搭 RC：先固定1V，再加入受控源", "第一行先验证电容充放电；第二行解释你已找到的 VSWITCH 四个端子怎样用")
    label(draw, 105, 245, "A. RC 最小电路：只有 1V、2kΩ、10kΩ、10µF", 36, TEXT_COLOR, True)
    cell(draw, 180, 650, "BAT3", "1V")
    wire(draw, [(180, 572), (180, 500), (350, 500)])
    resistor(draw, 430, 500, "RS_RC", "2kΩ")
    wire(draw, [(510, 500), (660, 500)])
    dot(draw, 660, 500)
    label(draw, 660, 440, "RC_VA", 32, BLUE, True, "mm")
    resistor(draw, 890, 500, "R_RC", "10kΩ")
    wire(draw, [(660, 500), (810, 500)])
    wire(draw, [(970, 500), (1160, 500)])
    dot(draw, 1160, 500)
    label(draw, 1160, 440, "RC_VB", 32, BLUE, True, "mm")
    wire(draw, [(1160, 500), (1160, 590)])
    capacitor(draw, 1160, 667, "C_RC", "10µF，正端在上")
    wire(draw, [(1160, 744), (1160, 850)])
    wire(draw, [(180, 728), (180, 850), (1160, 850)])
    ground(draw, 660, 884)
    wire(draw, [(660, 850), (660, 884)])
    wire(draw, [(660, 500), (660, 340), (760, 340)])
    tag(draw, 760, 340, "RC_VA")
    wire(draw, [(1160, 500), (1160, 340), (1260, 340)])
    tag(draw, 1260, 340, "RC_VB")
    label(draw, 1470, 340, "RC_VA → U1 PA3 / 13脚", 31, BLUE, True)
    label(draw, 1470, 410, "RC_VB → U1 PA2 / 12脚", 31, BLUE, True)
    label(draw, 1470, 520, "每次测量前先让 C_RC 放电至接近0V。", 30)
    label(draw, 1470, 585, "在 t=0 接通1V，示波器 A通道看VB。", 30)
    label(draw, 1470, 650, "理论时间常数：(2kΩ+10kΩ)×10µF=120ms。", 30, ORANGE, True)
    label(draw, 1470, 715, "50ms与55ms的电压以后通过时序程序采样。", 29)

    draw.line((100, 1010, 2890, 1010), fill="#CFD9D3", width=4)
    label(draw, 105, 1040, "B. 再用 VSWITCH 切换1V测试源与3V运行源", 35, TEXT_COLOR, True)
    cell(draw, 190, 1300, "BAT3", "1V")
    cell(draw, 190, 1580, "BAT4", "3V")
    wire(draw, [(190, 1222), (350, 1222)])
    switch(draw, 470, 1222, "K1 / VSWITCH")
    wire(draw, [(350, 1222), (385, 1222)])
    wire(draw, [(555, 1222), (1250, 1222), (1250, 1362)])
    wire(draw, [(190, 1502), (350, 1502)])
    switch(draw, 470, 1502, "K2 / VSWITCH")
    wire(draw, [(350, 1502), (385, 1502)])
    wire(draw, [(555, 1502), (1250, 1502), (1250, 1362)])
    dot(draw, 1250, 1362)
    wire(draw, [(1250, 1362), (1390, 1362)])
    tag(draw, 1390, 1362, "RC_SOURCE")
    ground(draw, 190, 1420)
    wire(draw, [(190, 1378), (190, 1420)])
    ground(draw, 190, 1700)
    wire(draw, [(190, 1658), (190, 1700)])
    label(draw, 610, 1285, "K1 控制+→PB1；控制−→GND", 28, BLUE, True)
    label(draw, 610, 1565, "K2 控制+→PB11；控制−→GND", 28, BLUE, True)
    label(draw, 1690, 1150, "VSWITCH 有两组端子：", 31, TEXT_COLOR, True)
    label(draw, 1690, 1220, "主回路两端串在电源正极路径。", 29)
    label(draw, 1690, 1280, "控制+端接PB脚，控制−端接GND。", 29)
    label(draw, 1690, 1340, "两个CELL的负极各接公共GND。", 29)
    label(draw, 1690, 1400, "两个开关不能同时闭合。", 29, ORANGE, True)
    label(draw, 1690, 1460, "首轮固定1V时，先不用K1/K2。", 29, ORANGE, True)
    save(image, "解决RC电路与VSWITCH四端子使用不清的问题.png")


def draw_peripheral_stage():
    image, draw = canvas(3400, 1830, "第3张｜分压与RC都读对后，再接显示、存储、按键和串口", "每个蓝色网络名都要用 Proteus 左侧 LBL 工具贴到实际导线上；先核对一颗EEPROM")
    draw.rectangle((1130, 330, 1800, 1460), fill="#ECEEDC", outline=SYMBOL_COLOR, width=7)
    label(draw, 1465, 360, "U1  STM32F103C8", 38, TEXT_COLOR, True, "mm")
    left_pins = [
        (500, "PB6 / SCL", "I2C_SCL"),
        (575, "PB7 / SDA", "I2C_SDA"),
        (755, "PA4 / 模板键", "KEY_MODE"),
        (880, "PA5 / 检测键", "KEY_TEST"),
        (1005, "PA6 / 记录键", "KEY_SAVE"),
        (1130, "PA7 / 停止键", "KEY_STOP"),
        (1280, "PA9 / TX", "USART_TX"),
    ]
    for y, pin_name, net_name in left_pins:
        wire(draw, [(1010, y), (1130, y)])
        tag(draw, 1010, y, net_name, left=True)
        label(draw, 1150, y - 20, pin_name, 28)
    right_pins = [(1250, "PB13 / 绿灯", "LED_RUN"), (1360, "PB14 / 红灯", "LED_FAULT")]
    for y, pin_name, net_name in right_pins:
        label(draw, 1480, y - 20, pin_name, 28)
        wire(draw, [(1800, y), (1930, y)])
        tag(draw, 1930, y, net_name)

    label(draw, 100, 310, "左边：四个瞬时按钮", 34, TEXT_COLOR, True)
    button_info = [("KEY_MODE", 670), ("KEY_TEST", 820), ("KEY_SAVE", 970), ("KEY_STOP", 1120)]
    for name, y in button_info:
        label(draw, 110, y - 20, name, 27, BLUE, True)
        wire(draw, [(330, y), (390, y)])
        switch(draw, 480, y, "SW-SPST-MOM")
        wire(draw, [(565, y), (700, y), (700, y + 40)])
        ground(draw, 700, y + 70)
        wire(draw, [(700, y + 40), (700, y + 70)])
    label(draw, 95, 1350, "GPIO设上拉输入：松开=1、按下=0。", 28, ORANGE, True)
    label(draw, 95, 1410, "NRST复位按钮单独接，不算四个操作键。", 27, GRAY)

    label(draw, 2200, 310, "右边：OLED + 一颗24LC256", 34, TEXT_COLOR, True)
    draw.rectangle((2410, 400, 3310, 770), fill="#EFF4F5", outline=SYMBOL_COLOR, width=5)
    label(draw, 2860, 430, "LCD1 OLED12864I2C", 30, TEXT_COLOR, True, "mm")
    oled_rows = [(525, "1 GND", "GND"), (590, "2 VCC", "3.3V"), (655, "3 SCL", "I2C_SCL"), (720, "4 SDA", "I2C_SDA")]
    for y, pin_name, net_name in oled_rows:
        wire(draw, [(2280, y), (2410, y)])
        tag(draw, 2280, y, net_name, left=True)
        label(draw, 2430, y - 20, pin_name, 28)
    draw.rectangle((2410, 850, 3310, 1240), fill="#EFF4F5", outline=SYMBOL_COLOR, width=5)
    label(draw, 2860, 875, "U2 24LC256（只留一颗）", 30, TEXT_COLOR, True, "mm")
    eeprom_rows = [(965, "6 SCK", "I2C_SCL"), (1035, "5 SDA", "I2C_SDA"), (1105, "7 WP", "GND"), (1175, "1/2/3 A0/A1/A2", "GND")]
    for y, pin_name, net_name in eeprom_rows:
        wire(draw, [(2280, y), (2410, y)])
        tag(draw, 2280, y, net_name, left=True)
        label(draw, 2430, y - 20, pin_name, 26)
    label(draw, 2180, 1300, "SCL/SDA 各接 4.7kΩ 上拉到3.3V。", 27, ORANGE, True)
    label(draw, 2180, 1350, "U2 电源脚若隐藏：查属性和网表中的VCC/GND。", 26, GRAY)

    draw.rounded_rectangle((95, 1540, 3310, 1750), radius=24, fill="#FFFFFF", outline="#CED7D3", width=4)
    label(draw, 130, 1565, "其余元件按这个规则接：", 31, TEXT_COLOR, True)
    label(draw, 130, 1620, "绿灯：PB13 → 1kΩ → LED阳极，阴极→GND；红灯：PB14同理。", 29)
    label(draw, 130, 1680, "VIRTUAL TERMINAL 的 RXD → PA9(TX)；示波器只接测量点与公共地。", 29)
    save(image, "解决OLED存储器按键指示灯外设该接哪些脚的问题.png")


draw_first_stage()
draw_mcu_stage()
draw_rc_stage()
draw_peripheral_stage()
