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

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>   /* snprintf 把数值组成可读的串口文本。 */
#include <string.h>  /* strlen 取得需要发送的文本长度。 */

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define ADC_REFERENCE_MILLIVOLTS 3300   /* VDDA 为 3.3 V，即 3300 mV。 */
#define ADC_MAXIMUM_CODE 4095           /* 12 位 ADC 的最大数字读数。 */
#define ADC_TIMEOUT_MILLISECONDS 20    /* 最多等待一次 ADC 转换 20 ms。 */
#define UART_TIMEOUT_MILLISECONDS 100  /* 最多等待串口发送 100 ms。 */
#define REPORT_PERIOD_MILLISECONDS 500 /* 两次报告之间等待 500 ms。 */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
ADC_HandleTypeDef hadc1;

UART_HandleTypeDef huart1;

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_ADC1_Init(void);
static void MX_USART1_UART_Init(void);
/* USER CODE BEGIN PFP */
static uint32_t ReadAdcChannel(uint32_t channel);         /* 声明单通道采样函数。 */
static void SendReport(uint32_t va_raw, uint32_t vb_raw); /* 声明串口报告函数。 */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
static uint32_t ReadAdcChannel(uint32_t channel)
{
  ADC_ChannelConfTypeDef selected = {0}; /* 准备并清空通道配置结构。 */
  selected.Channel = channel; /* 使用传入的 IN0 或 IN1 通道。 */
  selected.Rank = ADC_REGULAR_RANK_1; /* 单通道转换只用序列中的第 1 位。 */
  selected.SamplingTime = ADC_SAMPLETIME_239CYCLES_5; /* 留够分压节点的采样时间。 */
  if (HAL_ADC_ConfigChannel(&hadc1, &selected) != HAL_OK) /* 切换 ADC1 输入通道。 */
  {
    Error_Handler(); /* 通道配置失败时停止，避免报告错误电压。 */
  }
  if (HAL_ADC_Start(&hadc1) != HAL_OK) /* 软件启动一次转换。 */
  {
    Error_Handler(); /* ADC 不能启动时停止。 */
  }
  if (HAL_ADC_PollForConversion(&hadc1, ADC_TIMEOUT_MILLISECONDS) != HAL_OK) /* 等待转换结束。 */
  {
    Error_Handler(); /* 转换超时或失败时停止。 */
  }
  uint32_t sample = HAL_ADC_GetValue(&hadc1); /* 取得 0～4095 的原始 ADC 值。 */
  if (HAL_ADC_Stop(&hadc1) != HAL_OK) /* 停止本次转换。 */
  {
    Error_Handler(); /* ADC 无法停止时停止程序。 */
  }
  return sample; /* 将原始读数交回主循环。 */
}

static void SendReport(uint32_t va_raw, uint32_t vb_raw)
{
  char line[96]; /* 为终端的一行输出准备空间。 */
  uint32_t va_mv = va_raw * ADC_REFERENCE_MILLIVOLTS / ADC_MAXIMUM_CODE; /* VA 换算成毫伏。 */
  uint32_t vb_mv = vb_raw * ADC_REFERENCE_MILLIVOLTS / ADC_MAXIMUM_CODE; /* VB 换算成毫伏。 */
  int written = snprintf(line, sizeof(line), "VA=%lu mV (%lu)  VB=%lu mV (%lu)\r\n",
                         (unsigned long)va_mv, (unsigned long)va_raw,
                         (unsigned long)vb_mv, (unsigned long)vb_raw); /* 拼出带原始码值的报告。 */
  if (written < 0 || written >= (int)sizeof(line)) /* 检查格式化是否出错或超长。 */
  {
    Error_Handler(); /* 避免发送不完整报告。 */
  }
  if (HAL_UART_Transmit(&huart1, (uint8_t *)line, (uint16_t)strlen(line),
                        UART_TIMEOUT_MILLISECONDS) != HAL_OK) /* 从 PA9 发向终端 RXD。 */
  {
    Error_Handler(); /* 串口发送失败时停止。 */
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
  MX_ADC1_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */
  if (HAL_ADCEx_Calibration_Start(&hadc1) != HAL_OK) /* 初始化之后执行 ADC 校准。 */
  {
    Error_Handler(); /* 校准失败时不继续读取。 */
  }

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    uint32_t vb_raw = ReadAdcChannel(ADC_CHANNEL_0); /* PA0 / 引脚 10 对应 DIV_VB。 */
    uint32_t va_raw = ReadAdcChannel(ADC_CHANNEL_1); /* PA1 / 引脚 11 对应 DIV_VA。 */
    SendReport(va_raw, vb_raw); /* 输出这一次测得的两路电压。 */
    HAL_Delay(REPORT_PERIOD_MILLISECONDS); /* 每 500 ms 再重复。 */
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
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

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
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_ADC;
  PeriphClkInit.AdcClockSelection = RCC_ADCPCLK2_DIV2;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief ADC1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC1_Init(void)
{

  /* USER CODE BEGIN ADC1_Init 0 */

  /* USER CODE END ADC1_Init 0 */

  ADC_ChannelConfTypeDef sConfig = {0};

  /* USER CODE BEGIN ADC1_Init 1 */

  /* USER CODE END ADC1_Init 1 */

  /** Common config
  */
  hadc1.Instance = ADC1;
  hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
  hadc1.Init.ContinuousConvMode = DISABLE;
  hadc1.Init.DiscontinuousConvMode = DISABLE;
  hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc1.Init.NbrOfConversion = 1;
  if (HAL_ADC_Init(&hadc1) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure Regular Channel
  */
  sConfig.Channel = ADC_CHANNEL_0;
  sConfig.Rank = ADC_REGULAR_RANK_1;
  sConfig.SamplingTime = ADC_SAMPLETIME_239CYCLES_5;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN ADC1_Init 2 */

  /* USER CODE END ADC1_Init 2 */

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 9600;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOA_CLK_ENABLE();

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
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
