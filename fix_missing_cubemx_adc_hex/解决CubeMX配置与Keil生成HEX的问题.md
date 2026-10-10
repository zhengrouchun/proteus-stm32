# 解决 CubeMX 配置不清、Keil 无法生成 HEX 的问题

这是与现有 Proteus 9.0 原理图匹配的**实际 CubeMX 生成工程**，不是空白模板。芯片 STM32F103C8T6；Proteus 中元件名 `STM32F103C8`。CubeMX 的 `.ioc` 已生成 MDK-ARM 工程；应用代码写在 `Src/main.c` 的 `USER CODE` 区；Keil 已编译出 `ADC_CubeMX_Keil.hex`，日志 0 错误、0 警告。

## 先打开哪些文件

- 用 STM32CubeMX 打开 `ADC_CubeMX_Keil/ADC_CubeMX_Keil.ioc`，核对所有芯片配置。
- 用 Keil μVision 打开 `ADC_CubeMX_Keil/MDK-ARM/ADC_CubeMX_Keil.uvprojx`，查看和编译应用。
- 逐句阅读 `ADC_CubeMX_Keil/Src/main.c`：写入的每条采样、换算和串口语句旁均有中文作用说明。CubeMX 自动生成的初始化代码保留在原位。
- 在 Proteus 的 U1 → **Program File** 中选择 `ADC_CubeMX_Keil/MDK-ARM/ADC_CubeMX_Keil/ADC_CubeMX_Keil.hex`。

## 从空白工程逐项配置 CubeMX

1. `New Project` → `MCU/MPU Selector` → 搜索 **STM32F103C8T6** → 选择 **STM32F103C(8-B)Tx / LQFP48**。不要误选 F103R/F103V 或其他封装。
2. 进入 `Pinout & Configuration`，给 **PA0-WKUP** 选 **ADC1_IN0**，对应原理图 `DIV_VB`。CubeMX 在 `.ioc` 中保存为 `ADCx_IN0`，并分配给 ADC1；实际生成的 `MX_ADC1_Init()` 确认为 `ADC_CHANNEL_0`。
3. 给 **PA1** 选 **GPIO_Analog**，对应原理图 `DIV_VA`。这样 PA1 始终是无上下拉的模拟输入，Keil 代码在读 VA 时用 `HAL_ADC_ConfigChannel(... ADC_CHANNEL_1 ...)` 动态选择 ADC1 通道 1。该做法保证 ADC 常规序列只有一个 rank，与逐路轮询代码一致。如果把 PA1 也添加到固定规则序列，CubeMX 可能自动打开两通道扫描，与下面代码的读取方式不匹配。
4. `Connectivity → USART1` 选 **Asynchronous**。CubeMX 自动占用 **PA9=USART1_TX、PA10=USART1_RX**。此项目只发送读数，Proteus 只需 PA9 接虚拟终端 RXD；PA10 不用接线。串口参数：**9600 Baud、8 Bits、1 Stop Bit、None Parity、None Hardware Flow Control**。本 `.ioc` 仍是 CubeMX 默认 TX/RX 模式，代码只调用发送函数。
5. `Analog → ADC1 → Parameter Settings`：**Scan Conversion Mode=Disabled**；**Continuous Conversion Mode=Disabled**；**Discontinuous Conversion Mode=Disabled**；**External Trigger Conversion=Software Start**；**Data Alignment=Right**；**Number of Conversion=1**。常规序列 **Rank 1=Channel 0**，**Sampling Time=239.5 Cycles**。启用一次转换后，应用先读 PA0，再切到 PA1 读第二次。
6. `System Core → RCC`：**HSE=Disable、LSE=Disable**；`SYS → Debug` 可保持 **No Debug**，因为仿真直接加载 HEX，暂时不用实体 ST-LINK。要兼顾真板在线调试，可改为 Serial Wire，ADC/串口不受影响。
7. `Clock Configuration`：**HSI=8 MHz；PLL=Off；SYSCLK Source=HSI；SYSCLK=8 MHz；AHB Prescaler=1；HCLK=8 MHz；APB1 Prescaler=1；PCLK1=8 MHz；APB2 Prescaler=1；PCLK2=8 MHz；ADC Prescaler=2；ADCCLK=4 MHz**。Proteus 的 U1 `Clock Frequency` 也设 **8 MHz**。这套方案不需要 8 MHz 外部晶振及其负载电容；4 MHz ADC 时钟足够，并且不超过 F103 ADC 时钟限制。
8. `System Core → NVIC`：保持 **SysTick enabled、Priority 15**。**ADC1_2 interrupt=Disabled、USART1 global interrupt=Disabled**；本程序用 `HAL_ADC_PollForConversion` 和 `HAL_UART_Transmit` 轮询，不需要 ADC 或串口 IRQ。**DMA 也不启用**。SysTick 为 `HAL_Delay(500)` 与超时计时提供毫秒节拍。
9. `Project Manager`：Project Name 填 `ADC_CubeMX_Keil`；Toolchain/IDE 选 **MDK-ARM V5**；Firmware Package 用本机 **STM32Cube FW_F1 V1.8.7**；勾选 **Keep User Code when re-generating**；点 `Generate Code`。本交付的 `.ioc` 已按这些值生成，直接打开即可检查。

### 为什么这样选

时钟选内部 HSI，是为了先把 MCU 固件和 ADC 验证跑通，减少 Proteus 外部晶振接线。ADC 选择单次软件触发，是因为分压状态每 500 ms 才报告一次，轮询两路足够直观；239.5 个 ADC 周期让分压节点的采样保持时间充裕。USART1 只用 PA9 发送，Proteus Virtual Terminal 可以直接看到 MCU 计算后的电压，便于与两块电压表的模拟读数对照。没有用到的 OLED、EEPROM、LED、逻辑分析仪和 RC 电容暂时不占 MCU 引脚。

## Proteus 元件和连接

按你已有分压图使用：`STM32F103C8` 一片，`RES` 三只分别设置 **Rs=2 kΩ、R1=10 kΩ、R2=10 kΩ**；`BATTERY` 或直流电源分别提供 **1.0 V**（分压器）和 **3.3 V**（MCU）；`SW-SPST` 一只串联 R1 用于断路故障；另一只开关并联 R2 用于短路故障；`SW-SPST-MOM` 一只给 NRST 作瞬时复位；`VIRTUAL TERMINAL` 一只、直流电压表两只用于观察。真实供电或较完整的电源模型可加 **100 nF 非极性去耦电容**和 **10 µF 电源滤波电容**，跨接 3.3 V 与 GND；第一轮最小仿真使用理想 3.3 V 电源时，它们不是启动 HEX 的必要条件。不要把 10 µF 当成 8 MHz 晶振的负载电容；此时根本不接外晶振。

接线顺序：`1 V 正端 → Rs 2 kΩ → VA → SW1 → R1 10 kΩ → VB → R2 10 kΩ → GND`。故障开关 SW2 跨接 **VB 与 GND**，与 R2 并联；**VA→PA1（引脚 11）**、**VB→PA0（引脚 10）**；**PA9（引脚 30）→Virtual Terminal 的 RXD**。1 V 负端、3.3 V 负端、R2 下端、U1 的 VSSA/供电地都共地。U1 的 **VDDA 和 VBAT** 接 3.3 V；同时检查 Proteus 该型号隐藏的 VDD/VSS 电源引脚网络。**BOOT0 用 10 kΩ 下拉到 GND**；**NRST 用 10 kΩ 上拉到 3.3 V，瞬时复位开关按下时才接 GND**。复位按钮不连接到 PA0/PA1，也不需要 CubeMX GPIO 配置。

SW1/SW2/SW3 都是 Proteus 中直接改变模拟电路的开关，不由 MCU 读取，**CubeMX 不给它们分配 GPIO**。若之后要 MCU 检测按键，再另开 GPIO 输入并接对应引脚；这不是当前分压验证的必要部分。

## Keil 写代码与编译

打开 `.uvprojx` 后，重点看 `Src/main.c` 的 `USER CODE`：

- `Includes` 加入 `stdio.h/string.h`，用于组成报告文本。
- `PD` 用有意义的名字定义 **3300 mV ADC 参考电压、4095 最大码值、20 ms ADC 超时、100 ms 串口超时、500 ms 报告周期**。手写代码里没有无意义的 `0U` 一类魔法数字。
- `PFP` 声明 `ReadAdcChannel`、`SendReport`；`USER CODE 0` 完成两函数。`ReadAdcChannel` 切换 ADC 通道、启动/等待/取值/停止；`SendReport` 把原始码值换算毫伏，并由 USART1 输出。
- `USER CODE 2` 在所有外设初始化完成之后运行 `HAL_ADCEx_Calibration_Start`；`USER CODE 3` 依次读 **Channel 0→VB**、**Channel 1→VA**，发送报告并延时。

Keil 里检查 `Project → Options for Target → Output → Create HEX File` 已勾选，然后点 **Rebuild**（快捷键通常 Ctrl+F7）。当前工程已设置 `CreateHexFile=1`。构建完成后可在 `MDK-ARM/ADC_CubeMX_Keil/` 找到同名 `.hex`。命令行也可复现：

```powershell
& 'D:\Stu15\Documents\Keil stm32\code\UV4\UV4.exe' -b 'ADC_CubeMX_Keil.uvprojx' -t 'ADC_CubeMX_Keil' -o 'keil_build.log'
```

该命令需要在 `ADC_CubeMX_Keil/MDK-ARM` 工作目录中运行。Build 日志末尾已验证 `FromELF: creating hex file`、`0 Error(s), 0 Warning(s)`；HEX 各记录校验和和结束记录有效。**尚未在你的 Proteus 原工程中实测串口、电压和三种故障状态**，故硬件/仿真运行结果需要下一步检查。

## 装入 Proteus 后要看到什么

U1 `Program File` 指向**此工程** `ADC_CubeMX_Keil.hex`，U1 时钟 8 MHz；虚拟终端 9600、8N1。SW1 闭合、SW2 断开是正常：约 `VA=909 mV、VB=455 mV`。SW1 断开、SW2 断开是 R1 断路：约 `VA=1000 mV、VB=0 mV`。SW1 闭合、SW2 闭合是 R2 短路：约 `VA=833 mV、VB=0 mV`。串口每 500 ms 报一行，括号中有 12 位 ADC 原始值。保存每种状态的 SW1/SW2、串口一行、两块电压表读数和截图编号；若结果不符先查共地、VDDA、VA/VB 标签及 SW1/SW2 当前状态。

## 这次用了什么文件与方法

阅读了原先 `P1_CreateProject.ioc`，确认芯片、CubeMX 固件包、MDK-ARM 工具链；读取你发的原理图/Proteus 截图，固定 VA/PA1、VB/PA0 的真实映射。用本机 STM32CubeMX 6.18.1 建立、保存并生成 `ADC_CubeMX_Keil.ioc`；打开生成的 `Src/main.c` 和 `Src/stm32f1xx_hal_msp.c` 核对 ADC/USART/GPIO 代码；把采样逻辑放入 `USER CODE`，确保今后 CubeMX 重新生成时保留手写部分；最后用本机 Keil μVision 构建与 Intel HEX 校验来验证交付。CubeMX 启动期间的联网更新检查曾输出第三方包下载警告，但本地 F1 固件包成功用于生成工程，Keil 构建成功。
