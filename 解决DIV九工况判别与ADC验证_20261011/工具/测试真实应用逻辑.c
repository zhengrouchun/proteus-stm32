/* PC 故障注入测试：使用从交付 main.c 原样提取的 USER CODE；模拟输入不是 Proteus 实测。 */
#include <stdint.h> /* 提供与 STM32 一致的整数宽度。 */
#include <stdio.h> /* 为被测报告提供 snprintf。 */
#include <string.h> /* 保存串口输出供 Python 断言。 */
#include <setjmp.h> /* 模拟 Error_Handler 停机而不让测试进程死循环。 */
#include "div_diagnosis.h" /* 直接编译交付工程的真实换算和判别函数。 */

typedef struct { uint32_t Channel; uint32_t Rank; uint32_t SamplingTime; } ADC_ChannelConfTypeDef; /* 只模拟采样函数使用的配置字段。 */
#define ADC_REGULAR_RANK_1 1 /* 测试中用一表示第一序列位置。 */
#define ADC_SAMPLETIME_239CYCLES_5 239 /* 仅用于断言已选择指定采样配置，不模拟电气时间。 */
#define ADC_CHANNEL_0 0 /* 模拟 VB 输入通道。 */
#define ADC_CHANNEL_1 1 /* 模拟 VA 输入通道。 */
#define HAL_OK 0 /* 模拟 HAL 成功状态。 */
static int hadc1; /* 占位句柄，PC 不访问真实 ADC 寄存器。 */
static int huart1; /* 占位串口句柄。 */
static uint32_t test_values[2]; /* 两个由测试显式给定的合成原码。 */
static int selected_channel; /* 记录被测代码切换到哪个输入。 */
static int fail_stage; /* 故障注入阶段：零无故障，一配置，二启动，三等待，四停止。 */
static int fail_channel; /* 指定故障出现在 VB 或 VA。 */
static uint32_t fake_tick; /* PC 合成节拍，只验证计时位置。 */
static char captured[512]; /* 保存被测 SendReport 实际形成的输出。 */
static jmp_buf halt_return; /* Error_Handler 跳回测试入口。 */
static int stopped; /* 记录采样链有几次尝试停止 ADC。 */

static int stage_status(int stage) /* 根据测试设置返回当前 HAL 调用的结果。 */
{
    return fail_stage == stage && fail_channel == selected_channel ? 1 : HAL_OK; /* 只对选定阶段、选定通道注入失败。 */
}
static int HAL_ADC_ConfigChannel(int *handle, ADC_ChannelConfTypeDef *config) /* 替代配置外设的动作。 */
{
    (void)handle; /* PC 不需要真实句柄内容。 */
    selected_channel = (int)config->Channel; /* 保存实际请求通道以检验 PA0/PA1 顺序。 */
    if (config->Rank != ADC_REGULAR_RANK_1 || config->SamplingTime != ADC_SAMPLETIME_239CYCLES_5) return 1; /* 配置不符即失败。 */
    return stage_status(1); /* 可注入通道配置错误。 */
}
static int HAL_ADC_Start(int *handle) /* 替代软件启动动作。 */
{
    (void)handle; /* 明确忽略模拟句柄。 */
    return stage_status(2); /* 可注入启动失败。 */
}
static int HAL_ADC_PollForConversion(int *handle, uint32_t timeout) /* 替代等待硬件完成动作。 */
{
    (void)handle; (void)timeout; /* 不做真实等待，此处只验证错误处理。 */
    return stage_status(3); /* 可注入超时或转换错误。 */
}
static uint32_t HAL_ADC_GetValue(int *handle) /* 为应用提供显式的测试夹具值。 */
{
    (void)handle; /* 不读取硬件寄存器。 */
    return test_values[selected_channel]; /* 由应用选中的通道决定返回值，测试标签不进入判别函数。 */
}
static int HAL_ADC_Stop(int *handle) /* 模拟转换结束后的清理。 */
{
    (void)handle; /* 不读取句柄。 */
    ++stopped; /* 断言成功或超时后是否确实调用停止。 */
    return stage_status(4); /* 可注入停止失败。 */
}
static uint32_t HAL_GetTick(void) /* 返回可控制的合成毫秒数。 */
{
    uint32_t value = fake_tick; /* 保存这一调用读到的计数器。 */
    fake_tick += 7; /* 下一次计时调用相隔七毫秒，含回绕测试。 */
    return value; /* 将读到的旧值返回给被测逻辑。 */
}
static int HAL_UART_Transmit(int *handle, uint8_t *text, uint16_t size, uint32_t timeout) /* 捕获实际格式化文本。 */
{
    (void)handle; (void)timeout; /* 不使用真实串口或串口超时。 */
    memcpy(captured, text, size); /* 按被测代码给出的长度保存输出。 */
    captured[size] = '\0'; /* 补上 C 字符串结束符便于读取。 */
    fake_tick += 50; /* 模拟发送开销，检查它不会进入之前测得的检测耗时。 */
    return HAL_OK; /* 本测试让串口发送成功。 */
}
static void Error_Handler(void) /* 替代固件中的永久停机。 */
{
    longjmp(halt_return, 1); /* 跳回入口，保留已捕获的错误报告。 */
}
#include "被测应用_USER_CODE.inc" /* 此文件由测试脚本从最终 main.c 原样提取，避免手抄应用逻辑。 */

__declspec(dllexport) int TestClassify(int32_t vb, int32_t va) /* 暴露真实 C 判别给 Python。 */
{
    return DivClassify(vb, va); /* 不使用 Python 重写的算法代替被测代码。 */
}
__declspec(dllexport) uint32_t TestConvert(uint32_t raw) /* 暴露真实 C 电压换算。 */
{
    return DivCodeToMillivolts(raw); /* 使用固件同一函数。 */
}
__declspec(dllexport) const char *TestRun(uint32_t vb, uint32_t va, int stage, int channel, uint32_t tick) /* 执行一次实际应用检测逻辑。 */
{
    test_values[0] = vb; test_values[1] = va; /* 设置两个独立节点的合成原码。 */
    fail_stage = stage; fail_channel = channel; /* 设置本轮是否注入指定错误。 */
    selected_channel = 0; fake_tick = tick; stopped = 0; captured[0] = '\0'; /* 重置测试环境，避免跨轮污染。 */
    if (setjmp(halt_return) == 0) RunDivDetection(); /* 首次执行被测检测，错误停机后回到此处继续核查。 */
    return captured; /* 返回应用实际形成的串口文本。 */
}
__declspec(dllexport) int TestStopCalls(void) /* 暴露停止调用次数。 */
{
    return stopped; /* 供错误路径断言使用。 */
}
