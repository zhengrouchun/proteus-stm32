# 解决 STM32F103C8 的 `Program file is not specified`

> 后续已按你的要求建立**由 STM32CubeMX 实际生成**的 ADC/USART/Keil 工程。现在优先使用 [解决CubeMX配置与Keil生成HEX的问题](../fix_missing_cubemx_adc_hex/解决CubeMX配置与Keil生成HEX的问题.md) 中的新 `.ioc`、源码和 HEX。本页保留此前独立工程的构建记录，避免混淆两个 HEX 路径。

## 卡住的是什么、由什么引起

Proteus 原理图仍有 STM32F103C8（U1），而 U1 属性里的 **Program File 为空**。模拟器要执行 U1 的机器码；电阻和电源连好并不会自动生成 MCU 程序，所以仿真在启动阶段报 `Program file is not specified`，接着报 `Real Time Simulation failed to start`。这不是 VA/VB 电阻数值计算错，也不是 SW1 当前开关状态本身导致的启动错误。先前只讨论了“删掉 U1 测纯模拟电路”，没有完成你要的 MCU 固件链路，这是漏项。

## 已做成的可用文件

- `ADC_U1_HEX_FIX/Core/Src/main.c`：真正运行在 U1 上的应用代码。每条关键语句旁的中文注释说明了作用；使用有意义的常量名，没有难懂的 `0U` 之类占位值。
- `ADC_U1_HEX_FIX/MDK-ARM/ADC_U1_HEX_FIX.uvprojx`：Keil 工程，可再次编译。
- `ADC_U1_HEX_FIX/MDK-ARM/ADC_U1_HEX_FIX/ADC_U1_HEX_FIX.hex`：已经编译出来、供 Proteus U1 加载的 Intel HEX。
- `ADC_U1_HEX_FIX/MDK-ARM/keil_build.log`：Keil 构建记录，末尾显示 `0 Error(s), 0 Warning(s)` 和 `FromELF: creating hex file`。
- `生成缺失HEX工程.py`：说明该独立工程如何从现有 CubeMX 工程复制启动文件、HAL/CMSIS、创建 Keil 工程。再次运行会重写工程配置；应用代码 `main.c` 不会被覆盖。

这套工程**基于本机已有的 CubeMX 生成工程** `D:\Proteus\project\P1_CreateProject`，将其 STM32F103C8 启动文件、HAL/CMSIS 和 Keil 工程配置复制出来，再为 ADC/USART 改写应用代码并实际经 Keil 编译。没有声称已在你当前 Proteus 原理图里完成实时仿真；那一步需要你给 U1 指定上面的 HEX 并运行。

## 你现在在 Proteus 9.0 里要做的操作

1. 保存当前电路，双击 **U1 = STM32F103C8**。
2. 找到 **Program File**，通过文件选择器选中 `D:\Proteus\project\解决U1缺少程序文件\ADC_U1_HEX_FIX\MDK-ARM\ADC_U1_HEX_FIX\ADC_U1_HEX_FIX.hex`。一定选 `.hex` 文件，不能选 `.uvprojx` 或 `.c`。
3. 把 U1 的 **Clock Frequency** 设成 **8 MHz**。固件使用内部 HSI 8 MHz，PD0/PD1 不用接 8 MHz 外部晶振。
4. 核对你的接线：`DIV_VB → PA0 / 引脚10 / ADC1_IN0`，`DIV_VA → PA1 / 引脚11 / ADC1_IN1`。这正是前面截图里的实际顺序。
5. 把 **Virtual Terminal 的 RXD** 接到 U1 **PA9 / 引脚30 / USART1_TX**。终端属性设为 **9600 baud、8 data bits、no parity、1 stop bit**。终端的 TXD 暂时不用接；RTS/CTS 也不用。
6. 让 **BAT1 的负端、电路 GND、BAT2 的负端、U1 的 VSSA/供电地** 共地。U1 的 VDDA、VBAT 接 +3.3 V；还要核对 Proteus 隐藏的 VDD/VSS 供电网络是否分别接 3.3 V/GND。BAT1 只能给分压器提供 1 V，不能给 MCU 供电。
7. 正常工况：SW1 闭合、R2 旁路开关 SW2 断开。R1 断路：SW1 断开、SW2 断开。R2 短路：SW1 闭合、SW2 闭合。保持 SW3 复位开关断开，避免 U1 一直处于复位。
8. 点击 Proteus 左下角运行三角。若仍提示 `Program file is not specified`，首先回到 U1 的 Program File 检查路径是否真的保存；如果日志点名别的 MCU，也检查那个器件。
9. 双击 Virtual Terminal 看周期性报告，例如 `VA=909 mV (...)  VB=455 mV (...)`。也可继续用电压表测真实 VA/VB 节点；串口值来自 ADC，电压表值来自模拟电路，两者应接近。终端没显示时先查 **PA9→RXD**、波特率、U1 复位和供电。

**保护接线**：VA/VB 的 0–1 V 在 0–3.3 V ADC 输入范围内。不要把 BAT2 的 3.3 V 接到 BAT1 的 1 V 节点。`R2` 旁路开关是故障注入：闭合它会故意把 VB 短到地，不应把它当作常规按键输入。

## 若你想从 CubeMX 界面自己重新生成

这是复现路径；已有的 Keil 工程和 HEX 可以直接用，不必先重做 CubeMX。打开 STM32CubeMX，`New Project` → 搜 `STM32F103C8T6` → 选该芯片：

1. **Pinout & Configuration**：PA0 设 `ADC1_IN0`（VB），PA1 设 `ADC1_IN1`（VA）。USART1 选 Asynchronous，PA9 为 `USART1_TX`。PA10 若被自动占用为 RX 可以留空不用。
2. **System Core → RCC**：HSE 选 `Disable`，LSE 选 `Disable`。**SYS → Debug** 可以选择 `Serial Wire`，仅影响 SWD 引脚；Proteus 通过 HEX 运行无需实体 ST-LINK。
3. **Clock Configuration**：HSI = 8 MHz、SYSCLK 选 HSI、PLL 关、AHB/APB1/APB2 分频都为 1，ADC prescaler 设 2，得到 ADCCLK = 4 MHz。
4. **ADC1**：12 位（F103 固定）、单次转换、软件触发、右对齐。程序每次先配置一个通道并读一次，因此 **Scan Conversion Mode = Disabled，Number of Conversion = 1**；两个引脚都为模拟模式，通道采样时间设 239.5 cycles。若 CubeMX 把两个通道自动排成两个 rank，删去第二个 rank；代码会在每次采样前动态切到 IN0/IN1。
5. **USART1**：9600 baud、8 data bits、1 stop bit、no parity、no hardware flow control。若界面支持 TX only，选 TX only；否则 Asynchronous TX/RX 也可以，程序只发送。
6. **Project Manager**：工程名可设 `ADC_U1_HEX_FIX`，Toolchain/IDE 选 **MDK-ARM V5**，Firmware Package 用已安装的 STM32CubeF1 包，点 `Generate Code`。CubeMX 只生成初始化工程，不会替你写分压器采样、毫伏换算和报告逻辑。
7. 用 Keil 打开生成的 `.uvprojx`。将 `main.c` 里标注的 ADC 采样、UART 输出逻辑放进 CubeMX 的 `USER CODE` 区域；**不要直接把本工程整个 `main.c` 覆盖新生成文件**，否则新工程的 `stm32f1xx_it.c` 可能与本文件的 `SysTick_Handler` 重复定义。若使用本交付目录内现成的 `.uvprojx`，直接编译即可，不需要再复制代码。
8. Keil 的 **Project → Options for Target → Output → Create HEX File** 勾选；点击 **Rebuild**。构建成功后到输出文件夹找 `.hex`，再在 Proteus U1 的 Program File 选择它。

CubeMX/Keil/Proteus 分工：CubeMX 生成外设初始化与工程；Keil 编译你写的 C 代码并生成 HEX；Proteus 加载 HEX 才能模拟 U1。这三个步骤不能互相代替。

## 对照读数、记录办法

本程序每 500 ms 报一行 `VA=... mV (原始码)  VB=... mV (原始码)`。以 3.3 V ADC 参考电压换算，理论期望如下（电压表和 ADC 会有采样量化误差）：

- **正常**：VA ≈ 909 mV、VB ≈ 455 mV；ADC 原始码约 1128/564。
- **R1 断路**：VA ≈ 1000 mV、VB ≈ 0 mV；ADC 原始码约 1241/0。
- **R2 短路**：VA ≈ 833 mV、VB ≈ 0 mV；ADC 原始码约 1034/0。

记录每一种状态的：SW1/SW2 位置、串口 VA/VB 毫伏和 ADC 原始码、电压表读数、截图编号、与理论值的绝对误差。若 ADC 显示零而电压表非零，优先检查共地、VDDA/VSSA 和 PA0/PA1 标签。若只看到 UART 字符乱码，先核对 9600 baud 与 8 MHz 运行时钟。

## 阅读文件与使用的位置

- `D:\Proteus\project\P1_CreateProject\P1_CreateProject.ioc`：核对原模板的芯片确为 STM32F103C8T6、已有工具链为 MDK-ARM；原工程使用外部振荡器，所以新程序明确改用 HSI，Proteus 不必外接晶振。
- `D:\Proteus\project\P1_CreateProject\MDK-ARM\P1_CreateProject.uvprojx`：取得 Keil 工程的器件、启动文件、编译器、包含目录和 **CreateHexFile=1** 配置，改写成独立 ADC 工程。
- `D:\Proteus\project\P1_CreateProject\Core\Inc\stm32f1xx_hal_conf.h`：启用 HAL ADC/UART 模块。
- `D:\Proteus\project\P1_CreateProject\Drivers\...` 与 `MDK-ARM\startup_stm32f103xb.s`：使用现成 HAL、CMSIS 头文件及 STM32F103 启动代码；程序不是凭空生成 HEX。
- 你发来的 Proteus 电路截图和错误日志：确认 **DIV_VB→PA0、DIV_VA→PA1**，并用 `Program file is not specified` 定位到 U1 缺固件。

使用过的命令：`python 生成缺失HEX工程.py` 建立独立工程；`UV4.exe -b ADC_U1_HEX_FIX.uvprojx -t ADC_U1_HEX_FIX -o keil_build.log` 编译；Python 按 Intel HEX 每行校验和规则检查生成文件。最终日志为零错误、零警告，HEX 校验和及结束记录有效。这只验证了**构建与文件格式**，尚不能替代在你的原理图中点击运行、检查 UART 和 ADC 读数。
