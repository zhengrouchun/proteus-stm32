/* 测试同一份真实固件逻辑；HAL 替身仅模拟 ADC、GPIO、计时和串口，不代表 Proteus 实测。 */
#include <assert.h> /* 验证供电互锁、误判和次数等行为要求。 */
#include <stdint.h> /* 与 STM32 使用相同的固定宽度整数。 */
#include <stdio.h> /* 输出行为测试结果。 */
#include <stdlib.h> /* 发生未预期的 Error_Handler 时终止测试。 */
#include <string.h> /* 保存和检查实际串口报告文本。 */
#include "../工程/Inc/div_diagnosis.h" /* 使用工程中的真实电压换算和九工况判别。 */

typedef enum {GPIO_PIN_RESET, GPIO_PIN_SET} GPIO_PinState; /* 模拟 HAL 的低、高电平枚举。 */
typedef struct {int unused;} ADC_HandleTypeDef; /* 测试中只需要 ADC 句柄的地址。 */
typedef struct {int unused;} UART_HandleTypeDef; /* 测试中只需要串口句柄的地址。 */
typedef struct {uint32_t Channel, Rank, SamplingTime;} ADC_ChannelConfTypeDef; /* 保存固件指定的 ADC 通道配置。 */
typedef struct {uint32_t Pin, Mode, Pull, Speed;} GPIO_InitTypeDef; /* 保存固件指定的 GPIO 初始化参数。 */
#define GPIOA 1 /* 区分按钮所在的端口。 */
#define GPIOB 2 /* 区分控制输出所在的端口。 */
#define GPIO_PIN_4 (1 << 4) /* PA4 复测输入的位掩码。 */
#define GPIO_PIN_5 (1 << 5) /* PA5 停止输入的位掩码。 */
#define GPIO_PIN_12 (1 << 12) /* PB12 测试电源输出的位掩码。 */
#define GPIO_PIN_13 (1 << 13) /* PB13 运行电源输出的位掩码。 */
#define GPIO_MODE_INPUT 1 /* 测试配置中区分普通输入。 */
#define GPIO_MODE_OUTPUT_PP 2 /* 测试配置中区分推挽输出。 */
#define GPIO_MODE_IT_FALLING 3 /* 测试配置中区分下降沿中断。 */
#define GPIO_NOPULL 0 /* 测试配置中区分不使用内部上拉。 */
#define GPIO_PULLUP 1 /* 测试配置中区分按钮上拉。 */
#define GPIO_SPEED_FREQ_LOW 1 /* 记录低速输出配置。 */
#define EXTI9_5_IRQn 23 /* 模拟停止按钮的中断标识。 */
#define HAL_OK 0 /* 模拟 HAL 的成功返回值。 */
#define HAL_ERROR 1 /* 模拟 HAL 的错误返回值。 */
#define ADC_CHANNEL_0 0 /* 模拟 VB 所在的通道。 */
#define ADC_CHANNEL_1 1 /* 模拟 VA 所在的通道。 */
#define ADC_REGULAR_RANK_1 1 /* 检查单次转换的序列位置。 */
#define ADC_SAMPLETIME_239CYCLES_5 239 /* 检查固件选定的长采样档位。 */
#define __HAL_RCC_GPIOA_CLK_ENABLE() ((void)0) /* 主机不实际访问 RCC 寄存器。 */
#define __HAL_RCC_GPIOB_CLK_ENABLE() ((void)0) /* 主机不实际访问 RCC 寄存器。 */
#define __HAL_RCC_AFIO_CLK_ENABLE() ((void)0) /* 主机不实际访问 RCC 寄存器。 */

static uint32_t tick_ms, outputs, interrupt_mask, selected_channel, last_off_ms; /* 模拟计时、控制输出与 ADC 当前通道。 */
static int stop_level, retest_level, stop_at_ms, failure_stage, failure_channel; /* 保存按钮、停止注入时刻和 ADC 故障配置。 */
static int adc_reads, reports, pending_interrupt; /* 记录真实逻辑的转换读取和报告次数。 */
static int sample_vb_mv, sample_va_mv; /* 测试用输入，明确标为合成数据。 */
static char last_report[512]; /* 保存固件实际格式化出来的最近一条串口报告。 */
static GPIO_InitTypeDef output_configuration, stop_configuration; /* 核查实际 GPIO 初始化配置。 */
ADC_HandleTypeDef hadc1; /* 为真实固件函数提供 ADC 句柄。 */
UART_HandleTypeDef huart1; /* 为真实固件函数提供 UART 句柄。 */
void DivEmergencyStop(void); /* 中断注入需要调用真实停止实现。 */
static uint32_t HAL_GetTick(void) {return tick_ms;} /* 固件读取模拟毫秒时钟。 */
static uint32_t __get_PRIMASK(void) {return interrupt_mask;} /* 固件可保存模拟中断屏蔽状态。 */
static void __disable_irq(void) {interrupt_mask = 1;} /* 模拟进入临界区。 */
static void __set_PRIMASK(uint32_t saved) /* 模拟恢复中断后立即处理挂起的停止。 */
{
    interrupt_mask = saved; /* 恢复调用前的中断状态。 */
    if (!interrupt_mask && pending_interrupt) /* 未屏蔽中断且有新停止时立即处理。 */
    {
        pending_interrupt = 0; /* 清除待处理事件。 */
        DivEmergencyStop(); /* 调用真实的双路断电实现。 */
    }
}
static GPIO_PinState HAL_GPIO_ReadPin(int port, uint16_t pin) /* 区分按钮输入和控制引脚电平。 */
{
    if (port == GPIOB) return outputs & pin ? GPIO_PIN_SET : GPIO_PIN_RESET; /* 回读当前输出，供真实报告使用。 */
    return (pin == GPIO_PIN_5 ? stop_level : retest_level) ? GPIO_PIN_SET : GPIO_PIN_RESET; /* 回读对应按钮。 */
}
static void HAL_GPIO_WritePin(int port, uint16_t pins, GPIO_PinState level) /* 每次真实固件输出变化都核验互锁。 */
{
    assert(port == GPIOB); /* 本测试的供电输出只能来自 GPIOB。 */
    if (level == GPIO_PIN_SET) /* 对每次合闸核验先断后合要求。 */
    {
        assert(outputs == 0); /* 合闸前两路必须都关闭。 */
        assert(tick_ms - last_off_ms >= 5); /* 合闸前必须有至少 5 ms 双路断开间隔。 */
        outputs |= pins; /* 应用真实固件的合闸命令。 */
    }
    else /* 关闭命令必须能够同时关闭两路。 */
    {
        outputs &= ~pins; /* 应用真实固件的断电命令。 */
        if (!outputs) last_off_ms = tick_ms; /* 保存最近一次断开时刻。 */
    }
    assert(outputs != (GPIO_PIN_12 | GPIO_PIN_13)); /* 两路同时开启在任何测试路径下都立即失败。 */
}
static void HAL_Delay(uint32_t delay) /* 在互锁与稳定等待中按指定时刻注入停止。 */
{
    tick_ms += delay; /* 推进模拟时钟。 */
    if (stop_at_ms >= 0 && tick_ms >= (uint32_t)stop_at_ms) /* 本次测试到达指定停止时刻。 */
    {
        stop_at_ms = -1; /* 每个停止事件只注入一次。 */
        stop_level = 0; /* 模拟停止按钮按下。 */
        if (interrupt_mask) pending_interrupt = 1; /* 若在临界区中则等待中断恢复。 */
        else DivEmergencyStop(); /* 否则立即调用真实停止处理。 */
    }
}
static void HAL_GPIO_Init(int port, GPIO_InitTypeDef *config) /* 记录而不复制 GPIO 配置算法。 */
{
    if (port == GPIOB) output_configuration = *config; /* 核查 PB12/PB13 的输出模式和引脚掩码。 */
    if (port == GPIOA && config->Pin == GPIO_PIN_5) stop_configuration = *config; /* 核查 PA5 的上拉及下降沿中断。 */
}
static void HAL_NVIC_SetPriority(int irq, int priority, int subpriority) /* 核查停止的中断优先级。 */
{
    assert(irq == EXTI9_5_IRQn && priority == 0 && subpriority == 0); /* 停止必须使用本工程指定的最高优先级。 */
}
static void HAL_NVIC_EnableIRQ(int irq) {assert(irq == EXTI9_5_IRQn);} /* 核查启用的是停止按钮中断。 */
static int injected_failure(int stage) {return failure_stage == stage && (int)selected_channel == failure_channel;} /* 按通道与阶段模拟 ADC 故障。 */
static int HAL_ADC_ConfigChannel(ADC_HandleTypeDef *handle, ADC_ChannelConfTypeDef *config) /* 记录真实通道配置。 */
{
    (void)handle; /* ADC 句柄本身不需要硬件寄存器。 */
    selected_channel = config->Channel; /* 保存 VB 或 VA 通道。 */
    assert(outputs == GPIO_PIN_12); /* ADC 采样时必须只有 1 V 测试电源开启。 */
    assert(config->Rank == ADC_REGULAR_RANK_1 && config->SamplingTime == ADC_SAMPLETIME_239CYCLES_5); /* 核查实际采样配置。 */
    return injected_failure(1) ? HAL_ERROR : HAL_OK; /* 模拟配置阶段失败或成功。 */
}
static int HAL_ADC_Start(ADC_HandleTypeDef *handle) {(void)handle; return injected_failure(2) ? HAL_ERROR : HAL_OK;} /* 模拟启动失败。 */
static int HAL_ADC_PollForConversion(ADC_HandleTypeDef *handle, uint32_t timeout) /* 等待阶段可以被停止或 ADC 故障打断。 */
{
    (void)handle; /* 不访问实际 ADC。 */
    assert(timeout == 20); /* 核查真实固件超时设置。 */
    HAL_Delay(1); /* 用一毫秒推进模拟转换，并支持期间注入停止。 */
    return injected_failure(3) ? HAL_ERROR : HAL_OK; /* 模拟转换等待失败或成功。 */
}
static uint32_t HAL_ADC_GetValue(ADC_HandleTypeDef *handle) /* 为真实换算和判别提供合成 ADC 原码。 */
{
    int millivolts = selected_channel == ADC_CHANNEL_0 ? sample_vb_mv : sample_va_mv; /* 按通道取当前工况的输入。 */
    (void)handle; /* 主机无 ADC 寄存器。 */
    ++adc_reads; /* 记录发生了多少次真实逻辑的 GetValue 调用。 */
    if (injected_failure(5)) return DIV_ADC_MAX_CODE + 1; /* 模拟返回越界原码。 */
    return (millivolts * DIV_ADC_MAX_CODE + DIV_ADC_REFERENCE_MV / 2) / DIV_ADC_REFERENCE_MV; /* 产生与输入对应的 12 位原码。 */
}
static int HAL_ADC_Stop(ADC_HandleTypeDef *handle) {(void)handle; return injected_failure(4) ? HAL_ERROR : HAL_OK;} /* 模拟停止失败。 */
static int HAL_UART_Transmit(UART_HandleTypeDef *handle, uint8_t *data, uint16_t length, uint32_t timeout) /* 保存真实函数格式化的报告。 */
{
    (void)handle; (void)timeout; /* UART 硬件和发送超时不参与供电模型。 */
    assert(length < sizeof(last_report)); /* 检查实际报告长度。 */
    memcpy(last_report, data, length); /* 保存发送内容供行为断言检查。 */
    last_report[length] = '\0'; /* 结束字符串。 */
    ++reports; /* 统计检测和停止事件报告。 */
    return HAL_OK; /* 本测试默认串口成功。 */
}
static void Error_Handler(void) {abort();} /* 意外进入不可恢复错误时使行为测试失败。 */
#include "实际固件逻辑.inc" /* 编译从工程原样提取的控制、采样和报告函数。 */

static void reset_case(int vb, int va) /* 每个测试从一次新的上电状态开始。 */
{
    tick_ms = outputs = interrupt_mask = selected_channel = last_off_ms = 0; /* 清空硬件替身。 */
    stop_level = retest_level = 1; /* 两只操作按钮默认松开。 */
    stop_at_ms = -1; /* 默认不注入停止。 */
    failure_stage = failure_channel = -1; /* 默认 ADC 各阶段都成功。 */
    adc_reads = reports = pending_interrupt = 0; /* 清空行为计数。 */
    last_report[0] = '\0'; /* 清空串口内容。 */
    sample_vb_mv = vb; sample_va_mv = va; /* 设置本测试的两点输入。 */
    power_gpio_ready = stop_requested = stop_reported = 0; /* 将真实固件状态恢复为上电初值。 */
    detection_pending = 1; /* 上电安排一次真实检测。 */
    retest_button.raw_level = retest_button.stable_level = GPIO_PIN_SET; /* 初始化复测按钮未按下状态。 */
    retest_button.changed_ms = 0; /* 初始化消抖时间。 */
    MX_GPIO_Init(); /* 运行真实的 GPIO 初始化代码。 */
    assert(outputs == 0); /* 启动时两路都必须关闭。 */
    assert(output_configuration.Pin == (GPIO_PIN_12 | GPIO_PIN_13) && output_configuration.Mode == GPIO_MODE_OUTPUT_PP); /* 两个控制引脚应为推挽输出。 */
    assert(stop_configuration.Mode == GPIO_MODE_IT_FALLING && stop_configuration.Pull == GPIO_PULLUP); /* 停止应为下降沿中断和上拉输入。 */
}

int main(void) /* 覆盖正常、八种故障、未知、ADC 错误、停止和复测行为。 */
{
    const int samples[9][2] = {{454,909},{0,1000},{999,1000},{833,833},{0,833},{588,882},{312,937},{294,882},{625,937}}; /* 合成输入选取用户电压表读数，不作为实测记录。 */
    int index, stage, channel, previous_reads, previous_reports; /* 保存测试循环和保持运行时的计数。 */
    for (index = 0; index < 9; ++index) /* 九种工况分别通过真实 ADC 换算和区间判别。 */
    {
        char expected[24]; /* 保存当前预期编号。 */
        reset_case(samples[index][0], samples[index][1]); /* 模拟当前工况的上电。 */
        ServiceControls(); /* 执行真实的一次检测。 */
        snprintf(expected, sizeof(expected), "STATE=DIV%d ", index); /* 按工况编号构造断言。 */
        assert(strstr(last_report, expected)); /* 实际逻辑必须判别到对应编号。 */
        assert(strstr(last_report, "FEATURE_READS=2 ADC_CONVERSIONS=2")); /* 成功检测应读取两个节点并进行两次转换。 */
        assert(outputs == (index == 0 ? GPIO_PIN_13 : 0)); /* 正常只开运行电源，八种故障两路都关闭。 */
        assert(strstr(last_report, index == 0 ? "RUN_POWER=ON TEST_POWER=OFF" : "RUN_POWER=OFF TEST_POWER=OFF")); /* 核查报告与输出电平一致。 */
        previous_reads = adc_reads; previous_reports = reports; /* 保存本次检测后的计数。 */
        HAL_Delay(500); ServiceControls(); /* 经过旧循环周期后再次处理控制。 */
        assert(adc_reads == previous_reads && reports == previous_reports); /* 无复测请求时不能再次采样或重复检测报告。 */
        printf("PASS DIV%d: correct classification, interlock and no automatic resample\n", index); /* 输出九工况行为测试结果。 */
    }
    reset_case(700,700); ServiceControls(); /* 使用不属于任何区间的未知输入。 */
    assert(outputs == 0 && strstr(last_report,"STATE=UNKNOWN")); /* 未知输入不得进入运行。 */
    puts("PASS unknown input keeps both power switches off"); /* 输出未知输入验证结果。 */
    for (channel = 0; channel < 2; ++channel) /* 覆盖 VB 与 VA 两个 ADC 通道。 */
    {
        for (stage = 1; stage <= 5; ++stage) /* 覆盖配置、启动、等待、停止和越界五类错误。 */
        {
            reset_case(454,909); failure_stage = stage; failure_channel = channel; /* 指定本次错误位置。 */
            ServiceControls(); /* 执行真实错误处理。 */
            assert(outputs == 0 && strstr(last_report,"STATE=UNKNOWN") && !strstr(last_report,"ERROR=OK")); /* ADC 错误必须明确报告且双路关闭。 */
        }
    }
    puts("PASS 10 ADC error paths keep both power switches off"); /* 输出错误路径验证结果。 */
    for (index = 1; index <= 33; ++index) /* 在互锁、稳定、ADC 与正常合闸阶段逐毫秒注入停止。 */
    {
        reset_case(454,909); stop_at_ms = index; /* 安排停止发生的时刻。 */
        ServiceControls(); /* 运行真实检测与停止逻辑。 */
        if (stop_at_ms >= 0) HAL_Delay(35); /* 晚于检测结束的停止也应立即关闭已开启的运行电源。 */
        assert(outputs == 0 && stop_requested); /* 无论阶段如何，最终都必须断电并锁存停止。 */
    }
    puts("PASS stop injection at 33 time boundaries"); /* 输出停止时序验证结果。 */
    reset_case(454,909); stop_level = 0; ServiceControls(); /* 模拟上电时已按住停止。 */
    assert(adc_reads == 0 && outputs == 0); /* 不能执行自动检测或开启测试电源。 */
    stop_level = 1; HAL_Delay(50); ServiceControls(); /* 松开停止，等待主循环处理。 */
    assert(adc_reads == 0 && outputs == 0); /* 仅松开停止不能恢复供电。 */
    retest_level = 0; ServiceControls(); HAL_Delay(20); ServiceControls(); /* 用户明确按复测并通过消抖。 */
    assert(adc_reads == 2 && outputs == GPIO_PIN_13); /* 复测解除锁存，正常后重新开启运行。 */
    puts("PASS held STOP at boot, latched stop, and explicit retest recovery"); /* 输出上电和停止恢复验证结果。 */
    reset_case(454,909); ServiceControls(); /* 先正常进入运行。 */
    sample_vb_mv = 0; sample_va_mv = 833; /* 把电路切换为 R2 短路输入。 */
    retest_level = 0; ServiceControls(); HAL_Delay(5); /* 复测按钮产生一个短暂低电平。 */
    retest_level = 1; ServiceControls(); HAL_Delay(20); ServiceControls(); /* 松开形成不到 20 ms 的抖动。 */
    assert(adc_reads == 2); /* 抖动不能触发新检测。 */
    retest_level = 0; ServiceControls(); HAL_Delay(20); ServiceControls(); /* 再次按下并稳定 20 ms。 */
    assert(adc_reads == 4 && outputs == 0 && strstr(last_report,"STATE=DIV4")); /* 从运行进入复测必须在 1 V 下识别故障并关闭运行。 */
    HAL_Delay(100); ServiceControls(); /* 持续按住复测。 */
    assert(adc_reads == 4); /* 持续按住不能产生第二次检测。 */
    puts("PASS run-to-fault retest, debounce and held-button single trigger"); /* 输出复测行为验证结果。 */
    reset_case(454,909); power_gpio_ready = 0; DivEmergencyStop(); /* 模拟初始化之前异常发生。 */
    assert(outputs == 0 && stop_requested); /* 不访问未准备好的 GPIO，硬件应靠下拉保持关闭。 */
    puts("PASS emergency stop before GPIO initialization"); /* 输出启动边界验证结果。 */
    puts("ALL BEHAVIOR TESTS PASSED; HOST HAL MOCKS, NOT PROTEUS MEASUREMENTS"); /* 明确区分主机逻辑验证和电路仿真实测。 */
    return 0; /* 测试全部成功。 */
}
