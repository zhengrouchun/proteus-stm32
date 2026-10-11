"""生成准确的RC接线参考图，并用附件数据核对理论电压；本脚本不操作Proteus。""" # 说明脚本用途和边界。
import json # 读取附件理论结果，并保存本次核对结果。
import math # 使用指数函数计算RC充电电压。
import sys # 将工作区已有的绘图依赖加入模块搜索路径。
from pathlib import Path # 使用明确的文件路径管理所有输出。
ROOT = Path(__file__).resolve().parent # 所有生成文件都保存到本脚本所在的RC文件夹。
sys.path.insert(0, str(ROOT.parent / "检路操作指南" / "绘图依赖")) # 复用工作区已有Pillow，不安装或更改系统软件。
from PIL import Image, ImageDraw, ImageFont # 使用确定性的绘图工具绘制电路符号和中文标注。
INK = "#172B3A" # 使用深色绘制正文。
WIRE = "#267449" # 使用绿色表示实际电气连接。
SYMBOL = "#743B41" # 使用暗红色表示电阻、电容和开关。
BLUE = "#195EA6" # 使用蓝色突出采样节点和时钟。
GRAY = "#536475" # 使用灰色绘制说明。
ORANGE = "#A54D16" # 使用橙色表示操作和故障开关。
REGULAR = "C:/Windows/Fonts/msyh.ttc" # 采用微软雅黑，保证中文和微法符号可读。
BOLD = "C:/Windows/Fonts/msyhbd.ttc" # 使用微软雅黑粗体区分标题与器件编号。
def text(draw, x, y, words, size=30, color=INK, bold=False, anchor=None): # 定义统一的文字绘制入口。
    draw.text((x, y), words, fill=color, font=ImageFont.truetype(BOLD if bold else REGULAR, size), anchor=anchor) # 根据字重、字号和锚点绘制文字。
def wire(draw, *points, color=WIRE, width=5): # 定义可绘制折线的电气连接函数。
    draw.line(points, fill=color, width=width, joint="curve") # 将指定端点按顺序连成导线。
def dot(draw, x, y): # 定义表示真实连接的节点圆点。
    draw.ellipse((x-7, y-7, x+7, y+7), fill=WIRE) # 用实心圆标明分支在此相连。
def ground(draw, x, y): # 定义公共地符号，输入坐标为导线端点。
    wire(draw, (x,y), (x,y+20)) # 将导线端点连接到地符号。
    for offset, half in ((20,30),(32,20),(44,10)): # 依次绘制三条长度递减的接地线。
        wire(draw, (x-half,y+offset), (x+half,y+offset), width=4) # 绘制本条接地横线。
def resistor(draw, x, y, name, value, vertical=False): # 定义具有明确数值和编号的电阻符号。
    if vertical: # 选择竖直放置的电阻。
        wire(draw, (x,y-75), (x,y-45)) # 绘制上端引脚。
        draw.rectangle((x-17,y-45,x+17,y+45), fill="white", outline=SYMBOL, width=5) # 绘制电阻本体。
        wire(draw, (x,y+45), (x,y+75)) # 绘制下端引脚。
        text(draw,x+32,y-42,name,29,bold=True) # 在右侧标明编号。
        text(draw,x+32,y,value,29) # 在右侧标明阻值。
    else: # 选择水平放置的电阻。
        wire(draw,(x-85,y),(x-55,y)) # 绘制左端引脚。
        draw.rectangle((x-55,y-17,x+55,y+17), fill="white", outline=SYMBOL,width=5) # 绘制电阻本体。
        wire(draw,(x+55,y),(x+85,y)) # 绘制右端引脚。
        text(draw,x,y-92,name,30,bold=True,anchor="mm") # 在本体上方显示编号。
        text(draw,x,y-48,value,30,anchor="mm") # 在编号下方显示阻值。
def capacitor(draw, x, y, name="C", value="10 μF"): # 定义电容的上下引脚和容量。
    wire(draw,(x,y-75),(x,y-16)) # 绘制接电容正端节点的上引脚。
    wire(draw,(x-34,y-16),(x+34,y-16),color=SYMBOL,width=6) # 绘制上极板。
    wire(draw,(x-34,y+16),(x+34,y+16),color=SYMBOL,width=6) # 绘制下极板。
    wire(draw,(x,y+16),(x,y+75)) # 绘制接地的下引脚。
    text(draw,x+50,y-41,name,30,bold=True) # 显示电容编号。
    text(draw,x+50,y+4,value,30) # 显示电容容量。
def switch(draw, x, y, name, closed=False, vertical=False): # 定义串联断路和并联短路的手动开关。
    def at(a,b): # 把标准水平开关坐标换算到所需方向。
        return (x-b,y+a) if vertical else (x+a,y+b) # 竖直开关按九十度旋转坐标。
    wire(draw,at(-75,0),at(-30,0)) # 绘制开关输入引脚。
    wire(draw,at(30,0),at(75,0)) # 绘制开关输出引脚。
    for a in (-30,30): # 依次绘制两个触点。
        cx,cy=at(a,0) # 计算当前触点的位置。
        draw.ellipse((cx-5,cy-5,cx+5,cy+5),fill=SYMBOL) # 绘制触点。
    wire(draw,at(-30,0),at(30,0) if closed else at(24,-28),color=SYMBOL) # 闭合时连接触点，断开时画出抬起的触臂。
    text(draw,x+40,y-15,name,29,ORANGE,True) if vertical else text(draw,x,y-66,name,29,ORANGE,True,"mm") # 在不遮挡导线的位置显示开关编号。
def source(draw, x, y, name, volts): # 定义具有正负极的理想电压源。
    wire(draw,(x,y-90),(x,y-45)) # 绘制电源正极引脚。
    draw.ellipse((x-45,y-45,x+45,y+45),fill="white",outline=SYMBOL,width=5) # 绘制电压源符号。
    text(draw,x,y-23,"+",27,SYMBOL,True,"mm") # 标明上端为正极。
    text(draw,x,y+23,"−",27,SYMBOL,True,"mm") # 标明下端为负极。
    wire(draw,(x,y+45),(x,y+90)) # 绘制电源负极引脚。
    text(draw,x+62,y-33,name,29,bold=True) # 标明电源编号。
    text(draw,x+62,y+7,volts,29) # 标明电源电压。
def controlled(draw, x, y, name, gpio, vertical=False): # 定义四端电压控制开关的简化接线符号。
    if vertical: # 选择放电支路所需的竖直主通道。
        draw.rectangle((x-42,y-50,x+42,y+50),fill="white",outline=SYMBOL,width=4) # 绘制受控开关本体。
        wire(draw,(x,y-75),(x,y-50)) # 绘制主通道上端。
        wire(draw,(x,y+50),(x,y+75)) # 绘制主通道下端。
        wire(draw,(x,y-30),(x+17,y+24),color=SYMBOL,width=4) # 用断开的触臂表示默认关闭主通道。
        wire(draw,(x+42,y-20),(x+85,y-20)) # 绘制控制正端。
        wire(draw,(x+42,y+20),(x+85,y+20)) # 绘制控制负端。
        text(draw,x+95,y-35,"+  "+gpio,26,BLUE) # 控制正端接指定GPIO网络。
        text(draw,x+95,y+5,"−  GND",26) # 控制负端接公共地。
        text(draw,x-65,y,name,30,ORANGE,True,"rm") # 显示受控开关编号。
    else: # 选择电源输入支路所需的水平主通道。
        draw.rectangle((x-55,y-36,x+55,y+36),fill="white",outline=SYMBOL,width=4) # 绘制受控开关本体。
        wire(draw,(x-90,y),(x-55,y)) # 绘制主通道输入端。
        wire(draw,(x+55,y),(x+90,y)) # 绘制主通道输出端。
        wire(draw,(x-30,y),(x+23,y-22),color=SYMBOL,width=4) # 表示复位时断开的主通道。
        wire(draw,(x-25,y+36),(x-25,y+67)) # 绘制控制正端引线。
        wire(draw,(x+25,y+36),(x+25,y+67)) # 绘制控制负端引线。
        text(draw,x-25,y+80,"+ "+gpio,25,BLUE,anchor="mt") # 给正控制端标明GPIO网络。
        text(draw,x+25,y+119,"− GND",25,anchor="mt") # 给负控制端标明地网络。
        text(draw,x,y-66,name+"  VSWITCH",29,ORANGE,True,"mm") # 明确器件库搜索名称。
def header(draw, title, subtitle, width): # 定义每张图统一的标题和说明。
    text(draw,70,45,title,48,bold=True) # 写明本图解决的问题。
    text(draw,72,118,subtitle,29,GRAY) # 给出阅读顺序和适用范围。
    wire(draw,(70,178),(width-70,178),color="#DCE3E8",width=2) # 用细分隔线区分标题与图纸。
def basic(): # 生成与用户附件对应的基本RC接线图。
    im=Image.new("RGB",(2300,1250),"white"); d=ImageDraw.Draw(im) # 创建适合放大阅读的白底图纸。
    header(d,"RC 基本接法与复测放电","主电路与附件一致；S_TEST 用于施加阶跃，S_DIS 用于复测前放电。",2300) # 标明新增开关的用途。
    source(d,200,595,"V_TEST","1.000 V") # 放置外部一伏测试电压源。
    wire(d,(200,505),(200,350),(315,350)) # 将电源正极引至测试开关。
    switch(d,390,350,"S_TEST",False) # 画出初始断开的测试开关。
    wire(d,(465,350),(565,350)); resistor(d,650,350,"Rs","2 kΩ") # 放置不能省略的源电阻。
    wire(d,(735,350),(950,350),(1115,350)); dot(d,950,350) # 标明两个电阻之间的VA节点。
    resistor(d,1200,350,"R","10 kΩ"); wire(d,(1285,350),(1610,350),(1610,505)) # 串联被测电阻，并将输出引到电容。
    capacitor(d,1610,580); wire(d,(1610,655),(1610,850)); ground(d,1610,850) # 将十微法电容下端接地。
    dot(d,1610,350); text(d,950,410,"VA → PA3 / ADC1_IN3",32,BLUE,True,"mm") # 标明VA连接到STM32第十三脚。
    text(d,1610,270,"VB → PA2 / ADC1_IN2",32,BLUE,True,"mm") # 标明VB连接到STM32第十二脚。
    wire(d,(200,685),(200,850)); ground(d,200,850) # 将电源负极接公共地。
    dot(d,1610,445); wire(d,(1610,445),(1950,445),(1950,505)) # 从电容上端引出独立放电支路。
    resistor(d,1950,580,"R_DIS","100 Ω",True); wire(d,(1950,655),(1950,680)) # 放置一百欧姆放电限流电阻。
    switch(d,1950,755,"S_DIS",False,True); wire(d,(1950,830),(1950,850)); ground(d,1950,850) # 放电开关下端接地，测量时保持断开。
    text(d,85,965,"操作：S_TEST 断开 → S_DIS 闭合 30 ms → S_DIS 断开 → S_TEST 闭合，此刻记为 t = 0。",30,ORANGE,True) # 明确零初态的建立和计时基准。
    text(d,85,1027,"正常标称：τ = (2 kΩ + 10 kΩ) × 10 μF = 120 ms",32) # 标明包含源电阻的正确时间常数。
    text(d,85,1090,"VB 在 50 ms：340.759 mV；VA 在 55 ms：894.611 mV。两者不是同一时刻的读数。",30,BLUE) # 写出附件一致的理论采样值。
    text(d,85,1160,"只观察波形时可不接 MCU；所有 GND 同网。此图是接线参考，尚未作 Proteus 实测。",27,GRAY) # 区分图纸与实际软件测量。
    im.save(ROOT/"解决RC基本电路与放电支路怎么接的问题.png") # 把基本电路图片保存到RC文件夹。
def full(): # 生成带九工况设置和自动控制接口的最终RC参考图。
    im=Image.new("RGB",(3000,1800),"white"); d=ImageDraw.Draw(im) # 为主电路、接口和控制细节准备足够空间。
    header(d,"RC 最终接线参考","STM32F103C8；1 V 测试、3 V 运行、单故障开关、100 Ω 放电；同名网络相连。",3000) # 明确这是RC支路的完整参考接法。
    source(d,170,460,"V_TEST","1.000 V"); ground(d,170,550) # 放置测试电源，并将负极接地。
    wire(d,(170,370),(410,370)); controlled(d,500,370,"K3","RC_TEST") # 测试源正极通过K3接入被测网络，控制标注避开电源文字。
    wire(d,(590,370),(630,370),(630,550)) # 将测试开关输出接到公共输入节点。
    source(d,170,760,"V_RUN","3.000 V"); ground(d,170,850) # 放置独立的三伏运行电源。
    wire(d,(170,670),(410,670)); controlled(d,500,670,"K4","RC_RUN") # 运行源正极通过K4接入公共输入。
    wire(d,(590,670),(630,670),(630,550),(725,550)); dot(d,630,550) # 两个电源只在开关之后汇合。
    resistor(d,810,550,"Rs","2 kΩ"); wire(d,(895,550),(1010,550),(1105,550)); dot(d,1010,550) # 接入源电阻，并标明VA节点。
    switch(d,1180,550,"S5  R断路",True); wire(d,(1255,550),(1315,550)) # 串联故障开关S5正常时闭合。
    resistor(d,1400,550,"R","10 kΩ"); wire(d,(1485,550),(1720,550),(1720,605)); dot(d,1720,550) # 将被测电阻输出接到VB。
    wire(d,(1010,550),(1010,320),(1280,320)); switch(d,1355,320,"S6  R短路",False) # 在电阻与S5整体两端放置正常断开的短路开关。
    wire(d,(1430,320),(1720,320),(1720,550)) # 将短路支路接回VB。
    text(d,1010,660,"RC_VA",33,BLUE,True,"mm"); text(d,1720,460,"RC_VB",33,BLUE,True,"mm") # 用同名网络标识实际ADC连接。
    switch(d,1720,680,"S7  C断路",True,True); wire(d,(1720,755),(1720,785)) # 串联电容断路开关正常时闭合。
    capacitor(d,1720,860); wire(d,(1720,935),(1720,1100)); ground(d,1720,1100) # 十微法电容下端接公共地。
    wire(d,(1720,550),(1990,550),(1990,715)); switch(d,1990,790,"S8  C短路",False,True) # 在VB和地之间放置正常断开的电容短路开关。
    wire(d,(1990,865),(1990,1100)); ground(d,1990,1100) # 完成电容短路支路的接地。
    dot(d,1720,770); wire(d,(1720,770),(1370,770),(1370,785)) # 放电支路向左引出，连接S7下游的电容上端，并避免跨越短路支路。
    resistor(d,1370,860,"R_DIS","100 Ω",True); wire(d,(1370,935),(1370,950)) # 放置放电限流电阻。
    controlled(d,1370,1025,"K5","RC_DIS",True); wire(d,(1370,1100),(1370,1160)); ground(d,1370,1160) # 放电开关由专用GPIO控制，控制负端接地。
    text(d,2470,270,"U1  STM32F103C8",34,bold=True) # 标明右侧接口说明对应的芯片型号。
    text(d,2470,340,"PA2（12脚）← RC_VB",29,BLUE) # VB接ADC通道二。
    text(d,2470,395,"PA3（13脚）← RC_VA",29,BLUE) # VA接ADC通道三。
    text(d,2470,470,"PB1（19脚）→ RC_TEST",28) # PB1控制测试电源开关K3。
    text(d,2470,525,"PB11（22脚）→ RC_RUN",28) # PB11控制运行电源开关K4。
    text(d,2470,580,"PB12（25脚）→ RC_DIS",28) # PB12控制电容放电开关K5。
    text(d,2470,670,"GPIO：推挽输出，初值 LOW",27,ORANGE) # 上电时保持三路控制开关均断开。
    text(d,2470,725,"VDD / VDDA / VBAT = 3.3 V",27) # MCU电源独立于被测网络的测试和运行源。
    text(d,2470,780,"VSS / VSSA = GND",27) # MCU模拟地和数字地使用公共地。
    text(d,2470,850,"不接外部晶振，HSI = 8 MHz",27,BLUE) # 明确本图采用的时钟方案。
    text(d,2470,908,"供电、复位、BOOT0 见配置说明",26,GRAY) # 将最小系统细节引导到同目录说明。
    text(d,90,1228,"正常：S5、S7 闭合；S6、S8 断开。每次只设置一个故障。",32,ORANGE,True) # 标明四个故障开关的正确初态。
    text(d,90,1285,"偏差工况直接改值：R = 5k / 20k；C = 5u / 20u。正常恢复 R = 10k、C = 10u。",29) # 说明九工况中的四种参数变化。
    text(d,90,1360,"每个 VSWITCH 的控制正端接对应 GPIO，控制负端接 GND；控制正端另接 10 kΩ 下拉。",30) # 防止将控制端接入被测主回路，并规定硬件默认断开。
    text(d,90,1418,"建议目标：RON = 0.1 Ω；ROFF ≥ 1 GΩ；VON ≈ 2.4 V；VOFF ≈ 0.9 V，按本机属性核实。",29) # 给出需要在Proteus模型中确认的目标开关参数。
    text(d,90,1500,"检测：K3/K4断开 → K5闭合30 ms → K5断开 → K3闭合并计时 → 50 ms读VB → 55 ms读VA。",29,BLUE,True) # 明确开关互锁和采样顺序。
    text(d,90,1560,"正常确认后：先断K3，再合K4；异常或停止：K3/K4均断开。K5放电时，两路电源必须断开。",29) # 给出检测结束后的供电操作。
    text(d,90,1640,"本图接口是RC专用分配；现有DIV固件占用PB12作测试控制，需改映射后才能接本图。",29,ORANGE) # 明确实际工作区代码与本参考分配之间的冲突。
    text(d,90,1710,"此图为可照接的原理图参考，未执行九工况Proteus仿真；VSWITCH实际引脚方位以库模型为准。",27,GRAY) # 不将接线图当作已经运行通过的原生工程。
    im.save(ROOT/"解决RC九工况与STM32控制接口怎么接的问题.png") # 保存完整RC接线图。
def clock(): # 生成Proteus、CubeMX与ADC一致的时钟设置图。
    im=Image.new("RGB",(2400,1520),"white"); d=ImageDraw.Draw(im) # 创建时钟树及设置文字的图纸。
    header(d,"STM32F103C8 时钟与 ADC 配置","基础方案：内部 HSI 8 MHz；外部 HSE/LSE 禁用；PLL 不作为系统时钟来源。",2400) # 标明适用于本任务的时钟选择。
    for x,label,value in ((140,"HSI","8 MHz"),(710,"SYSCLK","8 MHz"),(1280,"AHB / HCLK","8 MHz"),(1850,"APB2 / PCLK2","8 MHz")): # 依次绘制系统时钟主路径。
        draw_box=(x,250,x+360,400) # 计算当前时钟节点的位置。
        d.rectangle(draw_box,outline=BLUE,width=3) # 给时钟节点画出边界。
        text(d,x+180,295,label,32,BLUE,True,"mm") # 标明节点名称。
        text(d,x+180,355,value,35,INK,True,"mm") # 标明节点频率。
        if x<1850: # 最后一个节点无需向右继续连接。
            wire(d,(x+360,325),(x+550,325),color=BLUE,width=4) # 连接到下一个时钟节点。
            d.polygon(((x+550,325),(x+536,316),(x+536,334)),fill=BLUE) # 画出时钟流向箭头。
    text(d,1115,282,"/1",27,BLUE,anchor="mm") # 标明AHB不分频。
    text(d,1685,282,"/1",27,BLUE,anchor="mm") # 标明APB2不分频。
    wire(d,(1460,400),(1460,500),(1000,500),color=BLUE,width=4) # 从HCLK向左引出APB1时钟分支，避免导线遮挡标签。
    text(d,970,500,"APB1 / PCLK1 = 8 MHz（/1）",30,BLUE,anchor="rm") # 标明APB1时钟与分频。
    wire(d,(2030,400),(2030,600),(1510,600),color=BLUE,width=4) # 从APB2引出ADC预分频支路。
    text(d,1060,600,"ADC prescaler = /2 → ADCCLK = 4 MHz",32,BLUE,True,"mm") # 标明ADC时钟的计算路径。
    text(d,85,725,"Proteus：双击 STM32F103C8",35,bold=True) # 指明Proteus中打开属性的位置。
    text(d,85,790,"Clock Frequency（若该模型提供）填 8MHz。",29) # 明确频率单位，避免只填无单位数字。
    text(d,85,847,"Program File 选择按同一时钟配置编译的 .hex / .elf。",29) # 指定固件和模型设置必须一致。
    text(d,85,904,"5/6脚 OSCIN/OSCOUT 留空；3/4脚 LSE 引脚留空。",29) # 说明内部HSI方案无需放置外部晶振。
    text(d,85,981,"CubeMX：RCC 与 Clock Configuration",35,bold=True) # 指明CubeMX中修改时钟的入口。
    text(d,85,1046,"HSE = Disable；LSE = Disable；System Clock Mux 选 HSI。",29) # 指定振荡器及系统时钟来源。
    text(d,85,1103,"AHB / APB1 / APB2 prescaler 均 /1；ADC prescaler /2。",29) # 给出四个分频设置。
    text(d,85,1160,"确认 SYSCLK/HCLK/PCLK1/PCLK2 都为 8 MHz，ADC 为 4 MHz。",29) # 要求核对最终频率而不是只改输入数字。
    text(d,1320,725,"ADC1：软件逐次选择通道",35,bold=True) # 用单次转换实现两个不同时刻的采样。
    text(d,1320,790,"PA2 = ADC1_IN2（VB）；PA3 = ADC1_IN3（VA）。",29) # 标明每个采样点对应的引脚和通道。
    text(d,1320,847,"Sampling Time = 239.5 cycles；Right alignment。",29) # 使用长采样时间和右对齐结果。
    text(d,1320,904,"Scan / Continuous / DMA 关闭；软件触发单次转换。",29) # 避免连续采样与特征采样时刻混淆。
    text(d,1320,961,"12位原始码 0～4095；先校准，再做0/1/3V校验。",29) # 给出实际ADC返回范围和校验动作。
    text(d,1320,1038,"计时：TIM2 或 1 ms SysTick",35,bold=True) # 给出可实现采样时间基准的两个途径。
    text(d,1320,1103,"TIM2 Clock Source = Internal Clock；输入 8 MHz。",29) # 在本图APB1不分频时TIM2时钟为八兆赫。
    text(d,1320,1160,"Prescaler = 7 → 1 MHz计数；Period = 65535。",29) # 定时器除数为PSC加一，计数周期是一微秒。
    text(d,85,1275,"时刻都从 K3 接通开始：50 ms 读 VB，55 ms 读 VA；不是读完 VB 后再等 55 ms。",31,ORANGE,True) # 防止将VA采样错推迟到一百零五毫秒。
    text(d,85,1340,"一次ADC转换约 (239.5 + 12.5) / 4 MHz = 63 μs；50/55 ms 是充电等待时间。",30) # 区分ADC内部采样周期和RC响应采样时刻。
    text(d,85,1410,"用示波器或标记引脚核对实际时刻 ±1 ms；采样结束后再刷新显示、发串口或写存储。",29,GRAY) # 将设置值与实际时序验收区分开。
    im.save(ROOT/"解决Proteus与CubeMX时钟及ADC配置不一致的问题.png") # 将时钟配置图保存到指定文件夹。
def verify(): # 独立核对RC九工况标称电压，不伪造实测记录。
    report=json.loads((ROOT.parent/"文件"/"理论复核结果.json").read_text(encoding="utf-8")) # 读取用户给出的理论结果作为比较基准。
    rows=[] # 保存每种工况的比较结果。
    for state in report["templates"]["RC"]["states"]: # 遍历RC正常和八种异常工况。
        name=state["name"]; r=state["x_ohm"]; c=state["y_ohm_or_F"] # 获取当前工况名称、电阻及电容。
        if name=="R断路": vb,va=0.0,1.0 # 已放电的电容保持零电压，VA无负载等于测试源。
        elif name=="C断路": vb,va=1.0,1.0 # 电容断开后主回路无电流，两个节点均为一伏。
        elif name=="C短路": vb,va=0.0,r/(2000.0+r) # VB被短接到地，VA由两个串联电阻分压决定。
        else: # 计算正常、R短路和阻容偏差的充电响应。
            if name=="R短路": r=0.0 # 短路时被测电阻从时间常数中去掉，源电阻仍保留。
            tau=(2000.0+r)*c # 以源电阻与被测电阻之和计算时间常数。
            vb=1.0-math.exp(-0.050/tau) # 计算阶跃后五十毫秒的VB电压。
            va=1.0-2000.0/(2000.0+r)*math.exp(-0.055/tau) # 计算阶跃后五十五毫秒的VA电压。
        error=max(abs(vb*1000-state["nominal_VB_mV"]),abs(va*1000-state["nominal_VA_mV"])) # 以毫伏比较本次独立计算与附件。
        assert error<0.001,(name,error) # 要求九种工况均与附件在千分之一毫伏以内一致。
        rows.append({"id":state["id"],"状态":name,"理论VB_mV":round(vb*1000,3),"理论VA_mV":round(va*1000,3),"与附件最大差_mV":error}) # 保存可复查的理论结果。
    (ROOT/"解决RC采样时刻与理论电压核对的问题.json").write_text(json.dumps({"验证范围":"独立理论计算；未执行Proteus仿真或实际ADC采集","工况":rows},ensure_ascii=False,indent=2),encoding="utf-8") # 将核对结果保存到RC文件夹。
basic() # 生成便于首次搭建的基本电路图。
full() # 生成带故障开关与STM32接口的最终接线参考。
clock() # 生成时钟树和ADC设置说明图。
verify() # 核对所有九种RC工况的标称电压。
print("已生成3张接线配置图；RC九工况理论值与附件一致。") # 输出真实完成范围。
