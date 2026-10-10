#ifndef DISPLAY_H /* 判断头文件保护标记是否已定义。 */
#define DISPLAY_H /* 防止同一头文件被重复展开。 */

#include "main.h" /* 提供 uint8_t 和 STM32 HAL/GPIO 定义。 */

void Display_TimerTick(void); /* 从 TIM2 中断通知显示模块刷新节拍到达。 */
void Display_Task(uint8_t num); /* 主循环调用此函数，按 num 刷新显示。 */

#endif /* 结束头文件保护。 */

