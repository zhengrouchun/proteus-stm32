/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "tim.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
uint8_t led_index = 0;//全局状态变量 led_index，记录当前应该点亮第几个LED：0~3 
/*
为什么这里一定推荐 volatile
因为：timer_ms不是只在普通程序里面变化。
它会在：HAL_TIM_PeriodElapsedCallback()
也就是中断回调函数里面被修改。
所以：volatile uint32_t timer_ms;
是在告诉编译器：
这个变量可能在你意想不到的时候被中断修改，所以每次使用时都重新读取真实值，不要自作聪明缓存或优化。*/
volatile uint32_t system_ms = 0;//整个程序从 TIM2 启动以后经过了多少毫秒。
volatile uint8_t led_update_flag = 0;//流水灯的500ms时间到了没有
volatile uint8_t display_update_flag = 0;
/* 当前应该显示哪一位：
   0 = 第一位
   1 = 第二位
为什么用 volatile？
因为：
中断函数
HAL_TIM_PeriodElapsedCallback()
        ↓
修改 display_update_flag

main()
        ↓
读取 display_update_flag
它是一个：中断与主程序共享的变量
所以：volatile告诉编译器：
这个变量可能突然被中断修改，每次都真正从内存读取，不要认为它一直没变。
*/
uint8_t display_index = 0;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
uint8_t Timer_Elapsed(uint32_t *last_time, uint32_t interval_ms);//检查指定时间到了没有。
void LED_Run(void);
void Display_Scan(void);
void display(uint16_t shu);
void display_clear(void);
void bitsel(uint16_t wei);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_TIM2_Init();
  /* USER CODE BEGIN 2 */
  HAL_TIM_Base_Start_IT(&htim2);//启动定时器，原因前面的GPIO 和 TIM2 都初始化完成了，才能正式启动 TIM2 中断。

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
//  //��һ������ʽ��ѯ������ˮ��
//  HAL_GPIO_WritePin(LED1_GPIO_Port,LED1_Pin,GPIO_PIN_RESET);
//  HAL_GPIO_WritePin(LED2_GPIO_Port,LED2_Pin,GPIO_PIN_SET);
//  HAL_GPIO_WritePin(LED3_GPIO_Port,LED3_Pin,GPIO_PIN_SET);
//  HAL_GPIO_WritePin(LED4_GPIO_Port,LED4_Pin,GPIO_PIN_SET);
//  HAL_Delay(500);
//  HAL_GPIO_WritePin(LED1_GPIO_Port,LED1_Pin,GPIO_PIN_SET);
//  HAL_GPIO_WritePin(LED2_GPIO_Port,LED2_Pin,GPIO_PIN_RESET);
//  HAL_GPIO_WritePin(LED3_GPIO_Port,LED3_Pin,GPIO_PIN_SET);
//  HAL_GPIO_WritePin(LED4_GPIO_Port,LED4_Pin,GPIO_PIN_SET);
//  HAL_Delay(500);
//  HAL_GPIO_WritePin(LED1_GPIO_Port,LED1_Pin,GPIO_PIN_SET);
//  HAL_GPIO_WritePin(LED2_GPIO_Port,LED2_Pin,GPIO_PIN_SET);
//  HAL_GPIO_WritePin(LED3_GPIO_Port,LED3_Pin,GPIO_PIN_RESET);
//  HAL_GPIO_WritePin(LED4_GPIO_Port,LED4_Pin,GPIO_PIN_SET);
//  HAL_Delay(500);
//  HAL_GPIO_WritePin(LED1_GPIO_Port,LED1_Pin,GPIO_PIN_SET);
//  HAL_GPIO_WritePin(LED2_GPIO_Port,LED2_Pin,GPIO_PIN_SET);
//  HAL_GPIO_WritePin(LED3_GPIO_Port,LED3_Pin,GPIO_PIN_SET);
//  HAL_GPIO_WritePin(LED4_GPIO_Port,LED4_Pin,GPIO_PIN_RESET);
//  HAL_Delay(500);
 
 //��������λȡ�� NOT

// // LED1���������� 
//    HAL_GPIO_WritePin(GPIOA, LED1_Pin | LED2_Pin | LED3_Pin | LED4_Pin,GPIO_PIN_SET);
//    HAL_GPIO_WritePin(GPIOA, LED1_Pin, GPIO_PIN_RESET);
//    HAL_Delay(500);
//    // LED2���������� 
//    HAL_GPIO_WritePin(GPIOA, LED1_Pin | LED2_Pin | LED3_Pin | LED4_Pin,GPIO_PIN_SET);
//    HAL_GPIO_WritePin(GPIOA, LED2_Pin, GPIO_PIN_RESET);
//    HAL_Delay(500);

//    // LED3���������� 
//    HAL_GPIO_WritePin(GPIOA,LED1_Pin | LED2_Pin | LED3_Pin | LED4_Pin, GPIO_PIN_SET);
//    HAL_GPIO_WritePin(GPIOA, LED3_Pin, GPIO_PIN_RESET);
//    HAL_Delay(500);


//    //LED4����������
//    HAL_GPIO_WritePin(GPIOA,LED1_Pin | LED2_Pin | LED3_Pin | LED4_Pin,GPIO_PIN_SET);
//    HAL_GPIO_WritePin(GPIOA, LED4_Pin, GPIO_PIN_RESET);
//    HAL_Delay(500);


/* ---------- 500ms流水灯任务 ---------- */
    if (led_update_flag)
    {
        led_update_flag = 0;
        LED_Run();
    }

    /* ---------- 1ms数码管扫描任务 ---------- */
    if (display_update_flag)
    {
        display_update_flag = 0;
        Display_Scan();
    }

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
//非阻塞方式延时
uint8_t Timer_Elapsed(uint32_t *last_time, uint32_t interval_ms)
{
    uint32_t now = system_ms;

    if ((uint32_t)(now - *last_time) >= interval_ms)
    {
        *last_time = now;

        return 1;
    }

    return 0;//未到时间，直接返回去做其他事情，不等待
  }
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    static uint16_t led_tick = 0;
/*
  第一次进入 TIM2 中断：led_tick = 0↓led_tick++↓1
退出中断以后，因为有：static
所以值不会消失。下一次进入：原来是1↓led_tick++↓2一直：1...500到了：500ms
执行：
led_tick = 0;
led_update_flag = 1;
于是：又从0开始计下一个500ms*/
    if (htim->Instance == TIM2)
    {
        /* 每进入一次TIM2中断，就代表经过1ms */
        system_ms++;
/* ==============================
           数码管任务
           每1ms刷新一次
           ============================== */
        display_update_flag = 1;

        /* 流水灯自己的计时器 */
        led_tick++;

        /* 每500ms通知主程序切换一次LED */
        if (led_tick >= 125)
        {
            led_tick = 0;

            led_update_flag = 1;
          /*没有直接调用：LED_Run();
          中断尽可能只负责计时、记录状态、设置标志，，然后马上退出。*/
        }
    }
}

void LED_Run(void)
{
    /* 先关闭全部LED */
    HAL_GPIO_WritePin(LED1_GPIO_Port, LED1_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(LED2_GPIO_Port, LED2_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(LED3_GPIO_Port, LED3_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(LED4_GPIO_Port, LED4_Pin, GPIO_PIN_SET);

    /* 根据led_index点亮对应LED */
    if (led_index == 0)
    {
        HAL_GPIO_WritePin(LED1_GPIO_Port, LED1_Pin, GPIO_PIN_RESET);
    }
    else if (led_index == 1)
    {
        HAL_GPIO_WritePin(LED2_GPIO_Port, LED2_Pin, GPIO_PIN_RESET);
    }
    else if (led_index == 2)
    {
        HAL_GPIO_WritePin(LED3_GPIO_Port, LED3_Pin, GPIO_PIN_RESET);
    }
    else if (led_index == 3)
    {
        HAL_GPIO_WritePin(LED4_GPIO_Port, LED4_Pin, GPIO_PIN_RESET);
    }

    /* 切换到下一个LED */
    led_index++;

    if (led_index >= 4)
    {
        led_index = 0;
    }
}
void Display_Scan(void)
{
    /* =================================================
       第一步：先关闭两个数码管
       ================================================= */

    HAL_GPIO_WritePin(B1_GPIO_Port, B1_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(B2_GPIO_Port, B2_Pin, GPIO_PIN_RESET);


    /* =================================================
       第二步：先关闭全部段
       
       因为你使用的是共阳极数码管：
       
       段选：
       SET   = 1 = 灭
       RESET = 0 = 亮
       
       所以这里全部写SET，相当于全部熄灭。
       ================================================= */

    HAL_GPIO_WritePin(A_GPIO_Port, A_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(B_GPIO_Port, B_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(B_GPIO_Port, C_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(D_GPIO_Port, D_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(E_GPIO_Port, E_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(F_GPIO_Port, F_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(G_GPIO_Port, G_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(DP_GPIO_Port, DP_Pin, GPIO_PIN_SET);


    /* =================================================
       第三步：根据 display_index 决定显示哪一位
       ================================================= */

    if (display_index == 0)
    {
        /* ---------- 第一位的段码 ---------- */

        HAL_GPIO_WritePin(A_GPIO_Port, A_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(B_GPIO_Port, B_Pin, GPIO_PIN_SET);
        HAL_GPIO_WritePin(B_GPIO_Port, C_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(D_GPIO_Port, D_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(E_GPIO_Port, E_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(F_GPIO_Port, F_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(G_GPIO_Port, G_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(DP_GPIO_Port, DP_Pin, GPIO_PIN_SET);

        /* 段码准备完成之后，再打开第一位 */
        HAL_GPIO_WritePin(B1_GPIO_Port, B1_Pin, GPIO_PIN_SET);
        HAL_GPIO_WritePin(B2_GPIO_Port, B2_Pin, GPIO_PIN_RESET);

        /* 下一次显示第二位 */
        display_index = 1;
    }
    else
    {
        /* ---------- 第二位的段码 ---------- */

        HAL_GPIO_WritePin(A_GPIO_Port, A_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(B_GPIO_Port, B_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(B_GPIO_Port, C_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(D_GPIO_Port, D_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(E_GPIO_Port, E_Pin, GPIO_PIN_SET);
        HAL_GPIO_WritePin(F_GPIO_Port, F_Pin, GPIO_PIN_SET);
        HAL_GPIO_WritePin(G_GPIO_Port, G_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(DP_GPIO_Port, DP_Pin, GPIO_PIN_SET);

        /* 段码准备完成之后，再打开第二位 */
        HAL_GPIO_WritePin(B1_GPIO_Port, B1_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(B2_GPIO_Port, B2_Pin, GPIO_PIN_SET);

        /* 下一次重新显示第一位 */
        display_index = 0;
    }
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
