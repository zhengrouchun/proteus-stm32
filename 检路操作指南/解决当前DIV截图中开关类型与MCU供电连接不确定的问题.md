# 解决当前DIV截图中开关类型与MCU供电连接不确定的问题

**启动前提修正：**日志已确认U1没有指定程序文件，整个仿真无法启动。无固件首轮测试必须先另存工程副本，并从测试副本删除U1；仅断开U1导线无效。保留U1的完整工程必须指定有效固件。处理见[解决缺程序文件导致仿真无法启动的问题](D:/Proteus/project/检路操作指南/解决未指定程序文件导致DIV仿真无法启动的问题.md)。


本次根据你发的三张Proteus 9截图逐点核对。**没有直接打开或修改你的 `.pdsprj` 工程，截图不能证明未显示的端子属性或隐藏引脚网络。**因此下列意见区分“截图能确认”和“需要在Proteus中检查”。

## 截图能确认的部分

- DIV测试拓扑基本正确：`BAT1(1V) → RS(2kΩ) → VA → SW1 → R1(10kΩ) → VB → R2(10kΩ) → GND`。R2旁边的开关跨接VB到GND，位置正确。两只电压表分别测VA对地、VB对地，接线方向正确。
- `DIV_VA`和`DIV_VB`在被测节点与U1的PA1/PA0旁各出现一次，拼写一致。你使用的是Proteus带名称的**网络端子**；如果端子确实落在引脚/导线上，同名端子相当于一根隐藏导线。你问的空心三角形是我绘制示意图时画的同类“网络出口”符号，不是必须搜索的实体元件；你图中的圆形端子可以继续使用。
- `BOOT0`第44脚经过`R4(10kΩ)`到右侧的接地符号，作为下拉的接法正确，前提是右端确实是Proteus的GND端子。
- `NRST`第7脚连到R3与按钮的交点，R3在上、按钮通向地，这个**拓扑**正确；但按钮器件类型选错，见下节。

## 必须先改的地方

1. **两个开关型号互换用途。**`SW1`是`SW-SPST`，用作R1断路，正确。你现在的`SW2`是`SW-SPST-MOM`瞬时按钮，放在R2两端，按住才短路，不适合稳定的R2短路工况。你现在的`SW3`是`SW-SPST`保持型开关，放在NRST上，一旦闭合会一直把复位脚拉低，MCU持续复位。把R2跨接位置换成一只`SW-SPST`；把NRST接地位置换成一只`SW-SPST-MOM`。自动位号可以变化，功能位置比`SW2/SW3`数字更重要。
2. **把BAT2负极明确接到GND。**截图在BAT2负极下方只看到线端/光标，没有清楚可辨的GND符号。不要假设它已经接地；从BAT2负极拉导线到左侧DIV电路已有的GND网络，或在负极放真正的`GROUND`端子。两只电源共地，但1V正极与3.3V正极不能相连。
3. **把3.3V网络名明确为`VDD`并逐项核对。**BAT2正极和R3顶端是向上的电源端子，但截图没有显示端子名称；VDDA和VBAT旁是向右的空心端子，也没有显示名称。仅靠图形形状不能确认这几处属于同一网络。最直接做法是用导线把BAT2正极分别接到R3顶端、U1第9脚VDDA和第1脚VBAT，并在这根3.3V线上放一个**名称明确为`VDD`**的电源端子，供U1隐藏的VDD脚使用；U1第8脚VSSA接公共GND。右击U1查看`Edit Properties → Hidden Pins`，并用`Design → Power Rail Configuration`核对VDD为3.3V、GND为0V。Proteus官方手册说明隐藏电源脚按脚名归网，**未命名的电源端子默认属于VCC网络**，因此“两个箭头长得一样”不足以证明VDD已接到BAT2。若第9脚与第1脚暂时使用端子而非直接导线，请双击端子，确保二者与BAT2所接网络**同名**。
4. **补C1去耦。**你已经有`CAP C1=100nF`，第一阶段仅用电压表检查DIV时它可以暂放图边；接入U1并运行固件前，把C1并联在BAT2正极3.3V和GND之间。若后续做实物，数字和模拟电源附近应按芯片资料安排更多去耦；单只C1是仿真首轮最小画法。`CAP-ELEC C2=10µF`属于下一阶段RC，**不能**拿它替代3.3V旁的100nF去耦，也不应在DIV的VB上随意并接，否则改变被测模型。
5. **正常工况先闭合SW1。**当前截图SW1图形呈断开状态，所以按运行钮后首先得到的是R1断路，不是正常。R2旁的跨接开关正常时保持断开。

图三中暂不用的OLED、EEPROM和矩阵显示器有的压在蓝色纸张边框上或边框外。这通常不改变已连DIV网络的电气结果，但导出/打印图纸可能看不全；完成核心验证后再把需要的器件移到边框内，未用器件从最终提交图中清理。

建议把三个关键连接改完后先在另存且删除U1的纯模拟测试副本中运行电压表：正常VA约0.909V、VB约0.455V；R1断路VA约1V、VB约0V；R2短路VA约0.833V、VB约0V。截图中的电压表显示`+88.8`只是尚未得到有效读数的画面，**不能据此判断电路已通过仿真**。

## 图一空心三角形与现在的圆形端子

我画的空心三角形`DIV_VA`是**网络标记示意**，不是电阻、电容或必须买/搜索的元件。你现在实际使用的带名字圆形端子也可以实现同名虚拟连线：分压VA旁和PA1旁同名`DIV_VA`，分压VB旁和PA0旁同名`DIV_VB`。Proteus官方教程明确同名端子视作相连。你可以双击每个端子复查`Terminal Label`，并确认端子尖端确实碰到绿色导线/芯片引脚。若要用左侧`LBL`工具给导线标网络名，则必须点在绿色导线上，不能只在空白处放文字。

## CubeMX、编译、HEX、Proteus之间的关系

**只量DIV电压表且测试副本中已删除U1时，不需要CubeMX或HEX；保留U1则必须指定有效程序文件。**要让U1用ADC读取并在虚拟终端/OLED输出，才需要固件。如果采用C语言固件路线，顺序是：独立的STM32CubeMX配置芯片/时钟/ADC并生成工程 → STM32CubeIDE写应用代码和编译 → 导出`.hex`（或可调试的`.elf`）→ 双击Proteus U1，给`Program File`选择编译输出、`Clock Frequency`设为与固件一致的8MHz → 仿真检查PA0/PA1的真实ADC码和输出。CubeMX只生成初始化和工程框架，不会自动写出R1断路/R2短路判别程序。Labcenter明确支持把编译后的HEX设为MCU程序文件。

这台电脑在注册表中查到`STM32CubeMX 6.0.1`、`STM32CubeIDE 2.1.1`、`Proteus 9.0.40482.2`。STM32CubeIDE 2.x已把CubeMX变为独立工具，所以不要按旧教程在IDE内找集成的CubeMX界面。若选择C路线，先用独立CubeMX生成针对`STM32F103C8Tx`、工具链`STM32CubeIDE`的工程；HSI开、HSE关、PLL关、SYSCLK 8MHz，ADC1先开PA0/IN0与PA1/IN1，ADC时钟4MHz、采样时间先用239.5周期。编译生成ELF后，在IDE的`Project Properties → C/C++ Build → Settings → MCU Post build outputs`勾选`Convert to Intel Hex file`再构建，可在工程`Debug`或`Release`目录查找HEX。具体菜单以本机版本实际界面为准。CubeMX 6.0.1比IDE 2.1.1旧；若F1固件包下载、生成或导入时报兼容问题，再升级独立CubeMX，不必为了第一轮电压表验证先改软件。

**规则约束另算。**你此前给的A任务说明提到流程图/可视化外设模块编程。CubeMX+CubeIDE编译HEX是技术上可仿真的C语言路线；如果正式提交必须是Proteus Visual Designer流程图，它不能自动等同于合规提交。首轮电路和ADC验证可用这一路线，但最终交付形式应按正式比赛规则执行。

## 本次看了什么、怎么核查

查看你本次三张截图中SW1/SW2/SW3的器件文字、VA/VB节点和U1引脚号、BAT2/R3电源端子的图形；对照本地已整理的[Proteus9元件与时钟说明](D:/Proteus/project/检路操作指南/解决Proteus9找不到元件及STM32F103C8接线时钟配置的问题.md)，使用PowerShell只读查询已安装软件版本。又核对[Labcenter官方教程](https://www.labcenter.com/downloads/Tutorials.pdf)的同名端子、隐藏供电脚和默认VCC规则，[Labcenter编译器说明](https://www.labcenter.com/compilers/)的Program File与时钟属性，以及[ST官方说明](https://community.st.com/stm32-software-tools-165/what-s-new-in-stm32cubeide-2-0-0-159478?fid=None&tid=159478)的CubeIDE 2.x/CubeMX分离和[STM32CubeIDE用户手册](https://www.st.com/content/ccc/resource/technical/document/user_manual/group1/f8/a2/48/77/68/e6/4b/74/DM00629856/files/DM00629856.pdf/jcr%3Acontent/translations/en.DM00629856.pdf)的HEX输出设置。上述查阅解决的是“同形电源箭头是否同网、按钮和保持开关是否用反、固件如何进入Proteus”的问题；BAT2及右侧端子的实际网络名仍需在你的工程属性中确认。
