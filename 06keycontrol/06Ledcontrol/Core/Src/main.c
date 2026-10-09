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
/* 对应参考图的 keyflag：0 等待第一次松开，1 同步闪烁，2 交替闪烁。 */
static volatile uint8_t led_keyflag = 0;
/* TIM2 中断更新，主循环读取：按住时必须关灯。 */
static volatile uint8_t led_button_pressed = 0;
/* 0 为第一个 200 ms 相位，1 为第二个 200 ms 相位。 */
static volatile uint8_t led_blink_phase = 0;

  /* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
  /* USER CODE BEGIN 0 */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  /* 这些 static 变量在下一次 1 ms 中断到来时会保留原值。 */
  static GPIO_PinState last_sample = GPIO_PIN_SET;     /* 上一次采样电平 */
  static GPIO_PinState confirmed_level = GPIO_PIN_SET; /* 已消抖的电平 */
  static uint8_t same_sample_count = 0;                /* 连续相同次数 */
  static uint8_t valid_press_seen = 0;                 /* 是否已有有效按下 */
  static uint16_t blink_elapsed_ms = 0;                /* 当前相位经过时间 */
  GPIO_PinState button_level;                          /* 本次读到的按键电平 */

  /* HAL 可能把其他定时器也交给此回调；这里只处理 TIM2。 */
  if (htim->Instance != TIM2)
  {
    return;
  }

  /* PB0 有上拉：松开读到高电平，按下接地读到低电平。 */
  button_level = HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_0);

  /* 与上一毫秒不同就重新计数；相同就累计，最多计到 20。 */
  if (button_level != last_sample)
  {
    last_sample = button_level;
    same_sample_count = 1;
  }
  else if (same_sample_count < 20)
  {
    same_sample_count++;
  }

  /* 连续 20 个 1 ms 采样相同，才确认按下或松开。 */
if ((same_sample_count == 20) && (button_level != confirmed_level))
  {
    confirmed_level = button_level;
    if (confirmed_level == GPIO_PIN_RESET)
    {
      /* 按下只做记录，此时不切换闪烁方式。 */
      valid_press_seen = 1;
    }
    else if (valid_press_seen)
    {
      /* 参考图的 keyflag++：只在一次完整按下、松开后加一。 */
      valid_press_seen = 0;
      led_keyflag++;
      if (led_keyflag == 3)
      {
        led_keyflag = 1; /* 模式只在 1（同步）和 2（交替）之间循环。 */
      }
      led_blink_phase = 0; /* 新模式从第一个 200 ms 相位开始。 */
      blink_elapsed_ms = 0;
    }
  }

  /* 用 TIM2 累计 200 个 1 ms 中断，代替参考图的 HAL_Delay(200)。 */
  blink_elapsed_ms++;
  if (blink_elapsed_ms >= 200)
  {
    blink_elapsed_ms = 0;
    if (led_blink_phase == 0)
    {
      led_blink_phase = 1;
    }
    else
    {
      led_blink_phase = 0;
    }
  }

  /* 一读到按下就锁定关灯，触点短暂回弹也不会使 LED 闪亮。 */
  if (button_level == GPIO_PIN_RESET)
  {
    led_button_pressed = 1;
  }
  /* 只有连续 20 ms 读到松开，才解除关灯状态。 */
  else if ((confirmed_level == GPIO_PIN_SET) &&
           (same_sample_count == 20))
  {
    led_button_pressed = 0;
  }
}

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
  /* 上电时先把 PA1、PA2 输出高电平，确保第一次松开之前两灯都灭。 */
HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1 | GPIO_PIN_2, GPIO_PIN_SET);
  /* 启动 TIM2 更新中断，使上面的回调每约 1 ms 执行一次。 */
  HAL_TIM_Base_Start_IT(&htim2);
  /* USER CODE END 2 */

  /* Infinite loop */
/* USER CODE BEGIN WHILE */
  while (1)
  {
#if 0 /* 旧的按键/LED 实验代码暂停使用，避免覆盖定时器中断的输出。 */
        GPIO_PinState key = HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_0);

    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1 | GPIO_PIN_2,
                      key == GPIO_PIN_RESET
                          ? GPIO_PIN_RESET
                          : GPIO_PIN_SET);
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
#endif
    /* 按住按钮时两灯先灭；松开且完成消抖后再按模式闪烁。 */
    if (led_button_pressed != 0)
    {
      HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1 | GPIO_PIN_2, GPIO_PIN_SET);
    }
    else if (led_keyflag == 1)
    {
      /* 对应参考图 keyflag==1：两个灯同时亮、同时灭。 */
      if (led_blink_phase == 0)
      {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1 | GPIO_PIN_2, GPIO_PIN_RESET);
      }
      else
      {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1 | GPIO_PIN_2, GPIO_PIN_SET);
      }
    }
    else if (led_keyflag == 2)
    {
      /* 对应参考图 keyflag==2：两个灯交替亮。 */
      if (led_blink_phase == 0)
      {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, GPIO_PIN_RESET); /* LED1 亮 */
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_2, GPIO_PIN_SET);   /* LED2 灭 */
      }
      else
      {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, GPIO_PIN_SET);   /* LED1 灭 */
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_2, GPIO_PIN_RESET); /* LED2 亮 */
      }
    }
    else
    {
      /* 上电后还没有完成第一次按下松开：两灯保持熄灭。 */
      HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1 | GPIO_PIN_2, GPIO_PIN_SET);
    }
    /* 等待中断唤醒；TIM2 中断会更新按键状态和 200 ms 相位。 */
    __WFI();
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
