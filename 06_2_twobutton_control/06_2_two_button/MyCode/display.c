#include "display.h" /* 引入显示模块接口和 GPIO 定义。 */

/* 共阳数码管数字 0 到 9 的段码，位序为 A、B、C、D、E、F、G、DP。 */
static const uint8_t duan[10] =
{
  0xC0, 0xF9, 0xA4, 0xB0, 0x99, /* 依次对应数字 0 到 4。 */
  0x92, 0x82, 0xF8, 0x80, 0x90  /* 依次对应数字 5 到 9。 */
};

/* 保存 TIM2 是否请求了显示刷新。 */
static volatile uint8_t display_update_flag = 0;
/* 保存当前扫描位：0 是十位，1 是个位。 */
static uint8_t display_index = 0;

/* 本文件内部函数：根据 num 刷新一位数码管。 */
static void Display_Scan(uint8_t num)
{
  /* digit 保存本次要显示的十位或个位数字。 */
  uint8_t digit;
  /* code 保存 digit 对应的段码。 */
  uint8_t code;

  /* 先关闭十位，避免切换段码时出现重影。 */
  HAL_GPIO_WritePin(B1_GPIO_Port, B1_Pin, GPIO_PIN_RESET);
  /* 再关闭个位，避免切换段码时出现重影。 */
  HAL_GPIO_WritePin(B2_GPIO_Port, B2_Pin, GPIO_PIN_RESET);

  /* 共阳数码管高电平熄灭，所以先关闭 A 到 DP 的全部段。 */
  HAL_GPIO_WritePin(A_GPIO_Port, A_Pin | B_Pin | C_Pin | D_Pin |
                    E_Pin | F_Pin | G_Pin | DP_Pin, GPIO_PIN_SET);

  /* display_index 为 0 时取当前数值的十位。 */
  if (display_index == 0)
  {
    digit = num / 10; /* 整数除以 10 得到十位。 */
  }
  /* display_index 为 1 时取当前数值的个位。 */
  else
  {
    digit = num % 10; /* 除以 10 的余数得到个位。 */
  }

  code = duan[digit]; /* 使用 digit 作为下标查找段码。 */

  /* 段码 bit0 控制 A 段，0 点亮，1 熄灭。 */
  HAL_GPIO_WritePin(A_GPIO_Port, A_Pin, (code & 0x01) ? GPIO_PIN_SET : GPIO_PIN_RESET);
  /* 段码 bit1 控制 B 段，0 点亮，1 熄灭。 */
  HAL_GPIO_WritePin(B_GPIO_Port, B_Pin, (code & 0x02) ? GPIO_PIN_SET : GPIO_PIN_RESET);
  /* 段码 bit2 控制 C 段，0 点亮，1 熄灭。 */
  HAL_GPIO_WritePin(C_GPIO_Port, C_Pin, (code & 0x04) ? GPIO_PIN_SET : GPIO_PIN_RESET);
  /* 段码 bit3 控制 D 段，0 点亮，1 熄灭。 */
  HAL_GPIO_WritePin(D_GPIO_Port, D_Pin, (code & 0x08) ? GPIO_PIN_SET : GPIO_PIN_RESET);
  /* 段码 bit4 控制 E 段，0 点亮，1 熄灭。 */
  HAL_GPIO_WritePin(E_GPIO_Port, E_Pin, (code & 0x10) ? GPIO_PIN_SET : GPIO_PIN_RESET);
  /* 段码 bit5 控制 F 段，0 点亮，1 熄灭。 */
  HAL_GPIO_WritePin(F_GPIO_Port, F_Pin, (code & 0x20) ? GPIO_PIN_SET : GPIO_PIN_RESET);
  /* 段码 bit6 控制 G 段，0 点亮，1 熄灭。 */
  HAL_GPIO_WritePin(G_GPIO_Port, G_Pin, (code & 0x40) ? GPIO_PIN_SET : GPIO_PIN_RESET);
  /* 段码 bit7 控制小数点，0 点亮，1 熄灭。 */
  HAL_GPIO_WritePin(DP_GPIO_Port, DP_Pin, (code & 0x80) ? GPIO_PIN_SET : GPIO_PIN_RESET);

  /* 扫描十位时打开 B1，并把下一次扫描位设为个位。 */
  if (display_index == 0)
  {
    HAL_GPIO_WritePin(B1_GPIO_Port, B1_Pin, GPIO_PIN_SET); /* 打开十位。 */
    HAL_GPIO_WritePin(B2_GPIO_Port, B2_Pin, GPIO_PIN_RESET); /* 关闭个位。 */
    display_index = 1; /* 下一次扫描个位。 */
  }
  /* 扫描个位时打开 B2，并把下一次扫描位设为十位。 */
  else
  {
    HAL_GPIO_WritePin(B1_GPIO_Port, B1_Pin, GPIO_PIN_RESET); /* 关闭十位。 */
    HAL_GPIO_WritePin(B2_GPIO_Port, B2_Pin, GPIO_PIN_SET); /* 打开个位。 */
    display_index = 0; /* 下一次扫描十位。 */
  }
}

/* 由 TIM2 中断调用，记录一个显示刷新节拍。 */
void Display_TimerTick(void)
{
  display_update_flag = 1; /* 请求主循环刷新一位数码管。 */
}

/* 由主循环调用，有刷新请求时才执行一次扫描。 */
void Display_Task(uint8_t num)
{
  /* 检查 TIM2 是否请求显示刷新。 */
  if (display_update_flag)
  {
    display_update_flag = 0; /* 清除当前刷新请求。 */
    Display_Scan(num); /* 按当前数值刷新一位。 */
  }
}
