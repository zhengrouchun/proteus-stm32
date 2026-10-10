/* 解决九工况判别缺失：只根据实测电压匹配参数 2.0，不接收故障开关或预设标签。 */
#ifndef DIV_DIAGNOSIS_H /* 防止本头文件被重复包含。 */
#define DIV_DIAGNOSIS_H /* 标记本头文件已经包含。 */
#include <stdint.h> /* 引入固定位宽整数，确保 PC 检查与 STM32 使用相同数值类型。 */

#define DIV_ADC_REFERENCE_MV 3300 /* ADC 参考电压假定为 3300 mV，必须用实际 VDDA 和已知输入核验。 */
#define DIV_ADC_MAX_CODE 4095 /* 12 位右对齐 ADC 的最大原码。 */
#define DIV_ADC_ROUNDING_BIAS (DIV_ADC_MAX_CODE / 2) /* 整数除法前加入半个除数，实现四舍五入到 mV。 */
#define DIV_CASE_COUNT 9 /* 本阶段只有 DIV0 至 DIV8。 */
#define DIV_UNKNOWN (-1) /* 负一表示无唯一匹配，不能把它当成工况编号。 */

typedef struct /* 描述一个工况的二维闭区间。 */
{
    int32_t vb_min; /* VB 最小允许电压，保留 -5 mV 的有符号下界。 */
    int32_t vb_max; /* VB 最大允许电压，单位 mV。 */
    int32_t va_min; /* VA 最小允许电压，单位 mV。 */
    int32_t va_max; /* VA 最大允许电压，单位 mV。 */
} DivBounds; /* 给区间结构起一个有意义的类型名。 */

static const DivBounds div_bounds[DIV_CASE_COUNT] = /* 逐项来自原始 特征区间_v2.csv 的 DIV 行。 */
{
    {422, 488, 889, 928}, /* DIV0：正常，必须两点同时满足。 */
    {-5, 5, 985, 1015}, /* DIV1：R1 断路。 */
    {985, 1015, 985, 1015}, /* DIV2：R2 断路。 */
    {811, 855, 811, 855}, /* DIV3：R1 短路。 */
    {-5, 5, 811, 855}, /* DIV4：R2 短路。 */
    {555, 621, 862, 903}, /* DIV5：R1 改成 5 kOhm。 */
    {284, 342, 919, 956}, /* DIV6：R1 改成 20 kOhm。 */
    {267, 322, 862, 903}, /* DIV7：R2 改成 5 kOhm。 */
    {591, 659, 919, 956} /* DIV8：R2 改成 20 kOhm。 */
};

static uint32_t DivCodeToMillivolts(uint32_t raw) /* 输入已检查为 0 至 4095 的真实 ADC 原码。 */
{
    return (raw * DIV_ADC_REFERENCE_MV + DIV_ADC_ROUNDING_BIAS) / DIV_ADC_MAX_CODE; /* 原码按参考电压缩放并取整。 */
}

static int DivClassify(int32_t vb_mv, int32_t va_mv) /* 使用带符号比较，避免 -5 被变成很大的无符号数。 */
{
    int matches = 0; /* 本次还没有匹配到任何工况。 */
    int matched_case = DIV_UNKNOWN; /* 在唯一匹配被证明前保持未知。 */
    int index; /* 遍历参数表的行号，不是外部指定的故障标签。 */
    for (index = 0; index < DIV_CASE_COUNT; ++index) /* 检查全部九组，避免找到首个匹配就提前接受。 */
    {
        const DivBounds *bounds = &div_bounds[index]; /* 取得当前行的上下界。 */
        if (vb_mv >= bounds->vb_min && vb_mv <= bounds->vb_max && /* VB 必须在当前工况闭区间内。 */
            va_mv >= bounds->va_min && va_mv <= bounds->va_max) /* VA 也必须在同一工况闭区间内。 */
        {
            ++matches; /* 记录命中数量，用于拒绝多重匹配。 */
            matched_case = index; /* 暂存匹配的编号。 */
        }
    }
    return matches == 1 ? matched_case : DIV_UNKNOWN; /* 恰好一组匹配才返回 DIV 编号，其余返回未知。 */
}
#endif /* 结束重复包含保护。 */
