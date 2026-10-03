# Proteus 仿真：按键按下 LED 颜色不变（红→蓝）——根因与修复

## 1. 现象

- 在 Proteus 里点击“开始仿真”后，按下按键，左侧 LED 没有从红色变为蓝色。
- MCU 为 STM32F103C8，工程是 STM32CubeMX + Keil MDK-ARM。

## 2. 根因（不是 Proteus 软件坏了，而是工程和代码都没准备好）

### 2.1 固件主循环是空的

文件：`D:\Proteus\project\P1_CreateProject\Core\Src\main.c`

```c
while (1)
{
  /* USER CODE END WHILE */

  /* USER CODE BEGIN 3 */
}
```

**问题**：这里没有任何读取按键、切换 LED 的代码，MCU 上电后就在空转。

### 2.2 GPIO 初始化也是空的

文件：`D:\Proteus\project\P1_CreateProject\Core\Src\gpio.c`

```c
void MX_GPIO_Init(void)
{
  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOD_CLK_ENABLE();
}
```

**问题**：只打开了 GPIOD 的时钟，没有配置任何引脚为输入/输出，也没有配置上拉/下拉。

### 2.3 CubeMX 里没有给按键和 LED 分配 GPIO 引脚

文件：`D:\Proteus\project\P1_CreateProject\P1_CreateProject.ioc`

当前只配置了：

- `PD0-OSC_IN` / `PD1-OSC_OUT`：8MHz 外部晶振（HSE）
- `PC14-OSC32_IN` / `PC15-OSC32_OUT`：32.768kHz 低速晶振（LSE）

**没有任何 PA/PB/PC 引脚被设置为 GPIO_Input（按键）或 GPIO_Output（LED）。**

### 2.4 按键接到了 NRST（复位）引脚

从录屏截图里可以看到：按键一端接在 STM32 的 `NRST`（第 7 脚），另一端接地。

**问题**：NRST 是复位引脚，不是用来读取按键状态的 GPIO。按下它会让单片机复位重启，而不是给程序发送一个“按键被按下”的信号。

### 2.5 当前 LED 不是红/蓝双色 LED

截图中只有一个 `D1 LED-GREEN`，当前显示为绿色。如果你期望的是“红变蓝”的效果，可能：

- 你放的是双色 LED / RGB LED，但截图里只截到了绿色部分；
- 或者你指的是 Proteus 里的逻辑探针（红/蓝小方块），而不是实际 LED 元件。

## 3. 为什么之前会“卡住”

你目前做的只是“新建 CubeMX 工程并生成代码”，还没有进入真正的应用逻辑。
CubeMX 只会生成你勾选了的外设和引脚的初始化代码；
如果你没配置按键和 LED 引脚、没写主循环逻辑，单片机就什么都不会做，仿真自然没反应。

## 4. 修复步骤

### 步骤 1：在 CubeMX 里配置引脚

打开 `P1_CreateProject.ioc`：

- 选一个 GPIO 作为**按键输入**，例如 `PA0`：
  - 模式设为 `GPIO_Input`
  - 配置为 `Pull-Up`（上拉）
- 选一个 GPIO 作为**LED 输出**，例如 `PA1`：
  - 模式设为 `GPIO_Output`
  - 输出电平初始值根据电路决定（共阳 LED 初始 High=灭，共阴 LED 初始 Low=灭）

> 注意：你现在电路里的 LED 阳极通过 R3 接 VCC，所以是**共阳接法**。要点亮它，MCU 引脚需要输出 **Low**。

### 步骤 2：重新生成代码

点击 CubeMX 的 **GENERATE CODE**。这样 `gpio.c` 里会自动出现 PA0、PA1 的初始化代码。

### 步骤 3：修改主循环，实现按键控制 LED

在 `main.c` 的 `while(1)` 里添加：

```c
while (1)
{
  /* 读取 PA0 按键状态 */
  if (HAL_GPIO_ReadPin(KEY_GPIO_Port, KEY_Pin) == GPIO_PIN_RESET)
  {
    HAL_Delay(20);                      /* 简单消抖 */
    if (HAL_GPIO_ReadPin(KEY_GPIO_Port, KEY_Pin) == GPIO_PIN_RESET)
    {
      HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);  /* 翻转 LED */
      while (HAL_GPIO_ReadPin(KEY_GPIO_Port, KEY_Pin) == GPIO_PIN_RESET); /* 等待松手 */
      HAL_Delay(20);
    }
  }
}
```

如果你不习惯用 `KEY_GPIO_Port` 这种宏，也可以直接用：

```c
if (HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_0) == GPIO_PIN_RESET) { ... }
HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_1);
```

### 步骤 4：修改 Proteus 原理图

1. **把按键从 NRST 移到 PA0**：一端接 PA0，另一端接 GND（因为你配置了内部上拉）。
2. **把 LED 阴极接到 PA1**，阳极仍然通过 R3 接 VCC。

### 步骤 5：编译并更新 .hex

1. 在 Keil 里点击 **Rebuild**。
2. 生成的 `.hex` 通常位于：
   `D:\Proteus\project\P1_CreateProject\MDK-ARM\P1_CreateProject\P1_CreateProject.hex`
3. 在 Proteus 里双击 MCU，把 **Program File** 重新指向新的 `.hex`。
4. 运行仿真。

## 5. 涉及的知识点

- **CubeMX 代码生成**：只有配置了引脚/外设，生成代码里才会出现对应初始化。
- **GPIO 模式**：输入要配 `Input + Pull-Up/Pull-Down`，输出要配 `Output Push-Pull`。
- **HAL 库函数**：
  - `HAL_GPIO_ReadPin()`：读取引脚电平
  - `HAL_GPIO_WritePin()`：写引脚电平
  - `HAL_GPIO_TogglePin()`：翻转引脚电平
- **按键消抖**：机械按键按下/松开时有抖动，需要加 `HAL_Delay()` 或状态机消抖。
- **NRST 是复位引脚**：不能当普通 GPIO 用。
- **共阳/共阴 LED**：阳极接 VCC 的 LED，MCU 输出低电平时点亮；阳极接 MCU、阴极接 GND 的 LED，MCU 输出高电平时点亮。

## 6. 如果你想让我帮你改

我可以直接帮你：

1. 修改 `P1_CreateProject.ioc`（选 PA0/PA1 等）。
2. 修改 `gpio.c` / `main.c`，加上按键读取和 LED 翻转代码。
3. 给出 Proteus 原理图需要改动的具体说明。

你只需要确认：

- 按键想接哪个引脚？（建议 PA0）
- LED 想接哪个引脚？（建议 PA1）
- 你期望的 LED 到底是红/蓝双色 LED，还是截图里的 LED-GREEN？
