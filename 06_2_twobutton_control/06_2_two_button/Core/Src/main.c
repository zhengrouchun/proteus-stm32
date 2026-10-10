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
#include "main.h" /* 引入 HAL 类型和本工程引脚定义。 */
#include "tim.h" /* 引入 TIM2 初始化函数和 htim2。 */
#include "gpio.h" /* 引入 GPIO 初始化函数。 */

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "display.h" /* 引入数码管刷新接口。 */
#include "button.h" /* 引入按键读取和消抖接口。 */

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
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void); /* 声明系统时钟配置函数。 */
/* USER CODE BEGIN PFP */
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void) /* 程序入口，初始化硬件后循环处理按键和显示。 */
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init(); /* 初始化 HAL 和系统毫秒时钟。 */

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config(); /* 配置系统时钟为内部 8 MHz。 */

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init(); /* 初始化数码管输出和两个按键的中断输入。 */
  MX_TIM2_Init(); /* 配置 TIM2 每 1 ms 产生更新中断。 */
  /* USER CODE BEGIN 2 */
  uint8_t number = 0; /* 当前显示数字，范围为 0 到 99，上电显示 00。 */
  uint8_t key; /* 本次按键编号：0 无按键，1 加一，2 减一。 */

  if (HAL_TIM_Base_Start_IT(&htim2) != HAL_OK) /* 启动 TIM2 的 1 ms 中断，用于显示刷新和按键消抖。 */
  {
    Error_Handler(); /* 如果定时器启动失败，进入错误处理。 */
  }
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1) /* 不断读取按键并处理数码管刷新。 */
  {
    key = buttonflag_get(); /* 取出并清除本次按键，防止同一次按下重复计数。 */

    if (key == 1) /* 按钮一按下一次，数字加一。 */
    {
      if (number == 99) /* 当前数字为 99 时，再加一需要回到 0。 */
      {
        number = 0; /* 实现 99 再加一显示 00。 */
      }
      else /* 当前数字为 0 到 98。 */
      {
        number++; /* 显示数字加一。 */
      }
    }
    else if (key == 2) /* 按钮二按下一次，数字减一。 */
    {
      if (number == 0) /* 当前数字为 0 时，再减一需要回到 99。 */
      {
        number = 99; /* 实现 00 再减一显示 99。 */
      }
      else /* 当前数字为 1 到 99。 */
      {
        number--; /* 显示数字减一。 */
      }
    }

    Display_Task(number); /* 显示模块按 TIM2 刷新标志交替显示十位和个位。 */
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void) /* 设置芯片系统时钟和总线时钟。 */
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0}; /* 清零振荡器配置结构。 */
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0}; /* 清零总线时钟配置结构。 */

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI; /* 使用内部高速振荡器。 */
  RCC_OscInitStruct.HSIState = RCC_HSI_ON; /* 开启内部高速振荡器。 */
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT; /* 使用默认 HSI 校准值。 */
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE; /* 不使用 PLL 倍频。 */
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) /* 配置振荡器并检查是否成功。 */
  {
    Error_Handler(); /* 配置失败时进入错误处理。 */
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2; /* 选择需要配置的系统、AHB 和两条 APB 时钟。 */
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI; /* 系统时钟来源选择 8 MHz HSI。 */
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1; /* AHB 总线不分频。 */
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1; /* APB1 和 TIM2 时钟保持 8 MHz。 */
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1; /* APB2 总线不分频。 */

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK) /* 应用总线时钟配置并检查结果。 */
  {
    Error_Handler(); /* 配置失败时进入错误处理。 */
  }
}

/* USER CODE BEGIN 4 */
/* TIM2 每 1 ms 进入回调，完成按键消抖延时并请求显示刷新。 */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) /* 定时器更新中断回调，htim 指向触发中断的定时器。 */
{
  /* 只处理 TIM2 中断，不响应其他定时器。 */
  if (htim->Instance == TIM2) /* 仅处理本工程的 TIM2 更新中断。 */
  {
    Button_TimerTick(); /* 递减按键消抖时间，由中断完成延时。 */
    Display_TimerTick(); /* 请求数码管刷新一位，不改变 number。 */
  }
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void) /* 初始化失败时进入此函数。 */
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq(); /* 停止中断，避免失败后继续处理业务。 */
  while (1) /* 停在这里，便于定位初始化失败。 */
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
void assert_failed(uint8_t *file, uint32_t line) /* 启用完整断言时，接收出错文件名和行号。 */
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
