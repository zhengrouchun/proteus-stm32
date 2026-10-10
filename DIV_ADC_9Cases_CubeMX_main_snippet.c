/*
 * DIV test v2.0: paste functions into main.c USER CODE BEGIN 0
 * CubeMX prerequisites: ADC1_IN0(PA0), ADC1_IN1(PA1), USART1_TX(PA9)
 * Configure ADC1 single conversion + software trigger, sampling 239.5 cycles.
 * USART1 115200, 8N1. VREF=3300 mV assumption must be verified.
 * This is a USER CODE SNIPPET, not a stand-alone project.
 */
#include <stdio.h>   /* put in USER CODE BEGIN Includes */

/* Paste the following between USER CODE BEGIN 0 / END 0 */
static uint16_t DIV_ReadADC(uint32_t ch)
{
    ADC_ChannelConfTypeDef s = {0};
    s.Channel = ch;
    s.Rank = ADC_REGULAR_RANK_1;
    s.SamplingTime = ADC_SAMPLETIME_239CYCLES_5;
    if (HAL_ADC_ConfigChannel(&hadc1, &s) != HAL_OK) Error_Handler();
    if (HAL_ADC_Start(&hadc1) != HAL_OK) Error_Handler();
    if (HAL_ADC_PollForConversion(&hadc1, 100) != HAL_OK) Error_Handler();
    uint16_t raw = (uint16_t)HAL_ADC_GetValue(&hadc1);
    HAL_ADC_Stop(&hadc1);
    return raw;
}

static uint32_t DIV_CodeToMv(uint16_t raw)
{
    /* 12-bit ADC, 0..4095; rounded to nearest millivolt */
    return ((uint32_t)raw * 3300U + 2047U) / 4095U;
}

/* Each row: VB min, VB max, VA min, VA max (mV). */
static const int16_t DIV_Bounds[9][4] = {
    { 422, 488, 889, 928 },  /* DIV0 */
    {  -5,   5, 985, 1015},  /* DIV1 */
    { 985,1015, 985, 1015},  /* DIV2 */
    { 811, 855, 811, 855 },  /* DIV3 */
    {  -5,   5, 811, 855 },  /* DIV4 */
    { 555, 621, 862, 903 },  /* DIV5 */
    { 284, 342, 919, 956 },  /* DIV6 */
    { 267, 322, 862, 903 },  /* DIV7 */
    { 591, 659, 919, 956 }   /* DIV8 */
};

static int DIV_Classify(uint32_t vb, uint32_t va)
{
    int hits = 0;
    int found = -1;
    for (int i = 0; i < 9; ++i) {
        if ((int32_t)vb >= DIV_Bounds[i][0] &&
            (int32_t)vb <= DIV_Bounds[i][1] &&
            (int32_t)va >= DIV_Bounds[i][2] &&
            (int32_t)va <= DIV_Bounds[i][3]) {
            ++hits;
            found = i;
        }
    }
    return (hits == 1) ? found : -1;
}

/* After generated MX_ADC1_Init(), call exactly once: */
/* if (HAL_ADCEx_Calibration_Start(&hadc1) != HAL_OK) Error_Handler(); */

/* Paste following statements inside while(1): */
/*
uint16_t code_vb = DIV_ReadADC(ADC_CHANNEL_0);
uint16_t code_va = DIV_ReadADC(ADC_CHANNEL_1);
uint32_t mv_vb = DIV_CodeToMv(code_vb);
uint32_t mv_va = DIV_CodeToMv(code_va);
int state = DIV_Classify(mv_vb, mv_va);
char state_text[16];
if (state >= 0) snprintf(state_text, sizeof(state_text), "DIV%d", state);
else snprintf(state_text, sizeof(state_text), "UNKNOWN");
char msg[128];
int n = snprintf(msg, sizeof(msg),
    "VB_RAW=%u VB_MV=%lu VA_RAW=%u VA_MV=%lu STATE=%s\r\n",
    (unsigned)code_vb, (unsigned long)mv_vb,
    (unsigned)code_va, (unsigned long)mv_va, state_text);
if (n > 0) {
    uint16_t send_n = (uint16_t)((n < (int)sizeof(msg)) ? n : (int)sizeof(msg)-1);
    HAL_UART_Transmit(&huart1, (uint8_t*)msg, send_n, 200);
}
HAL_Delay(800);
*/
