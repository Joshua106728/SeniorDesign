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
#include "dma.h"
#include "fatfs.h"
#include "i2s.h"
#include "spi.h"
#include "tim.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "arm_math.h"
#include "arm_compiler_specific.h"
#include "constants.h"
#include "yin.h"
#include "preprocessing.h"
#include "postprocessing.h"
#include "to_midi.h"
#include <math.h>
#include <stdio.h>
#include <stdbool.h>
#include "LCD1602.h"
#include "sd_functions.h"
#include "stdio.h"
#include "sd_benchmark.h"
#include "integration_functions.h"

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

// MIC
uint16_t  mic_dma_buffer[MIC_DOUBLE_BUF];
float32_t frame_buffer[FRAME_LENGTH];
volatile bool half_ready = 0;
volatile bool full_ready = 0;

float32_t f0;
uint8_t   midi_buffer[512];
float32_t f0_estimates[MAX_FRAMES];
float32_t f0_times[MAX_FRAMES];
int       total_frames = 0;
int       midi_size = 0;
int       note_event_count = 0;
NoteEvent note_events[MAX_FRAMES];

// Keypad
volatile uint8_t start_flag, stop_flag, processing;

// LCD
static uint32_t last_beat_tick = 0;
static uint8_t  beat_visible = 0;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

static float32_t dc_x_prev = 0.0f;
static float32_t dc_y_prev = 0.0f;

static inline float32_t dc_block(float32_t x) {
    float32_t y = x - dc_x_prev + 0.995f * dc_y_prev;
    dc_x_prev = x;
    dc_y_prev = y;
    return y;
}

static void process_mic_dma(int dma_offset) {
	// shift [HOP_LENGTH:FRAME_LENGTH-1] --> [0:HOP_LENGTH-1] (idx 0 = oldest frame & last idx = newest)
	arm_copy_f32(&frame_buffer[HOP_LENGTH], &frame_buffer[0], HOP_LENGTH);

	// Reconstruct 24-bit mic data on first half of buffer
	for (int i = 0; i < HOP_LENGTH; i++) {
	    int idx = dma_offset + (i << 2);
	    int32_t sample = (mic_dma_buffer[idx] << 16) | mic_dma_buffer[idx+1];
	    sample >>= 8;
	    frame_buffer[HOP_LENGTH + i] = dc_block((float32_t)sample);
	}
}

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
int row = 0;
int col = 0;
char key;

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
  MX_DMA_Init();
  MX_I2S2_Init();
  MX_SPI3_Init();
  MX_TIM1_Init();
  /* USER CODE BEGIN 2 */
  HAL_TIM_Base_Start(&htim1);
  HAL_GPIO_WritePin (R1_GPIO_Port, R1_Pin, GPIO_PIN_SET);  //Pull the R1 High
  HAL_GPIO_WritePin (R2_GPIO_Port, R2_Pin, GPIO_PIN_SET);  // Pull the R2 High
  HAL_GPIO_WritePin (R3_GPIO_Port, R3_Pin, GPIO_PIN_SET);  // Pull the R3 High
  HAL_GPIO_WritePin (R4_GPIO_Port, R4_Pin, GPIO_PIN_RESET);  // Pull the R4 low


  // initialize LCD
  HAL_Delay(10);
  lcd_init ();
  lcd_put_cur(0, 0);
  lcd_send_string("                ");
  lcd_put_cur(1, 0);
  lcd_send_string("                ");

  HAL_Delay(10);
  lcd_clear();
  HAL_Delay(10);
  lcd_put_cur(0,0);
  HAL_Delay(10);

  lcd_send_string("INITIALIZING");
  lcd_put_cur(1, 0);
  HAL_Delay(10);

  // Initialize DSP, DMA, random LED
  yin_init();
  preprocessing_init();
  HAL_I2S_Receive_DMA(&hi2s2, mic_dma_buffer, MIC_BUF);
  HAL_GPIO_TogglePin(GPIOC, LED1_Pin);
  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_1, GPIO_PIN_SET);

  lcd_send_string("PRESS * TO START");

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */

  // Initialize SD Card
  while (1)
  {
	  if (start_flag) {
		  start_flag = 0;
		  processing = 1; // processing flag
		  total_frames = 0;
		  note_event_count = 0;
		  midi_size = 0;

		  lcd_clear();
		  lcd_put_cur(0, 0);
		  lcd_send_string("REC AT 80 BPM");
	  }
	  if (stop_flag)  {
		  stop_flag  = 0;
		  processing = 0;

		  lcd_clear();
		  lcd_put_cur(0, 0);
		  lcd_send_string("WRITING TO FILE");

		  // Write to MIDI BUFFER
		  note_event_count = segment_notes(
			  f0_estimates, f0_times, total_frames,
			  MIN_FRAMES, (float32_t)PITCH_TOLERANCE,
			  note_events, MAX_FRAMES
		  );

		  compensate_onset(note_events, note_event_count);
		  snap_notes(note_events, note_event_count, BPM);
		  midi_size = write_midi_file(
			  note_events, note_event_count,
			  BPM, midi_buffer, sizeof(midi_buffer)
		  );


		  lcd_clear();
		  lcd_put_cur(0, 0);
		  lcd_send_string("DONE");
	  }

	  // Continuous mic processing while recording
	  if (processing) {
		  if (half_ready) {
			  half_ready = 0;
			  process_mic_dma(0);
			  f0 = preprocess_audio(frame_buffer);
			  if (total_frames < MAX_FRAMES) {
				  f0_estimates[total_frames] = f0;
				  f0_times[total_frames] = (float32_t)total_frames * FRAME_TIME;
				  total_frames++;
			  }
			  if (total_frames >= MAX_FRAMES) {
				  stop_flag = 1;  // auto-stop when buffer full
			  }
		  }
		  if (full_ready) {
			  full_ready = 0;
			  process_mic_dma(MIC_BUF);
			  f0 = preprocess_audio(frame_buffer);
			  if (total_frames < MAX_FRAMES) {
				  f0_estimates[total_frames] = f0;
				  f0_times[total_frames] = (float32_t)total_frames * FRAME_TIME;
				  total_frames++;
			  }
			  if (total_frames >= MAX_FRAMES) {
				  stop_flag = 1;
			  }
		  }

		  uint32_t now = HAL_GetTick();
		  uint32_t phase = (now - last_beat_tick);

		  if (!beat_visible && phase >= BEAT_MS) {
			  // New beat — show the indicator
			  lcd_put_cur(1, 0);
			  lcd_send_string("* BPM 80 *");
			  beat_visible = 1;
			  last_beat_tick = now;
		  }
		  else if (beat_visible && phase >= FLASH_MS) {
			  // Flash window ended — clear it
			  lcd_put_cur(1, 0);
			  lcd_send_string("          ");   // 10 spaces to erase
			  beat_visible = 0;
		  }
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

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = 16;
  RCC_OscInitStruct.PLL.PLLN = 192;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 4;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_3) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
void HAL_I2S_RxHalfCpltCallback(I2S_HandleTypeDef *hi2s) {half_ready = 1; }
void HAL_I2S_RxCpltCallback(I2S_HandleTypeDef *hi2s) {full_ready = 1; }

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_pin) {
	if(GPIO_pin == C1_Pin) {start_flag = 1; }
	else if(GPIO_pin == C3_Pin) {stop_flag = 1; }
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
