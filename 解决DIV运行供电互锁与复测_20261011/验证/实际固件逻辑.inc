
typedef struct /* 保存一次检测结果，初始化时所有有效标志为假。 */
{
    uint32_t vb_raw; /* VB 的真实 ADC 原码，仅在 vb_valid 为真时可用。 */
    uint32_t va_raw; /* VA 的真实 ADC 原码，仅在 va_valid 为真时可用。 */
    uint32_t vb_mv; /* VB 四舍五入后的 mV 值。 */
    uint32_t va_mv; /* VA 四舍五入后的 mV 值。 */
    uint32_t adc_conversions; /* 每次 Poll 成功并 GetValue 后递增。 */
    uint32_t feature_reads; /* 实际获得有效读数的不同节点数。 */
    uint32_t elapsed_ms; /* 从断开旧电源到判别和供电设置完成的毫秒数，不含串口发送。 */
    int vb_valid; /* VB 已有效采样时为真，未读时输出 NA。 */
    int va_valid; /* VA 已有效采样时为真，未读时输出 NA。 */
    int state; /* 唯一工况编号，或 DIV_UNKNOWN。 */
    const char *error; /* OK 或明确的 ADC 错误阶段。 */
} DivMeasurement; /* 为本次采集记录定义类型名。 */

typedef struct /* 保存复测按钮的消抖状态，持续按下只触发一次。 */
{
    GPIO_PinState raw_level; /* 最近一次读到的按钮电平。 */
    GPIO_PinState stable_level; /* 已连续稳定足够时间的按钮电平。 */
    uint32_t changed_ms; /* 原始电平最后变化的时刻。 */
} RetestButton; /* 为复测按钮的状态定义类型名。 */



#define ADC_TIMEOUT_MILLISECONDS 20 /* 最多等待一次 ADC 转换 20 ms。 */
#define UART_TIMEOUT_MILLISECONDS 100 /* 一条报告最多发送 100 ms。 */
#define REPORT_BUFFER_SIZE 384 /* 容纳整条带状态和错误信息的报告。 */
#define TEST_POWER_PIN GPIO_PIN_12 /* PB12，芯片第 25 脚，控制 1 V 测试电源开关。 */
#define RUN_POWER_PIN GPIO_PIN_13 /* PB13，芯片第 26 脚，控制 3 V 运行电源开关。 */
#define RETEST_BUTTON_PIN GPIO_PIN_4 /* PA4，芯片第 14 脚，复测按钮按下接地。 */
#define STOP_BUTTON_PIN GPIO_PIN_5 /* PA5，芯片第 15 脚，停止按钮按下接地。 */
#define POWER_BREAK_MILLISECONDS 5 /* 两路电源都断开后等待 5 ms，保证先断后合。 */
#define TEST_SETTLE_MILLISECONDS 20 /* 打开测试电源后等待 20 ms，使 DIV 电压稳定。 */
#define BUTTON_DEBOUNCE_MILLISECONDS 20 /* 复测按钮稳定 20 ms 后接受一次按下事件。 */
#define CONTROL_POLL_MILLISECONDS 1 /* 主循环每隔 1 ms 检查复测；停止由中断立即断电。 */
#define DIV_NORMAL_CASE 0 /* 正常工况为 DIV0，只有该状态允许进入运行。 */



static volatile int power_gpio_ready = 0; /* GPIO 尚未初始化时禁止访问断电输出。 */
static volatile int stop_requested = 0; /* 停止中断锁存此标志，只有松开停止并按复测才解除。 */
static int detection_pending = 1; /* 上电安排一次检测，完成后等待复测按钮。 */
static int stop_reported = 0; /* 一次停止事件只输出一条事件报告。 */
static RetestButton retest_button = {GPIO_PIN_SET, GPIO_PIN_SET, 0}; /* 未按按钮默认为高电平。 */



static const char *ReadAdcChannel(uint32_t channel, uint32_t *raw, uint32_t *conversions); /* 声明真实采样函数。 */
static void SendReport(const DivMeasurement *result); /* 声明报告函数。 */
static void RunDivDetection(void); /* 声明一次完整检测。 */
static void AllPowerOff(void); /* 声明无等待的双路断电函数，可由停止中断调用。 */
static void ServiceControls(void); /* 声明复测和停止按钮的处理函数。 */



static void AllPowerOff(void) /* 同一次 GPIO 写操作关闭两个开关，不在中断里延时。 */
{
    if (power_gpio_ready) /* 初始化未完成时由外部下拉电阻维持断电。 */
    {
        HAL_GPIO_WritePin(GPIOB, TEST_POWER_PIN | RUN_POWER_PIN, GPIO_PIN_RESET); /* 将 PB12 和 PB13 一起拉低。 */
    }
}

static int StopIsActive(void) /* 同时检查锁存事件和按钮实时电平，包含上电时已按住的情况。 */
{
    return stop_requested || HAL_GPIO_ReadPin(GPIOA, STOP_BUTTON_PIN) == GPIO_PIN_RESET; /* 任一条件成立就禁止上电。 */
}

void DivEmergencyStop(void) /* 供停止中断和故障中断使用，不调用串口或 HAL_Delay。 */
{
    stop_requested = 1; /* 锁存停止，按钮松开也不会自动恢复运行。 */
    AllPowerOff(); /* 立即关闭测试和运行电源。 */
}

void HAL_GPIO_EXTI_Callback(uint16_t pin) /* HAL 在处理停止按钮的下降沿中断后调用此函数。 */
{
    if (pin == STOP_BUTTON_PIN) /* 只处理本工程接在 PA5 的停止按钮。 */
    {
        DivEmergencyStop(); /* 按下时立即断电，主循环随后发送停止事件。 */
    }
}

static int WaitWithoutStop(uint32_t milliseconds) /* 在稳定等待和互锁等待期间也允许停止取消检测。 */
{
    uint32_t started_ms = HAL_GetTick(); /* 保存等待开始时刻。 */
    while (HAL_GetTick() - started_ms < milliseconds) /* 无符号差值允许毫秒计数器回绕。 */
    {
        if (StopIsActive()) /* 检查等待期间是否出现停止。 */
        {
            DivEmergencyStop(); /* 即使按钮没有产生新下降沿，也保证立即断电。 */
            return 0; /* 告诉调用方本次等待被停止取消。 */
        }
        HAL_Delay(CONTROL_POLL_MILLISECONDS); /* 等待一个毫秒，保持 SysTick 正常更新。 */
    }
    if (StopIsActive()) /* 在等待结束的边界再检查一次停止。 */
    {
        DivEmergencyStop(); /* 保证边界出现的停止也关闭两路。 */
        return 0; /* 禁止继续合闸。 */
    }
    return 1; /* 等待完成且没有停止请求。 */
}

static int SelectPower(uint16_t selected_pin) /* 只允许在两个开关均关闭并等待之后开启其中一路。 */
{
    uint32_t previous_interrupt_mask; /* 保存调用前的中断屏蔽状态，不能擅自开启原本关闭的中断。 */
    int enabled = 0; /* 默认没有合闸，只有通过所有检查才置为成功。 */
    AllPowerOff(); /* 每次切换首先断开旧电源和另一条电源。 */
    if (selected_pin != TEST_POWER_PIN && selected_pin != RUN_POWER_PIN) /* 拒绝同时开启两路或传入其他引脚。 */
    {
        return 0; /* 保持双路关闭并报告未合闸。 */
    }
    if (!WaitWithoutStop(POWER_BREAK_MILLISECONDS)) /* 至少保持两路断开 5 ms，并接受停止取消。 */
    {
        return 0; /* 被停止后不允许合闸。 */
    }
    previous_interrupt_mask = __get_PRIMASK(); /* 保存当前中断状态。 */
    __disable_irq(); /* 将停止检查和单路合闸作为不可被打断的一组操作。 */
    if (!StopIsActive()) /* 若停止已发生或按钮仍按住，就维持断电。 */
    {
        HAL_GPIO_WritePin(GPIOB, selected_pin, GPIO_PIN_SET); /* 只拉高选中的一根控制线。 */
        enabled = 1; /* 记录已经发出单路开启命令。 */
    }
    __set_PRIMASK(previous_interrupt_mask); /* 恢复原中断状态，已挂起的停止中断将立即关闭电源。 */
    return enabled; /* 后续步骤仍会检查停止标志，避免接受已被取消的检测。 */
}

static int RetestWasPressed(void) /* 产生经消抖的按下事件，持续按住不会重复检测。 */
{
    GPIO_PinState current_level = HAL_GPIO_ReadPin(GPIOA, RETEST_BUTTON_PIN); /* 读取 PA4，低电平表示按下。 */
    uint32_t now_ms = HAL_GetTick(); /* 获取消抖计时时刻。 */
    if (current_level != retest_button.raw_level) /* 原始电平改变时重新开始稳定计时。 */
    {
        retest_button.raw_level = current_level; /* 保存刚读到的电平。 */
        retest_button.changed_ms = now_ms; /* 从本次变化时刻起等待 20 ms。 */
    }
    if (current_level != retest_button.stable_level && now_ms - retest_button.changed_ms >= BUTTON_DEBOUNCE_MILLISECONDS) /* 只接受持续稳定的变化。 */
    {
        retest_button.stable_level = current_level; /* 更新已确认的稳定电平。 */
        return current_level == GPIO_PIN_RESET; /* 仅按下沿返回真，松开沿只更新状态。 */
    }
    return 0; /* 没有新的稳定按下事件。 */
}

static const char *ReadAdcChannel(uint32_t channel, uint32_t *raw, uint32_t *conversions) /* 失败返回阶段名，成功返回 OK。 */
{
    ADC_ChannelConfTypeDef selected = {0}; /* 全部配置字段清零，随后明确设置所需字段。 */
    if (StopIsActive()) /* 停止若发生在上一通道转换期间，不再启动下一通道。 */
    {
        return "STOP_REQUESTED"; /* 断电后的读数不能作为新的有效测试采样。 */
    }
    selected.Channel = channel; /* 选择 PA0 的通道 0 或 PA1 的通道 1。 */
    selected.Rank = ADC_REGULAR_RANK_1; /* 单次转换只使用序列第一个位置。 */
    selected.SamplingTime = ADC_SAMPLETIME_239CYCLES_5; /* 给分压节点 239.5 个 ADC 周期采样时间。 */
    if (HAL_ADC_ConfigChannel(&hadc1, &selected) != HAL_OK) /* 在 ADC 停止期间切换通道。 */
    {
        return "ADC_CONFIG_FAILED"; /* 配置失败，没有启动转换。 */
    }
    if (StopIsActive()) /* 配置完成到启动之前再次检查停止。 */
    {
        return "STOP_REQUESTED"; /* 不在已经断电的电路上启动 ADC 转换。 */
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
        kind = result->state == DIV_NORMAL_CASE ? "NORMAL" : "FAULT"; /* 正常编号使用具名常量表达。 */
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
        "RUN_POWER=%s TEST_POWER=%s POWER_SOURCE=GPIO_LEVEL ERROR=%s\r\n", /* GPIO 电平是控制证据，不能冒充独立电源测量。 */
        state_text, kind, vb_raw_text, vb_mv_text, va_raw_text, va_mv_text, /* 对应前六个文本字段。 */
        (unsigned long)result->feature_reads, (unsigned long)result->adc_conversions, /* 使用本轮实际累加的计数。 */
        (unsigned long)result->elapsed_ms, /* 输出包含测试准备和供电切换的检测耗时。 */
        HAL_GPIO_ReadPin(GPIOB, RUN_POWER_PIN) == GPIO_PIN_SET ? "ON" : "OFF", /* 读取 PB13 的实际逻辑电平快照。 */
        HAL_GPIO_ReadPin(GPIOB, TEST_POWER_PIN) == GPIO_PIN_SET ? "ON" : "OFF", /* 读取 PB12 的实际逻辑电平快照。 */
        result->error); /* 输出本轮的 ADC 错误或停止原因。 */
    if (written < 0 || written >= (int)sizeof(line)) /* 检查格式化失败和缓冲区不足。 */
    {
        Error_Handler(); /* 不发送截断或损坏的记录。 */
    }
    if (HAL_UART_Transmit(&huart1, (uint8_t *)line, (uint16_t)written, UART_TIMEOUT_MILLISECONDS) != HAL_OK) /* 由 PA9 发往终端 RXD。 */
    {
        Error_Handler(); /* 串口发送失败时停止，避免伪称已交付数据。 */
    }
}

static void RunDivDetection(void) /* 在 1 V 测试条件下检测一次，然后保持结果等待复测。 */
{
    DivMeasurement result = {0}; /* 清空这一轮记录；两个有效标志均为假。 */
    uint32_t started_ms = HAL_GetTick(); /* 从关闭旧供电和建立测试条件之前开始计时。 */
    result.state = DIV_UNKNOWN; /* 在读完两点并成功判别之前维持未知。 */
    result.error = "STOP_REQUESTED"; /* 建立测试状态失败时报告停止，不能伪造 ADC 数据。 */
    if (!SelectPower(TEST_POWER_PIN) || !WaitWithoutStop(TEST_SETTLE_MILLISECONDS)) /* 关闭运行、互锁等待、打开测试并稳定 20 ms。 */
    {
        AllPowerOff(); /* 建立测试状态失败时保证双路关闭。 */
        result.elapsed_ms = HAL_GetTick() - started_ms; /* 保存到取消时刻的真实耗时。 */
        SendReport(&result); /* 未采样的电压输出 NA，次数保持零。 */
        return; /* 本次被取消，等待新的复测事件。 */
    }
    result.error = ReadAdcChannel(ADC_CHANNEL_0, &result.vb_raw, &result.adc_conversions); /* 从 PA0 读取 VB。 */
    if (strcmp(result.error, "OK") == 0) /* 明确比较整个返回字符串，确认 VB 采样成功。 */
    {
        result.vb_valid = 1; /* 标记本轮 VB 已读取。 */
        result.vb_mv = DivCodeToMillivolts(result.vb_raw); /* 由原码换算 VB 的毫伏值。 */
        ++result.feature_reads; /* VB 是本轮第一个有效节点。 */
        result.error = ReadAdcChannel(ADC_CHANNEL_1, &result.va_raw, &result.adc_conversions); /* 切到 PA1 读取 VA。 */
        if (strcmp(result.error, "OK") == 0) /* VA 采样成功才允许两点判别。 */
        {
            result.va_valid = 1; /* 标记本轮 VA 已读取。 */
            result.va_mv = DivCodeToMillivolts(result.va_raw); /* 由原码换算 VA 的毫伏值。 */
            ++result.feature_reads; /* VA 是本轮第二个有效节点。 */
            result.state = DivClassify((int32_t)result.vb_mv, (int32_t)result.va_mv); /* 用电压闭区间确定唯一工况。 */
        }
    }
    if (StopIsActive()) /* 即使停止发生在 ADC 转换期间，也禁止接受结果并开启运行。 */
    {
        result.state = DIV_UNKNOWN; /* 已取消的检测不作为正常或故障验收结果。 */
        result.error = "STOP_REQUESTED"; /* 报告本轮取消原因。 */
        AllPowerOff(); /* 保持停止时的双路关闭。 */
    }
    else if (strcmp(result.error, "OK") == 0 && result.vb_valid && result.va_valid && result.state == DIV_NORMAL_CASE) /* 两点均成功且唯一匹配正常才进入运行。 */
    {
        if (!SelectPower(RUN_POWER_PIN) || StopIsActive()) /* 先断开测试电源，再等待 5 ms，最后尝试开启运行。 */
        {
            result.state = DIV_UNKNOWN; /* 切换被停止取消时拒绝正常结果。 */
            result.error = "STOP_REQUESTED"; /* 输出明确的取消原因。 */
            AllPowerOff(); /* 保证双路最终关闭。 */
        }
    }
    else /* 已知故障、未知工况或任何 ADC 失败都不允许进入运行。 */
    {
        AllPowerOff(); /* 检测完成后连测试电源也关闭，保持等待复测状态。 */
    }
    result.elapsed_ms = HAL_GetTick() - started_ms; /* 包含测试建立、采样判别和最终供电切换，不含串口与按钮等待。 */
    SendReport(&result); /* 发送本次测试时保存的电压，即使现在已经进入 3 V 运行也不再采样。 */
}

static void SendStopEvent(void) /* 报告停止事件，与用于填写 CSV 的 STATE 检测记录分开。 */
{
    const char stopped[] = "EVENT=STOP RUN_POWER=OFF TEST_POWER=OFF MODE=WAIT_RETEST\r\n"; /* 表明停止后必须重新按复测。 */
    if (HAL_UART_Transmit(&huart1, (uint8_t *)stopped, sizeof(stopped) - 1, UART_TIMEOUT_MILLISECONDS) != HAL_OK) /* 在主循环里发送，中断只负责断电。 */
    {
        Error_Handler(); /* 通信失败也维持双路断电并停机。 */
    }
}

static void ServiceControls(void) /* 平时只检查按钮，不重复 ADC 采样或自动改变运行供电。 */
{
    if (StopIsActive()) /* 停止按钮优先于任何复测操作。 */
    {
        DivEmergencyStop(); /* 锁存停止并确保两路关闭。 */
        detection_pending = 0; /* 取消未执行的自动检测。 */
        if (!stop_reported) /* 同一次停止只报告一次。 */
        {
            SendStopEvent(); /* 让终端看到停止后供电关闭。 */
            stop_reported = 1; /* 后续循环不重复发送。 */
        }
    }
    if (RetestWasPressed() && HAL_GPIO_ReadPin(GPIOA, STOP_BUTTON_PIN) == GPIO_PIN_SET) /* 停止按钮松开后，新的复测按下事件才有效。 */
    {
        uint32_t previous_interrupt_mask = __get_PRIMASK(); /* 保存进入临界区前的中断状态。 */
        __disable_irq(); /* 防止解除旧停止标志时丢失同时出现的新停止。 */
        if (HAL_GPIO_ReadPin(GPIOA, STOP_BUTTON_PIN) == GPIO_PIN_SET) /* 在临界区内再次确认停止按钮没有按下。 */
        {
            stop_requested = 0; /* 只通过用户明确的复测动作解除停止锁存。 */
            detection_pending = 1; /* 安排一轮完整的断电、测试、采样和判别。 */
            stop_reported = 0; /* 允许下一次独立停止事件再次报告。 */
        }
        __set_PRIMASK(previous_interrupt_mask); /* 新挂起的停止中断随后仍可取消这一轮。 */
    }
    if (detection_pending && !StopIsActive()) /* 只有有检测请求且未停止才进行 ADC 检测。 */
    {
        detection_pending = 0; /* 执行前先清除请求，防止下一圈自动再测。 */
        RunDivDetection(); /* 测量一次，完成后保持运行或断电，直到用户按复测。 */
    }
}


static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef configured = {0}; /* 先将 GPIO 配置结构清零，再明确填写所需设置。 */
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOA_CLK_ENABLE(); /* 使能 GPIOA 时钟以便配置 PA 引脚。 */
  __HAL_RCC_GPIOB_CLK_ENABLE(); /* 打开 GPIOB 时钟以控制 PB12 和 PB13。 */
  __HAL_RCC_AFIO_CLK_ENABLE(); /* 打开复用功能时钟，使 PA5 能映射到外部中断线。 */

  /* USER CODE BEGIN MX_GPIO_Init_2 */
  HAL_GPIO_WritePin(GPIOB, TEST_POWER_PIN | RUN_POWER_PIN, GPIO_PIN_RESET); /* 先预置输出锁存为低，再启用输出，避免合闸毛刺。 */
  configured.Pin = TEST_POWER_PIN | RUN_POWER_PIN; /* 配置两根电源控制线。 */
  configured.Mode = GPIO_MODE_OUTPUT_PP; /* 使用推挽输出，低电平断开、高电平闭合。 */
  configured.Pull = GPIO_NOPULL; /* 输出运行时无需内部上下拉，复位时由外部 100 kOhm 下拉保证断电。 */
  configured.Speed = GPIO_SPEED_FREQ_LOW; /* 控制开关无需高速边沿，使用低速输出。 */
  HAL_GPIO_Init(GPIOB, &configured); /* 启用 PB12 和 PB13 的低电平输出。 */
  power_gpio_ready = 1; /* 此后故障和停止处理均可以调用双路断电。 */
  configured.Pin = RETEST_BUTTON_PIN; /* 选择 PA4 作为复测按钮输入。 */
  configured.Mode = GPIO_MODE_INPUT; /* 复测由主循环消抖，不使用外部中断。 */
  configured.Pull = GPIO_PULLUP; /* 松开为高，按下接 GND 为低。 */
  HAL_GPIO_Init(GPIOA, &configured); /* 应用复测按钮设置。 */
  configured.Pin = STOP_BUTTON_PIN; /* 选择 PA5 作为停止按钮输入。 */
  configured.Mode = GPIO_MODE_IT_FALLING; /* 按下产生下降沿中断，优先立即断电。 */
  HAL_GPIO_Init(GPIOA, &configured); /* 应用停止按钮上拉和外部中断设置。 */
  HAL_NVIC_SetPriority(EXTI9_5_IRQn, 0, 0); /* 停止使用最高可配置优先级，数值零表示最高紧迫程度。 */
  HAL_NVIC_EnableIRQ(EXTI9_5_IRQn); /* 允许 EXTI5 所在的共享中断进入停止处理。 */

  /* USER CODE END MX_GPIO_Init_2 */
}