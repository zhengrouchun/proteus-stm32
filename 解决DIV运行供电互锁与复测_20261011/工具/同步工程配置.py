from pathlib import Path  # 使用路径对象定位本交付包中的工程。

root = Path(__file__).resolve().parents[1]  # 交付包为工具目录的上一层。
project = root / "工程"  # 指向独立复制的工程，避免覆盖用户原工程。
keil = project / "MDK-ARM" / "ADC_CubeMX_Keil.uvprojx"  # 找到 Keil 工程配置文件。
text = keil.read_text(encoding="utf-8")  # 读取原来的编译和输出设置。
text = text.replace("<OutputDirectory>ADC_CubeMX_Keil\\</OutputDirectory>", "<OutputDirectory>DIV_Power_Control\\</OutputDirectory>")  # 使用新输出目录隔离旧固件。
text = text.replace("<OutputName>ADC_CubeMX_Keil</OutputName>", "<OutputName>DIV_Power_Control</OutputName>")  # 将新固件输出名改为供电控制版本。
keil.write_text(text, encoding="utf-8")  # 保存编译配置。
ioc = project / "ADC_CubeMX_Keil.ioc"  # 找到 CubeMX 的引脚配置文件。
text = ioc.read_text(encoding="utf-8")  # 读取配置，以保留现有 ADC、UART 和时钟设置。
text = text.replace("Mcu.Pin4=VP_SYS_VS_ND\nMcu.Pin5=VP_SYS_VS_Systick\nMcu.PinsNb=6", "Mcu.Pin4=PA4\nMcu.Pin5=PA5\nMcu.Pin6=PB12\nMcu.Pin7=PB13\nMcu.Pin8=VP_SYS_VS_ND\nMcu.Pin9=VP_SYS_VS_Systick\nMcu.PinsNb=10")  # 将新增按钮和控制引脚加入芯片引脚清单。
additional = """PA4.GPIOParameters=GPIO_PuPd,GPIO_Label
PA4.GPIO_PuPd=GPIO_PULLUP
PA4.GPIO_Label=RETEST
PA4.Locked=true
PA4.Signal=GPIO_Input
PA5.GPIOParameters=GPIO_PuPd,GPIO_Label,GPIO_ModeDefaultEXTI
PA5.GPIO_PuPd=GPIO_PULLUP
PA5.GPIO_Label=STOP
PA5.GPIO_ModeDefaultEXTI=GPIO_MODE_IT_FALLING
PA5.Locked=true
PA5.Signal=GPXTI5
PB12.GPIOParameters=PinState,GPIO_Label,GPIO_Speed
PB12.PinState=GPIO_PIN_RESET
PB12.GPIO_Label=TEST_ENABLE
PB12.GPIO_Speed=GPIO_SPEED_FREQ_LOW
PB12.Locked=true
PB12.Signal=GPIO_Output
PB13.GPIOParameters=PinState,GPIO_Label,GPIO_Speed
PB13.PinState=GPIO_PIN_RESET
PB13.GPIO_Label=RUN_ENABLE
PB13.GPIO_Speed=GPIO_SPEED_FREQ_LOW
PB13.Locked=true
PB13.Signal=GPIO_Output
NVIC.EXTI9_5_IRQn=true\\:0\\:0\\:false\\:false\\:true\\:true\\:true\\:true
"""  # CubeMX 记录按钮上拉、停止中断和两个默认低电平输出。
if "PB12.Signal=GPIO_Output" not in text:  # 重复执行时避免生成重复配置项。
    text += additional  # 把新增引脚配置加入已有工程配置。
ioc.write_text(text, encoding="utf-8")  # 保存 CubeMX 配置文件。
print("已同步新固件输出目录及 PA4/PA5/PB12/PB13 引脚配置。")  # 显示本次同步范围。
