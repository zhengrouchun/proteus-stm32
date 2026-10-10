/* 解决 Proteus 中 STM32F103C8 缺少程序文件的问题：读取 VA、VB 并通过串口报告。 */
#include "main.h"                 /* 引入 STM32 HAL 类型和函数声明。 */
#include <stdio.h>                 /* 引入 snprintf 格式化函数。 */
#include <string.h>                /* 引入 strlen 字符串长度函数。 */

#define ADC_REFERENCE_MILLIVOLTS 3300  /* 将 VDDA=3.3 V 表示为 3300 mV。 */
#define ADC_MAXIMUM_CODE 4095          /* 12 位 ADC 的最大读数。 */
#define ADC_TIMEOUT_MILLISECONDS 20   /* 最多等待一次 ADC 转换 20 ms。 */
#define UART_TIMEOUT_MILLISECONDS 100 /* 最多等待串口发送 100 ms。 */
#define REPORT_PERIOD_MILLISECONDS 500/* 每隔 500 ms 报告一次。 */

static ADC_HandleTypeDef adc1;   /* 保存 ADC1 的配置和运行状态。 */
static UART_HandleTypeDef uart1; /* 保存 USART1 的配置和运行状态。 */

static void ConfigureSystemClock(void);                  /* 声明时钟配置函数。 */
static void ConfigureAdc(void);                          /* 声明 ADC 初始化函数。 */
static void ConfigureUart(void);                         /* 声明串口初始化函数。 */
static uint32_t ReadAdcChannel(uint32_t channel);        /* 声明单通道采样函数。 */
static void SendReport(uint32_t va_raw, uint32_t vb_raw);/* 声明串口报告函数。 */

int main(void)
{
    HAL_Init();                              /* 复位 HAL 状态并启用 1 ms SysTick。 */
    ConfigureSystemClock();                  /* 使用内部 HSI 8 MHz，无需外接晶振。 */
    ConfigureAdc();                          /* 初始化 ADC1 与模拟输入。 */
    ConfigureUart();                         /* 初始化 PA9 串口输出。 */
    if (HAL_ADCEx_Calibration_Start(&adc1) != HAL_OK) /* 校准 ADC1，若失败则停止。 */
    {
        Error_Handler();                     /* 避免用未校准 ADC 值误判。 */
    }
    while (1)                                /* 持续采样与报告。 */
    {
        uint32_t vb_raw = ReadAdcChannel(ADC_CHANNEL_0); /* PA0 接 DIV_VB。 */
        uint32_t va_raw = ReadAdcChannel(ADC_CHANNEL_1); /* PA1 接 DIV_VA。 */
        SendReport(va_raw, vb_raw);          /* 串口报告原始码值和毫伏数。 */
        HAL_Delay(REPORT_PERIOD_MILLISECONDS); /* 两次报告间隔 500 ms。 */
    }
}

static void ConfigureSystemClock(void)
{
    RCC_OscInitTypeDef oscillator = {0};     /* 为振荡器配置结构清零。 */
    RCC_ClkInitTypeDef clocks = {0};         /* 为总线时钟配置结构清零。 */
    oscillator.OscillatorType = RCC_OSCILLATORTYPE_HSI; /* 只使用片内 HSI。 */
    oscillator.HSIState = RCC_HSI_ON;        /* 打开 HSI 8 MHz 振荡器。 */
    oscillator.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT; /* 保留出厂校准。 */
    oscillator.PLL.PLLState = RCC_PLL_OFF;    /* 不启用 PLL，简化 Proteus 时钟。 */
    if (HAL_RCC_OscConfig(&oscillator) != HAL_OK) /* 应用振荡器设置。 */
    {
        Error_Handler();                     /* 时钟配置失败时停止。 */
    }
    clocks.ClockType = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK |
                       RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2; /* 配置四类时钟。 */
    clocks.SYSCLKSource = RCC_SYSCLKSOURCE_HSI; /* 系统时钟来自 HSI。 */
    clocks.AHBCLKDivider = RCC_SYSCLK_DIV1; /* HCLK 保持 8 MHz。 */
    clocks.APB1CLKDivider = RCC_HCLK_DIV1;  /* APB1 保持 8 MHz。 */
    clocks.APB2CLKDivider = RCC_HCLK_DIV1;  /* APB2 保持 8 MHz。 */
    if (HAL_RCC_ClockConfig(&clocks, FLASH_LATENCY_0) != HAL_OK) /* 应用分频设置。 */
    {
        Error_Handler();                     /* 总线时钟配置失败时停止。 */
    }
    __HAL_RCC_ADC_CONFIG(RCC_ADCPCLK2_DIV2); /* ADC 时钟为 4 MHz。 */
}

static void ConfigureAdc(void)
{
    GPIO_InitTypeDef pins = {0};              /* 为引脚配置结构清零。 */
    __HAL_RCC_GPIOA_CLK_ENABLE();            /* 允许配置 GPIOA。 */
    __HAL_RCC_ADC1_CLK_ENABLE();             /* 允许使用 ADC1。 */
    pins.Pin = GPIO_PIN_0 | GPIO_PIN_1;      /* 同时选择 PA0、PA1。 */
    pins.Mode = GPIO_MODE_ANALOG;            /* ADC 引脚必须设为模拟输入。 */
    HAL_GPIO_Init(GPIOA, &pins);             /* 应用 PA0/PA1 模拟模式。 */
    adc1.Instance = ADC1;                    /* 使用第 1 个 ADC 外设。 */
    adc1.Init.ScanConvMode = ADC_SCAN_DISABLE; /* 每次只转换一个通道。 */
    adc1.Init.ContinuousConvMode = DISABLE;  /* 每次读取由程序显式启动。 */
    adc1.Init.DiscontinuousConvMode = DISABLE; /* 不使用间断扫描。 */
    adc1.Init.ExternalTrigConv = ADC_SOFTWARE_START; /* 由程序软件触发。 */
    adc1.Init.DataAlign = ADC_DATAALIGN_RIGHT; /* 原始结果右对齐。 */
    adc1.Init.NbrOfConversion = 1;           /* 常规组只配置一项转换。 */
    if (HAL_ADC_Init(&adc1) != HAL_OK)        /* 将配置写入 ADC1。 */
    {
        Error_Handler();                     /* ADC 初始化失败时停止。 */
    }
}

static void ConfigureUart(void)
{
    GPIO_InitTypeDef tx_pin = {0};            /* 为 TX 引脚配置结构清零。 */
    __HAL_RCC_GPIOA_CLK_ENABLE();            /* 允许配置 GPIOA。 */
    __HAL_RCC_USART1_CLK_ENABLE();           /* 允许使用 USART1。 */
    tx_pin.Pin = GPIO_PIN_9;                  /* PA9 是 USART1_TX。 */
    tx_pin.Mode = GPIO_MODE_AF_PP;            /* 使用复用推挽输出。 */
    tx_pin.Speed = GPIO_SPEED_FREQ_HIGH;     /* 使用足够的输出速度。 */
    HAL_GPIO_Init(GPIOA, &tx_pin);           /* 应用 PA9 设置。 */
    uart1.Instance = USART1;                 /* 使用第 1 个串口外设。 */
    uart1.Init.BaudRate = 9600;              /* 和 Proteus 终端统一 9600 波特。 */
    uart1.Init.WordLength = UART_WORDLENGTH_8B; /* 每个数据字节 8 位。 */
    uart1.Init.StopBits = UART_STOPBITS_1;   /* 每帧 1 个停止位。 */
    uart1.Init.Parity = UART_PARITY_NONE;    /* 不使用校验位。 */
    uart1.Init.Mode = UART_MODE_TX;          /* 当前只需要单片机发送。 */
    uart1.Init.HwFlowCtl = UART_HWCONTROL_NONE; /* 不使用 RTS/CTS。 */
    uart1.Init.OverSampling = UART_OVERSAMPLING_16; /* 标准 16 倍过采样。 */
    if (HAL_UART_Init(&uart1) != HAL_OK)      /* 将配置写入 USART1。 */
    {
        Error_Handler();                     /* 串口初始化失败时停止。 */
    }
}

static uint32_t ReadAdcChannel(uint32_t channel)
{
    ADC_ChannelConfTypeDef selected = {0};   /* 为通道配置结构清零。 */
    selected.Channel = channel;              /* 选择传入的 PA0 或 PA1 通道。 */
    selected.Rank = ADC_REGULAR_RANK_1;      /* 将它放在常规组第 1 位。 */
    selected.SamplingTime = ADC_SAMPLETIME_239CYCLES_5; /* 高阻节点多留采样时间。 */
    if (HAL_ADC_ConfigChannel(&adc1, &selected) != HAL_OK) /* 切换 ADC 输入。 */
    {
        Error_Handler();                     /* 通道配置失败时停止。 */
    }
    if (HAL_ADC_Start(&adc1) != HAL_OK)      /* 开始一次软件触发转换。 */
    {
        Error_Handler();                     /* ADC 无法启动时停止。 */
    }
    if (HAL_ADC_PollForConversion(&adc1, ADC_TIMEOUT_MILLISECONDS) != HAL_OK) /* 等待结果。 */
    {
        Error_Handler();                     /* 超时或转换失败时停止。 */
    }
    uint32_t sample = HAL_ADC_GetValue(&adc1); /* 取得 12 位原始码值。 */
    if (HAL_ADC_Stop(&adc1) != HAL_OK)       /* 结束本次转换。 */
    {
        Error_Handler();                     /* 停止失败时停止。 */
    }
    return sample;                           /* 将采样结果交给主循环。 */
}

static void SendReport(uint32_t va_raw, uint32_t vb_raw)
{
    char line[96];                           /* 为一行串口报告准备缓冲区。 */
    uint32_t va_mv = va_raw * ADC_REFERENCE_MILLIVOLTS / ADC_MAXIMUM_CODE; /* VA 转毫伏。 */
    uint32_t vb_mv = vb_raw * ADC_REFERENCE_MILLIVOLTS / ADC_MAXIMUM_CODE; /* VB 转毫伏。 */
    int written = snprintf(line, sizeof(line), "VA=%lu mV (%lu)  VB=%lu mV (%lu)\r\n",
                           (unsigned long)va_mv, (unsigned long)va_raw,
                           (unsigned long)vb_mv, (unsigned long)vb_raw); /* 拼接人可读报告。 */
    if (written < 0 || written >= (int)sizeof(line)) /* 防止格式化失败或截断。 */
    {
        Error_Handler();                     /* 避免发送错误内容。 */
    }
    if (HAL_UART_Transmit(&uart1, (uint8_t *)line, (uint16_t)strlen(line),
                          UART_TIMEOUT_MILLISECONDS) != HAL_OK) /* 发往虚拟终端。 */
    {
        Error_Handler();                     /* 串口发送失败时停止。 */
    }
}

void SysTick_Handler(void)
{
    HAL_IncTick();                            /* 维持 HAL_Delay 和超时计数。 */
}

void Error_Handler(void)
{
    __disable_irq();                          /* 停止中断，保留故障现场。 */
    while (1)                                 /* 明确停在错误处理处。 */
    {
    }
}
