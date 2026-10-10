#include "button.h" /* 引入按键接口、GPIO 引脚和 HAL 定义。 */

/* ---------- 按键模块内部变量 ---------- */
static volatile uint8_t buttonflag = 0; /* 按键编号：0 无按键，1 按钮一，2 按钮二；中断修改，主循环读取。 */
static volatile uint8_t key1_delay = 0; /* 按钮一还需等待多少毫秒，0 表示可以接受新按下。 */
static volatile uint8_t key2_delay = 0; /* 按钮二还需等待多少毫秒，0 表示可以接受新按下。 */

/* ---------- 主循环读取一次按键 ---------- */
uint8_t buttonflag_get(void) /* 返回按键编号，返回类型保持为 uint8_t。 */
{
    uint32_t irq_state = __get_PRIMASK(); /* 保存读取前的全局中断状态。 */
    uint8_t key; /* 暂存本次取出的按键编号。 */

    __disable_irq(); /* 暂时关闭中断，保证取出和清空之间不会插入新按键。 */
    key = buttonflag; /* 取出中断记录的按键编号。 */
    buttonflag = 0; /* 清空编号，让同一次按下只处理一次。 */
    __set_PRIMASK(irq_state); /* 恢复读取前的中断状态。 */
    return key; /* 把 0、1 或 2 交给主循环。 */
}

/* ---------- TIM2 每 1 ms 调用一次，完成中断消抖延时 ---------- */
void Button_TimerTick(void) /* 只推进消抖时间，不改变显示数字。 */
{
    if (key1_delay > 0) /* 按钮一的消抖时间尚未结束。 */
    {
        key1_delay--; /* 减去 1 ms，到 0 后才接受新的按下。 */
    }
    if (key2_delay > 0) /* 按钮二的消抖时间尚未结束。 */
    {
        key2_delay--; /* 减去 1 ms，到 0 后才接受新的按下。 */
    }
}

/* ---------- GPIO 按下和松开中断：只记录按键，不等待松手 ---------- */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) /* GPIO_Pin 表示这次触发中断的引脚。 */
{
    if (GPIO_Pin == KEY1_Pin) /* 判断中断是否来自按钮一。 */
    {
        if ((key1_delay == 0) && (HAL_GPIO_ReadPin(KEY1_GPIO_Port, KEY1_Pin) == GPIO_PIN_RESET)) /* 消抖结束且电平为低，才认作按钮一按下。 */
        {
            buttonflag = 1; /* 记录按钮一，通知主循环加一。 */
        }
        key1_delay = 20; /* 按下或松开后都启动 20 ms 消抖，期间的弹跳不再计数。 */
    }
    else if (GPIO_Pin == KEY2_Pin) /* 判断中断是否来自按钮二。 */
    {
        if ((key2_delay == 0) && (HAL_GPIO_ReadPin(KEY2_GPIO_Port, KEY2_Pin) == GPIO_PIN_RESET)) /* 消抖结束且电平为低，才认作按钮二按下。 */
        {
            buttonflag = 2; /* 记录按钮二，通知主循环减一。 */
        }
        key2_delay = 20; /* 按下或松开后都启动 20 ms 消抖，期间的弹跳不再计数。 */
    }
}
