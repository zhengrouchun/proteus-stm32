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
/* Bit 0: LED1 on; bit 1: LED2 on. Updated by TIM2, read by main. */
static volatile uint8_t led_target_mask = 0;

  /* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
  /* USER CODE BEGIN 0 */
static void LedControl_Apply(void)
{
  static uint8_t last_mask = 0xFF;
  uint8_t mask = led_target_mask;

  if (mask == last_mask)
  {
    return;
  }

  /* Both LEDs are wired to VDD: a low GPIO level turns an LED on. */
  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1,
                    (mask & 0x01U) ? GPIO_PIN_RESET : GPIO_PIN_SET);
  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_2,
                    (mask & 0x02U) ? GPIO_PIN_RESET : GPIO_PIN_SET);
  last_mask = mask;
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  static uint8_t candidate = 1U;
  static uint8_t stable = 1U;
  static uint8_t stable_ms = 0U;
  static uint8_t valid_press = 0U;
  static uint8_t mode = 0U;       /* 0: off, 1: together, 2: alternating */
  static uint8_t phase = 0U;
  static uint16_t blink_ms = 0U;
  uint8_t released;

  if (htim->Instance != TIM2)
  {
    return;
  }

  released = (HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_0) == GPIO_PIN_SET) ? 1U : 0U;

  /* Require 20 consecutive equal 1 ms samples before accepting an edge. */
  if (released != candidate)
  {
    candidate = released;
    stable_ms = 1U;
  }
  else if (stable_ms < 20U)
  {
    stable_ms++;
  }

  if ((stable_ms == 20U) && (candidate != stable))
  {
    stable = candidate;
    if (stable == 0U)
    {
      valid_press = 1U;
    }
    else if (valid_press != 0U)
    {
      valid_press = 0U;
      mode = (mode == 1U) ? 2U : 1U;
      phase = 0U;
      blink_ms = 0U;
    }
  }

  if (++blink_ms >= 200U)
  {
    blink_ms = 0U;
    phase ^= 1U;
  }

  /* Blank immediately on a low sample and until release is debounced. */
  if ((released == 0U) || (candidate == 0U) || (stable == 0U))
  {
    led_target_mask = 0U;
  }
  else if (mode == 1U)
  {
    led_target_mask = (phase == 0U) ? 0x03U : 0U;
  }
  else if (mode == 2U)
  {
    led_target_mask = (phase == 0U) ? 0x01U : 0x02U;
  }
  else
  {
    led_target_mask = 0U;
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
  /* Keep both LEDs off before the first complete press and release. */
HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1 | GPIO_PIN_2, GPIO_PIN_SET);
  HAL_TIM_Base_Start_IT(&htim2);
  /* USER CODE END 2 */

  /* Infinite loop */
/* USER CODE BEGIN WHILE */
  while (1)
  {
#if 0 /* Previous button/LED experiment; superseded by LedControl_Apply. */
        GPIO_PinState key = HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_0);

    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1 | GPIO_PIN_2,
                      key == GPIO_PIN_RESET
                          ? GPIO_PIN_RESET
                          : GPIO_PIN_SET);
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
 #endif
    LedControl_Apply();
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
