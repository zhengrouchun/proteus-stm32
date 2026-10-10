#ifndef BUTTON_H /* 检查本头文件是否已经包含。 */
#define BUTTON_H /* 定义保护标记，防止重复包含。 */

#include "main.h" /* 提供 uint8_t、HAL 函数和两个按键的 GPIO 定义。 */

uint8_t buttonflag_get(void); /* 主循环调用：返回 0 无按键、1 按钮一、2 按钮二，读取后清空。 */
void Button_TimerTick(void); /* TIM2 每 1 ms 调用：递减两个按键的消抖时间。 */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin); /* GPIO 中断回调：识别触发引脚并记录按下事件。 */

#endif /* 结束头文件保护。 */
