# Proteus 流水灯不亮：时钟单位与 LED 限流电阻排查

检查日期：2026-10-03。对象：STM32F103C8、P1_CreateProject、PA1～PA4 四路流水灯。

## 结论与验证边界

当前 main.c 已有正确的低电平点亮、每路停留约 500ms 的流水灯逻辑。GPIO 初始化、引脚宏、SysTick 中断和已有编译产物能够对应起来。

已确认的配置问题：

1. U1 的 OSC Frequency 保存为 `72`，没有 MHz 单位。这不能表示代码要求的 72MHz。对照本地 CM3 模型帮助，该属性非零时用于指定处理器主时钟；不要把它当成 CubeMX 页面上默认以 MHz 显示的数字输入框。
2. 四个 LED 的串联电阻 R4、R7、R5、R6 都为 10kΩ，电流过小，可能使动画亮度很低。
3. 主工程 1.0create_projectt.pdsprj 没有四个蓝灯；包含四个蓝灯的是 Project Backups 内的 Autosaved 版本，和用户截图更接近。须保存当前电路，避免再次打开旧电路。

这些是静态检查得到的真实配置问题。本次未操作 Proteus 图形界面，也未观察修改后的 LED 波形，不能宣称已经完成仿真验证。当前 PC 究竟停在时钟初始化、异常处理还是延时中，需要下面的动态检查确认。

## 建议按顺序处理

1. 停止仿真。在当前四灯电路中双击 U1，将 OSC Frequency 的 `72` 改为明确带单位的 `72MHz`（或 `72000000`）。这是与当前代码的系统时钟相匹配的强制频率设置，X1 的晶振参数仍应为 `8MHz`。
2. Clock Scale 当前为默认的 `8 Times`，不是 PLL 倍频，也不是给 `72` 添加 MHz 单位。先保留默认值；若要排查延时精度，再暂时设为 `Off`，代价是仿真可能较慢。观察 Proteus 显示的仿真时间，不要只按电脑上的等待时间判断 500ms。
3. 将 R4、R7、R5、R6 从 `10k` 改为 `330R`。R2 是 NRST 的上拉电阻，应保留 10k；不要把所有 10k 都改成 330Ω。
4. 确认电源为 3.3V，U1 隐藏的 VDD/VSS 正确接到电源和地，VDDA/VSSA 也正确连接。截图中的箭头本身不能证明实际电压值；D1 亮也只能说明 D1 所在供电支路有电。
5. 保持接法为电源 → 电阻 → LED 阳极 → LED 阴极 → 对应 PA 引脚。当前代码以 RESET 点亮，SET 熄灭，与这个接法一致。
6. 在 Keil 用 Rebuild（菜单命令 Rebuild all target files）生成 HEX。U1 的 Program File 指向：
   `D:\Proteus\project\P1_CreateProject\MDK-ARM\P1_CreateProject\P1_CreateProject.hex`
7. 正式保存当前四灯电路，再重新启动仿真。预期 LED1 → LED2 → LED3 → LED4，每路约 0.5 秒，一轮约 2 秒（HAL 的最小等待保证会增加少量时间）。

本地 CM3 官方帮助提醒：频率属性非零时会绕过模型的部分时钟控制机制，不适合验证 PLL 寄存器调频。如果明确需要仿真真实 RCC 时钟树，可以另行使用 OSC Frequency=0，由代码和外部 8MHz 时钟决定频率；该路径还需要检查具体 STM32 模型的晶振输入行为。不要在没有测量的情况下把 8MHz 填入强制处理器主频字段并期待得到 72MHz。

## 为什么代码正确仍然看不到流水灯

### 主时钟与 HAL 时间基准不一致

main.c 的 SystemClock_Config 使用 HSE、不分频、PLL ×9，目标是 8MHz ×9 = 72MHz。stm32f1xx_hal_conf.h 中 HSE_VALUE=8000000U。

HAL_InitTick 根据 SystemCoreClock 配置 SysTick。HAL_Delay 依赖 SysTick_Handler 调用 HAL_IncTick，使 uwTick 不断增加。若仿真模型运行频率与软件认为的频率相差很大，启动和延时可能极慢，表现为没有变化。不能仅凭截图断定已经进入 Error_Handler；那需要查看 PC 或断点。

SystemClock_Config 在 MX_GPIO_Init 之前执行。若 HAL_RCC_OscConfig 或 HAL_RCC_ClockConfig 返回失败，代码会调用 Error_Handler，关闭中断并永久循环，根本不会运行四灯控制。HAL_RCC_OscConfig 还有等待 HSERDY、PLLRDY 的过程，也应在动态调试时检查。

### 10kΩ 对 LED 串联限流过大

自动保存电路的 LED 模型参数为 VF=2.2V、IMAX=10mA。用模型标称 VF 做近似估算，假设电源为 3.3V、引脚低电平接近 0V：

`I ≈ (3.3V - 2.2V) / 10000Ω = 0.11mA`

换为 330Ω 后，估算约为 3.3mA。实际电流由模型的伏安曲线和 GPIO 输出电压决定，这不是实测值。真实蓝色 LED 的正向压降还可能高于这里的模型参数。

## 如果改完仍没有变化：按这个流程定位

1. 在 PA1～PA4 放逻辑分析仪或电压探针，观察至少 2 秒仿真时间。若四路按顺序出现约 0.5 秒低电平，程序已运行，问题在 LED、电阻、电源或连接。
2. 若引脚没有切换，用 U1 的 Program File 加载同目录下的 P1_CreateProject.axf，以便查看源代码和符号。在 main.c 的 MX_GPIO_Init 调用处、while 循环第一条写引脚处设断点。若到不了 GPIO 初始化，先查时钟配置和复位。
3. 若停在初始化，检查 HAL_RCC_OscConfig 的返回值、RCC->CR 的 HSERDY/PLLRDY，以及是否进入 Error_Handler、HardFault_Handler。注意优化可能把 Error_Handler 内联到调用处，不能只凭链接表里没有独立符号就认为错误处理不存在。
4. 若停在第一次 HAL_Delay，观察 uwTick 是否增长、SysTick 是否触发、是否关闭了中断。当前源码中 SysTick_Handler 已包含 HAL_IncTick，没有发现漏调用的问题。
5. 核对 NRST 为高电平、复位按钮松开；BOOT0 接地可以明确选择从 Flash 启动，不宜悬空。截图中 BOOT0 悬空是需规范处理的接线，不是本次已验证的唯一根因。

另有一个独立错误：自动保存工程的 X2 标签写着 32.768KHz，但真实 FREQ 属性为 `32.768MHz`。应改真实属性为 `32.768kHz`。本次 main.c 只请求 HSE，未启用 LSE，因此不能把 X2 作为当前流水灯不运行的直接原因。

## 阅读文件及其用途

- 用户上传的已粘贴的文本.txt：核对所提供 main.c 的四个点灯阶段、500ms 延时和时钟初始化。
- P1_CreateProject/Core/Src/main.c，第 74、81、88 行：核对 HAL、时钟、GPIO 的初始化顺序；第 94～117 行：核对有效的流水灯代码；第 153～185 行：核对 HSE + PLL ×9 和错误分支；第 196～204 行：核对错误处理永久循环。
- P1_CreateProject/Core/Src/gpio.c，第 50～60 行：核对 GPIOA 时钟已开启、初始输出高、推挽输出、无上下拉。
- P1_CreateProject/Core/Inc/main.h，第 60～67 行：核对 LED1～LED4 分别映射到 PA1～PA4。
- P1_CreateProject/Core/Src/stm32f1xx_it.c，第 183～188 行：核对 SysTick_Handler 调用 HAL_IncTick。
- P1_CreateProject/Core/Inc/stm32f1xx_hal_conf.h，第 86～88 行：核对 HSE_VALUE 为 8MHz。
- P1_CreateProject/P1_CreateProject.ioc，第 43～62 行附近的 PA 配置及第 116～136 行 RCC 配置：核对 CubeMX 的引脚和 72MHz 时钟设置。以实际键名为准。
- P1_CreateProject/Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal.c，第 234 行附近 HAL_InitTick 与第 371 行附近 HAL_Delay：追踪软件频率、SysTick、uwTick 与延时的关系。
- P1_CreateProject/Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_rcc.c，第 345 行起 HAL_RCC_OscConfig：核对 HSERDY/PLLRDY 等待与超时返回机制。
- P1_CreateProject/MDK-ARM/P1_CreateProject.uvprojx，第 50～54 行：核对输出目录、输出名和 CreateHexFile=1。
- 同目录产物子目录的 P1_CreateProject.build_log.htm：已有编译记录为 0 错误、0 警告；P1_CreateProject.map：核对 main、GPIO、SysTick、HAL_Delay 已链接；P1_CreateProject.axf：反汇编核对实际主循环；P1_CreateProject.hex：核对 Intel HEX 校验和、Flash 地址、复位向量和 SysTick 向量。
- 1.0create_projectt.pdsprj 和 Project Backups 中三个版本：以 ZIP 读取 ROOT.CDB、ROOT.DSN、PWRRAILS.DAT，核对程序路径、OSC、Clock Scale、晶振真实属性及 LED、电阻属性。根目录主工程是旧电路，Autosaved 版本有四个蓝灯。
- D:/Proteus/Help/CM3.chm：本机 Proteus 官方帮助，已提取为 diagnostics/cm3_help/Properties.htm。其中 Crystal Frequency 段解释处理器主频强制设置，Clock Scale 段解释仿真优化。其余型号的寄存器限制不能直接套用于 STM32。
- D:/Proteus/SysModels/CM3_STM32.LML 和 cm3_stm32.dll：只读检查模型参数 OSC/CLOCK_SCALE 的连接，以及模型内关于 Forced clock 的诊断文本，辅助确认强制频率语义。
- 根目录 Proteus按键按下LED不变化_根因与修复.md：仅用于核对旧问题背景。旧文档描述的空循环、空 GPIO 初始化已不符合当前代码；本次未沿用它们作为结论。

## 使用的方法与命令

方法：截图与保存参数交叉核对、源码调用链追踪、ZIP 内嵌参数提取、固件反汇编、Intel HEX 校验、电流近似计算。未改写 main.c，也未重新编译或改写原 Proteus 工程。

实际使用的主要命令如下（PowerShell 环境）：

```powershell
rg --files -g AGENTS.md -g '*main.c' -g '*.ioc' -g '*.hex' -g '*.uvprojx' -g '*.pdsprj' -g '*.map'
Get-Content -LiteralPath 'P1_CreateProject\Core\Src\main.c'
Get-Content -LiteralPath 'P1_CreateProject\Core\Src\gpio.c'
rg -n 'SysTick_Handler|HAL_IncTick' P1_CreateProject\Core\Src\stm32f1xx_it.c
rg -n 'HSE_VALUE|CreateHexFile|OutputName|OutputDirectory' P1_CreateProject\Core\Inc\stm32f1xx_hal_conf.h P1_CreateProject\MDK-ARM\P1_CreateProject.uvprojx
& 'D:\Stu15\stm32cubeCLT\STM32CubeCLT_1.21.0\GNU-tools-for-STM32\bin\arm-none-eabi-objdump.exe' -d --disassemble=main 'P1_CreateProject\MDK-ARM\P1_CreateProject\P1_CreateProject.axf'
& 'D:\Stu15\stm32cubeCLT\STM32CubeCLT_1.21.0\GNU-tools-for-STM32\bin\arm-none-eabi-objdump.exe' -d --disassemble=SystemClock_Config 'P1_CreateProject\MDK-ARM\P1_CreateProject\P1_CreateProject.axf'
& 'C:\Windows\hh.exe' -decompile D:\Proteus\project\diagnostics\cm3_help D:\Proteus\Help\CM3.chm
```

其他只读脚本通过 PowerShell 的 here-string 传入 `python -`：使用 Python 标准库 zipfile 读取 pdsprj，re 提取二进制中的可打印参数；按 Intel HEX 记录校验和为零的规则检查文件，并读取复位和 SysTick 向量。HEX 校验全部通过，有效数据 3244 字节，最低地址 0x08000000，复位入口 0x08000189，SysTick 入口 0x08000B01。AXF 反汇编证明存在 16 次写引脚调用和四次 500ms 延时。最终使用 struct 解析 AXF 的 ELF 加载段，与 HEX 的 Flash 加载内容逐字节比对，3244 字节全部一致，排除了所检查的 AXF 与 HEX 不对应的问题。

初始沙箱命令进程初始化失败，后续只读检查与项目内帮助提取改用授权执行。首次帮助提取、默认 Python 输出编码读取帮助失败后，改用直接 hh.exe 命令及 UTF-8 输出完成读取。

参考核对：[ST 官方 STM32F103x8/xB 数据手册](https://www.st.com/resource/en/datasheet/stm32f103c8.pdf)。Proteus 频率属性的具体解释来自上面本机官方帮助，不依赖网络转载教程。
