"""在已经完整备份的原 CubeMX 工程里更新 USER CODE；每一步均保留原始生成结构。"""
from pathlib import Path  # 用明确路径定位用户指定工程。
import re  # 仅替换有起止标记的 USER CODE 区域。

workspace = Path(__file__).resolve().parents[2]  # 脚本位于交付目录下的工具子目录。
project = workspace / "fix_missing_cubemx_adc_hex" / "ADC_CubeMX_Keil"  # 最终代码写到用户指定目录。
main_path = project / "Src" / "main.c"  # 定位 CubeMX 原入口文件。
text = main_path.read_text(encoding="utf-8-sig")  # 保留原始代码内容作为修改基础。

def replace_region(label, content):  # 只替换一个明确命名的用户代码区。
    global text  # 更新当前正在编辑的主文件文本。
    pattern = r"(/\* USER CODE BEGIN " + re.escape(label) + r" \*/).*?(/\* USER CODE END " + re.escape(label) + r" \*/)"  # 使用原有标记作为边界。
    text, count = re.subn(pattern, lambda m: m[1] + "\n" + content.strip() + "\n\n" + m[2], text, flags=re.S)  # 保留 BEGIN 和 END 行。
    assert count == 1, f"用户代码区不唯一或缺失：{label}"  # 避免误改不符合预期的文件。

replace_region("Includes", '''
#include <stdio.h> /* 将真实读数格式化为串口文本。 */
#include "div_diagnosis.h" /* 引入参数 2.0 的电压换算和九工况判别。 */
''')  # 保留 CubeMX 自带 main.h，在用户区增加依赖。
replace_region("PD", '''
#define ADC_TIMEOUT_MILLISECONDS 20 /* 最多等待一次 ADC 转换 20 ms。 */
#define UART_TIMEOUT_MILLISECONDS 100 /* 一条报告最多发送 100 ms。 */
#define REPORT_PERIOD_MILLISECONDS 500 /* 报告之间等待 500 ms，不计入检测耗时。 */
#define REPORT_BUFFER_SIZE 384 /* 容纳整条带状态和错误信息的报告。 */
''')  # 所有应用参数采用说明用途的名称。
replace_region("PTD", '''
typedef struct /* 保存一次检测结果，初始化时所有有效标志为假。 */
{
    uint32_t vb_raw; /* VB 的真实 ADC 原码，仅在 vb_valid 为真时可用。 */
    uint32_t va_raw; /* VA 的真实 ADC 原码，仅在 va_valid 为真时可用。 */
    uint32_t vb_mv; /* VB 四舍五入后的 mV 值。 */
    uint32_t va_mv; /* VA 四舍五入后的 mV 值。 */
    uint32_t adc_conversions; /* 每次 Poll 成功并 GetValue 后递增。 */
    uint32_t feature_reads; /* 实际获得有效读数的不同节点数。 */
    uint32_t elapsed_ms; /* 从本次开始采样到判别结束的 HAL 毫秒节拍差。 */
    int vb_valid; /* VB 已有效采样时为真，未读时输出 NA。 */
    int va_valid; /* VA 已有效采样时为真，未读时输出 NA。 */
    int state; /* 唯一工况编号，或 DIV_UNKNOWN。 */
    const char *error; /* OK 或明确的 ADC 错误阶段。 */
} DivMeasurement; /* 为本次采集记录定义类型名。 */
''')  # 将计数和有效性放在同一记录中，避免跨轮使用旧数值。
replace_region("PFP", '''
static const char *ReadAdcChannel(uint32_t channel, uint32_t *raw, uint32_t *conversions); /* 声明真实采样函数。 */
static void SendReport(const DivMeasurement *result); /* 声明报告函数。 */
static void RunDivDetection(void); /* 声明一次完整检测。 */
''')  # 扩展原采样和报告声明。
replace_region("0", '''
static const char *ReadAdcChannel(uint32_t channel, uint32_t *raw, uint32_t *conversions) /* 失败返回阶段名，成功返回 OK。 */
{
    ADC_ChannelConfTypeDef selected = {0}; /* 全部配置字段清零，随后明确设置所需字段。 */
    selected.Channel = channel; /* 选择 PA0 的通道 0 或 PA1 的通道 1。 */
    selected.Rank = ADC_REGULAR_RANK_1; /* 单次转换只使用序列第一个位置。 */
    selected.SamplingTime = ADC_SAMPLETIME_239CYCLES_5; /* 给分压节点 239.5 个 ADC 周期采样时间。 */
    if (HAL_ADC_ConfigChannel(&hadc1, &selected) != HAL_OK) /* 在 ADC 停止期间切换通道。 */
    {
        return "ADC_CONFIG_FAILED"; /* 配置失败，没有启动转换。 */
    }
    if (HAL_ADC_Start(&hadc1) != HAL_OK) /* 软件触发一次真实转换。 */
    {
        if (HAL_ADC_Stop(&hadc1) != HAL_OK) /* 启动失败也尝试让 ADC 回到停止状态。 */
        {
            return "ADC_START_AND_STOP_FAILED"; /* 同时报告启动与清理失败。 */
        }
        return "ADC_START_FAILED"; /* 不把启动失败记作完成转换。 */
    }
    if (HAL_ADC_PollForConversion(&hadc1, ADC_TIMEOUT_MILLISECONDS) != HAL_OK) /* 等待真实完成标志，最多 20 ms。 */
    {
        if (HAL_ADC_Stop(&hadc1) != HAL_OK) /* 超时或错误后也关闭 ADC。 */
        {
            return "ADC_POLL_AND_STOP_FAILED"; /* 明确报告等待和停止均失败。 */
        }
        return "ADC_POLL_FAILED"; /* 未确认完成的转换不计入成功转换数。 */
    }
    *raw = HAL_ADC_GetValue(&hadc1); /* 唯一的原码来源：读取 ADC 数据寄存器。 */
    ++(*conversions); /* 确认完成并取值后记录一次，停止失败也不会抹去已经发生的转换。 */
    if (HAL_ADC_Stop(&hadc1) != HAL_OK) /* 每次取值后停止，再允许下一次切换通道。 */
    {
        return "ADC_STOP_FAILED"; /* ADC 状态不可靠，本轮不接受为正常测量。 */
    }
    if (*raw > DIV_ADC_MAX_CODE) /* 检查返回值与 12 位右对齐配置一致。 */
    {
        return "ADC_RANGE_FAILED"; /* 不对越界原码套用电压换算。 */
    }
    return "OK"; /* 本次配置、启动、等待、取值和停止全部成功。 */
}

static void SendReport(const DivMeasurement *result) /* 只发送已经保存的检测结果，不再进行 ADC 转换。 */
{
    char line[REPORT_BUFFER_SIZE]; /* 保存完整的一行串口报告。 */
    char state_text[16] = "UNKNOWN"; /* 未确认唯一匹配前使用未知状态。 */
    char vb_raw_text[12] = "NA"; /* 未取得有效 VB 原码时不发送伪造的零。 */
    char va_raw_text[12] = "NA"; /* 未取得有效 VA 原码时显示未读。 */
    char vb_mv_text[12] = "NA"; /* VB 未读时没有可用的毫伏值。 */
    char va_mv_text[12] = "NA"; /* VA 未读时没有可用的毫伏值。 */
    const char *kind = "UNKNOWN"; /* 将正常、已知故障、未知分开显示。 */
    int written; /* 保存 snprintf 实际需要的字符数。 */
    if (result->state >= 0) /* 只有唯一匹配才输出 DIV 编号。 */
    {
        snprintf(state_text, sizeof(state_text), "DIV%d", result->state); /* 将内部编号转换为 DIV0 至 DIV8。 */
        kind = result->state == 0 ? "NORMAL" : "FAULT"; /* DIV0 为正常，其他已知工况为故障。 */
    }
    if (result->vb_valid) /* 只有有效 VB 采样才能进入报告。 */
    {
        snprintf(vb_raw_text, sizeof(vb_raw_text), "%lu", (unsigned long)result->vb_raw); /* 格式化真实 VB 原码。 */
        snprintf(vb_mv_text, sizeof(vb_mv_text), "%lu", (unsigned long)result->vb_mv); /* 格式化 VB 换算值。 */
    }
    if (result->va_valid) /* 独立判断 VA，避免沿用上一轮数据。 */
    {
        snprintf(va_raw_text, sizeof(va_raw_text), "%lu", (unsigned long)result->va_raw); /* 格式化真实 VA 原码。 */
        snprintf(va_mv_text, sizeof(va_mv_text), "%lu", (unsigned long)result->va_mv); /* 格式化 VA 换算值。 */
    }
    written = snprintf(line, sizeof(line), /* 按固定字段名组成便于保存与核对的串口记录。 */
        "STATE=%s KIND=%s VB_RAW=%s VB_MV=%s VA_RAW=%s VA_MV=%s " /* 先输出状态和两点原码、电压。 */
        "FEATURE_READS=%lu ADC_CONVERSIONS=%lu ELAPSED_MS=%lu " /* 分别输出节点数、转换数和检测耗时。 */
        "RUN_POWER=NOT_IMPLEMENTED ERROR=%s\\r\\n", /* 本阶段没有受控运行电源，明确报告未实现。 */
        state_text, kind, vb_raw_text, vb_mv_text, va_raw_text, va_mv_text, /* 对应前六个文本字段。 */
        (unsigned long)result->feature_reads, (unsigned long)result->adc_conversions, /* 使用本轮实际累加的计数。 */
        (unsigned long)result->elapsed_ms, result->error); /* 输出计时结果和错误阶段。 */
    if (written < 0 || written >= (int)sizeof(line)) /* 检查格式化失败和缓冲区不足。 */
    {
        Error_Handler(); /* 不发送截断或损坏的记录。 */
    }
    if (HAL_UART_Transmit(&huart1, (uint8_t *)line, (uint16_t)written, UART_TIMEOUT_MILLISECONDS) != HAL_OK) /* 由 PA9 发往终端 RXD。 */
    {
        Error_Handler(); /* 串口发送失败时停止，避免伪称已交付数据。 */
    }
}

static void RunDivDetection(void) /* 完整执行一次固定两点检测，不实现 RC 或按需补测优化。 */
{
    DivMeasurement result = {0}; /* 清空这一轮记录；两个有效标志均为假。 */
    uint32_t started_ms = HAL_GetTick(); /* 在通道配置之前开始计时。 */
    result.state = DIV_UNKNOWN; /* 在读完两点并成功判别之前维持未知。 */
    result.error = ReadAdcChannel(ADC_CHANNEL_0, &result.vb_raw, &result.adc_conversions); /* 从 PA0 读取 VB。 */
    if (result.error[0] == 'O' && result.error[1] == 'K') /* 只在第一次采样完整成功后使用该值。 */
    {
        result.vb_valid = 1; /* 标记本轮 VB 已读取。 */
        result.vb_mv = DivCodeToMillivolts(result.vb_raw); /* 由原码换算 VB 的毫伏值。 */
        ++result.feature_reads; /* VB 是本轮第一个有效节点。 */
        result.error = ReadAdcChannel(ADC_CHANNEL_1, &result.va_raw, &result.adc_conversions); /* 切到 PA1 读取 VA。 */
        if (result.error[0] == 'O' && result.error[1] == 'K') /* VA 采样成功才允许两点判别。 */
        {
            result.va_valid = 1; /* 标记本轮 VA 已读取。 */
            result.va_mv = DivCodeToMillivolts(result.va_raw); /* 由原码换算 VA 的毫伏值。 */
            ++result.feature_reads; /* VA 是本轮第二个有效节点。 */
            result.state = DivClassify((int32_t)result.vb_mv, (int32_t)result.va_mv); /* 用电压闭区间确定唯一工况。 */
        }
    }
    result.elapsed_ms = HAL_GetTick() - started_ms; /* 在串口发送和循环延时之前停止计时，允许真实结果为 0 ms。 */
    SendReport(&result); /* 发送本轮报告；这一步不包含在 ELAPSED_MS 中。 */
    if (!(result.error[0] == 'O' && result.error[1] == 'K')) /* ADC 错误已有报告时保留现场。 */
    {
        Error_Handler(); /* 停止后由用户复位重试，不自动制造更多不可靠结果。 */
    }
}
''')  # 用真实 HAL 采样链替换旧的仅显示电压逻辑。
replace_region("2", '''
  const char startup[] = "BOOT=DIV_20261011 MODE=TWO_NODES VREF_MV=3300 ADC_BITS=12 BAUD=115200 RUN_POWER=NOT_IMPLEMENTED\\r\\n"; /* 自报固件版本和换算假设。 */
  const char calibration_error[] = "STATE=UNKNOWN ERROR=ADC_CALIBRATION_FAILED RUN_POWER=NOT_IMPLEMENTED\\r\\n"; /* 校准失败时明确说明原因。 */
  if (HAL_UART_Transmit(&huart1, (uint8_t *)startup, sizeof(startup) - 1, UART_TIMEOUT_MILLISECONDS) != HAL_OK) /* 上电先验证终端链路。 */
  {
    Error_Handler(); /* 启动信息发送失败时停止。 */
  }
  if (HAL_ADCEx_Calibration_Start(&hadc1) != HAL_OK) /* 所有外设初始化之后只校准一次。 */
  {
    HAL_UART_Transmit(&huart1, (uint8_t *)calibration_error, sizeof(calibration_error) - 1, UART_TIMEOUT_MILLISECONDS); /* 尽力报告校准故障。 */
    Error_Handler(); /* 校准失败不得继续采样判别。 */
  }
''')  # 保留原先校准行为并补充可见错误信息。
replace_region("3", '''
    RunDivDetection(); /* 两点采样、判别、计数、计时并发送本轮结果。 */
    HAL_Delay(REPORT_PERIOD_MILLISECONDS); /* 给终端留出观察时间，不计入本轮检测耗时。 */
  }
''')  # 原循环的右花括号就在 USER CODE 3 中，保持结构。
text = text.replace("huart1.Init.BaudRate = 9600;", "huart1.Init.BaudRate = 115200; /* 与终端统一为 115200 波特。 */")  # 修改生成初始化代码并同步下面的 ioc。
comments = {  # 对原 CubeMX 初始化中的有效语句补充中文作用说明。
    '#include "main.h"': '引入 HAL、芯片定义和 Error_Handler 声明。',
    'ADC_HandleTypeDef hadc1;': '保存 ADC1 的 HAL 配置及状态。',
    'UART_HandleTypeDef huart1;': '保存 USART1 的 HAL 配置及状态。',
    'void SystemClock_Config(void);': '声明系统时钟配置函数。',
    'static void MX_GPIO_Init(void);': '声明 GPIO 初始化函数。',
    'static void MX_ADC1_Init(void);': '声明 ADC1 初始化函数。',
    'static void MX_USART1_UART_Init(void);': '声明 USART1 初始化函数。',
    'HAL_Init();': '复位 HAL 并建立 1 ms 的 SysTick 时间基准。',
    'SystemClock_Config();': '应用原工程的内部 HSI 8 MHz 时钟方案。',
    'MX_GPIO_Init();': '打开 GPIOA 时钟。',
    'MX_ADC1_Init();': '初始化 ADC1 单次软件转换，MSP 同时设置 PA0 和 PA1 为模拟输入。',
    'MX_USART1_UART_Init();': '初始化 USART1 与 PA9、PA10 引脚。',
    'RCC_OscInitTypeDef RCC_OscInitStruct = {0};': '将振荡器配置字段全部清零。',
    'RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};': '将总线时钟配置字段全部清零。',
    'RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};': '将 ADC 外设时钟配置字段全部清零。',
    'RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;': '选择片内 HSI 振荡器。',
    'RCC_OscInitStruct.HSIState = RCC_HSI_ON;': '开启 8 MHz HSI。',
    'RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;': '保留 HSI 默认校准值。',
    'RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;': '保持原工程不使用 PLL 的配置。',
    'if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)': '应用振荡器设置并检查失败。',
    '|RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;': '连同上一行选择 SYSCLK、HCLK、PCLK1 和 PCLK2。',
    'RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;': '系统时钟选 HSI 8 MHz。',
    'RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;': 'AHB 不分频，HCLK 为 8 MHz。',
    'RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;': 'APB1 不分频，为 8 MHz。',
    'RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;': 'APB2 不分频，为 8 MHz。',
    'if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)': '应用总线频率；8 MHz 使用零个 Flash 等待周期。',
    'PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_ADC;': '选择要配置的 ADC 外设时钟。',
    'PeriphClkInit.AdcClockSelection = RCC_ADCPCLK2_DIV2;': '8 MHz 除以二，ADC 工作在 4 MHz。',
    'if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)': '应用 ADC 时钟并检查失败。',
    'ADC_ChannelConfTypeDef sConfig = {0};': '准备初始通道配置，各字段先清零。',
    'hadc1.Instance = ADC1;': '选择芯片 ADC1 外设。',
    'hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;': '关闭多通道自动扫描，由应用逐次切换通道。',
    'hadc1.Init.ContinuousConvMode = DISABLE;': '关闭连续转换，每次 Start 仅转换一次。',
    'hadc1.Init.DiscontinuousConvMode = DISABLE;': '关闭间断扫描模式。',
    'hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;': '由软件启动，不使用外部触发器。',
    'hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;': '原码右对齐，直接得到 0 至 4095。',
    'hadc1.Init.NbrOfConversion = 1;': '常规序列长度设为一。',
    'if (HAL_ADC_Init(&hadc1) != HAL_OK)': '应用 ADC 配置并检查失败。',
    'sConfig.Channel = ADC_CHANNEL_0;': '启动后的默认输入为 PA0 的 VB。',
    'sConfig.Rank = ADC_REGULAR_RANK_1;': '通道位于常规序列第一位。',
    'sConfig.SamplingTime = ADC_SAMPLETIME_239CYCLES_5;': '初始采样时间同样为 239.5 周期。',
    'if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)': '应用初始通道配置并检查失败。',
    'huart1.Instance = USART1;': '选择 USART1 外设。',
    'huart1.Init.WordLength = UART_WORDLENGTH_8B;': '每帧包含八个数据位。',
    'huart1.Init.StopBits = UART_STOPBITS_1;': '每帧使用一个停止位。',
    'huart1.Init.Parity = UART_PARITY_NONE;': '不使用奇偶校验。',
    'huart1.Init.Mode = UART_MODE_TX_RX;': '保留原工程收发模式，本应用只发送。',
    'huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;': '不使用 CTS 或 RTS 流控。',
    'huart1.Init.OverSampling = UART_OVERSAMPLING_16;': '使用十六倍串口过采样。',
    'if (HAL_UART_Init(&huart1) != HAL_OK)': '应用串口和 MSP 引脚配置并检查失败。',
    '__HAL_RCC_GPIOA_CLK_ENABLE();': '使能 GPIOA 时钟以便配置 PA 引脚。',
    '__disable_irq();': '错误时关闭中断，保留失败现场供检查。',
    'while (1)': '持续执行循环；错误处理中的空循环用于停机。',
    'Error_Handler();': '初始化失败时停止，不继续发送可能错误的读数。',
}  # 库文件保持原样，不改动 ST 底层实现。
text = "\n".join(line + (" /* " + comments[line.strip()] + " */" if line.strip() in comments else "") for line in text.splitlines()) + "\n"  # 给原初始化语句补上逐句解释。
main_path.write_text(text, encoding="utf-8")  # 保存带原 USER CODE 标记的最终主程序。
ioc_path = project / "ADC_CubeMX_Keil.ioc"  # 配置文件必须与初始化代码保持一致。
ioc = ioc_path.read_text(encoding="utf-8")  # 读取原 CubeMX 工程而不是新建无关工程。
ioc = ioc.replace("USART1.BaudRate=9600", "USART1.BaudRate=115200")  # 重新生成时仍使用 115200。
ioc_path.write_text(ioc, encoding="utf-8")  # 除波特率外保留全部原配置。
print("已更新原工程 main.c USER CODE 与 USART1 波特率，未修改 HAL 驱动和 RC 功能。")  # 输出实际完成的变更。
