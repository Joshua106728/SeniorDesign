/*
 * LCD1602.c
 *
 *  Created on: 21-Jan-2020
 *      Author: Controllerstech
 */

#include <LCD1602.h>

#include "stm32f4xx_hal.h"


/****************** define the timer handler below  **************/
#define timer htim1


extern TIM_HandleTypeDef timer;
void delay (uint16_t us)
{
	__HAL_TIM_SET_COUNTER(&timer, 0);
	while (__HAL_TIM_GET_COUNTER(&timer) < us);
}

/****************************************************************************************************************************************************************/

void send_to_lcd (char data, int rs)
{
	HAL_GPIO_WritePin(RW_GPIO_Port, RW_Pin, GPIO_PIN_RESET);  // RW = 0 (WRITE)//ADDED THIS FROM CHAT, SAYING THAT THE RW PIN IS NEVER SET, P SURE I JUST CONNECTED IT TO GND THO
	HAL_GPIO_WritePin(RS_GPIO_Port, RS_Pin, rs);  // rs = 1 for data, rs=0 for command

	/* write the data to the respective pin */
	HAL_GPIO_WritePin(D7_GPIO_Port, D7_Pin, ((data>>3)&0x01));
	HAL_GPIO_WritePin(D6_GPIO_Port, D6_Pin, ((data>>2)&0x01));
	HAL_GPIO_WritePin(D5_GPIO_Port, D5_Pin, ((data>>1)&0x01));
	HAL_GPIO_WritePin(D4_GPIO_Port, D4_Pin, ((data>>0)&0x01));

	/* Toggle EN PIN to send the data
	 * if the HCLK > 100 MHz, use the  20 us delay
	 * if the LCD still doesn't work, increase the delay to 50, 80 or 100..
	 */
	HAL_GPIO_WritePin(EN_GPIO_Port, EN_Pin, 1);
	HAL_Delay(40);
	HAL_GPIO_WritePin(EN_GPIO_Port, EN_Pin, 0);
	HAL_Delay(40);
}

void lcd_send_cmd (char cmd)
{
    char datatosend;

    /* send upper nibble first */
    datatosend = ((cmd>>4)&0x0f);
    send_to_lcd(datatosend,0);  // RS must be 0 while sending command

    /* send Lower Nibble */
    datatosend = ((cmd)&0x0f);
	send_to_lcd(datatosend, 0);
}

void lcd_send_data (char data)
{
	char datatosend;

	/* send higher nibble */
	datatosend = ((data>>4)&0x0f);
	send_to_lcd(datatosend, 1);  // rs =1 for sending data

	/* send Lower nibble */
	datatosend = ((data)&0x0f);
	send_to_lcd(datatosend, 1);
}

void lcd_clear (void)
{
	lcd_send_cmd(0x01);
	HAL_Delay(2);
}

void lcd_put_cur(int row, int col)
{
    switch (row)
    {
        case 0:
            col |= 0x80;
            break;
        case 1:
            col |= 0xC0;
            break;
    }

    lcd_send_cmd (col);
}

static void lcd_write_nibble(uint8_t nibble)
{
    HAL_GPIO_WritePin(RS_GPIO_Port, RS_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(RW_GPIO_Port, RW_Pin, GPIO_PIN_RESET);

    HAL_GPIO_WritePin(D7_GPIO_Port, D7_Pin, (nibble >> 3) & 1);
    HAL_GPIO_WritePin(D6_GPIO_Port, D6_Pin, (nibble >> 2) & 1);
    HAL_GPIO_WritePin(D5_GPIO_Port, D5_Pin, (nibble >> 1) & 1);
    HAL_GPIO_WritePin(D4_GPIO_Port, D4_Pin, (nibble >> 0) & 1);

    HAL_GPIO_WritePin(EN_GPIO_Port, EN_Pin, GPIO_PIN_SET);
    HAL_Delay(1);
    HAL_GPIO_WritePin(EN_GPIO_Port, EN_Pin, GPIO_PIN_RESET);
}

void lcd_init(void)
{
    HAL_Delay(50);

    lcd_write_nibble(0x03);
    HAL_Delay(5);

    lcd_write_nibble(0x03);
    HAL_Delay(1);

    lcd_write_nibble(0x03);
    HAL_Delay(1);

    lcd_write_nibble(0x02);  // switch to 4-bit mode
    HAL_Delay(1);

    lcd_send_cmd(0x28);
    lcd_send_cmd(0x08);
    lcd_send_cmd(0x01);
    HAL_Delay(2);
    lcd_send_cmd(0x06);
    lcd_send_cmd(0x0C);
}


//void lcd_init(void)
//{
//    // --- Power-on delay ---
//    HAL_Delay(50);   // >40 ms after VDD rises to 4.5V
//
//    // --- Force 8-bit mode three times (datasheet requirement) ---
//    lcd_send_cmd(0x30);
//    HAL_Delay(5);    // >4.1 ms
//
//    lcd_send_cmd(0x30);
//    HAL_Delay(1);    // >100 µs
//
//    lcd_send_cmd(0x30);
//    HAL_Delay(1);
//
//    // --- Set 4-bit mode ---
//    lcd_send_cmd(0x20);   // 0b0010 ----
//    HAL_Delay(2);
//
//    // --- Function Set ---
//    // 4-bit, 2 lines, 5x8 font
//    lcd_send_cmd(0x28);   // 0b0010 1000
//    HAL_Delay(1);
//
//    // --- Display OFF ---
//    lcd_send_cmd(0x08);   // Display OFF (D=0)
//    HAL_Delay(1);
//
//    // --- Clear Display ---
//    lcd_send_cmd(0x01);
//    HAL_Delay(2);         // Clear command needs >1.52ms
//
//    // --- Entry Mode Set ---
//    lcd_send_cmd(0x06);   // Increment, No shift
//    HAL_Delay(1);
//
//    // --- Display ON (no cursor, no blink) ---
//    lcd_send_cmd(0x0C);   // Display ON, Cursor OFF, Blink OFF
//    HAL_Delay(1);
//}


//void lcd_init (void)
//{
//	// 4 bit initialisation
//	HAL_Delay(50);  // wait for >40ms
//	lcd_send_cmd (0x30);
//	HAL_Delay(5);  // wait for >4.1ms
//	lcd_send_cmd (0x30);
//	HAL_Delay(1);  // wait for >100us
//	lcd_send_cmd (0x30);
//	HAL_Delay(10);
//	lcd_send_cmd (0x20);  // 4bit mode
//	HAL_Delay(10);
//
//  // dislay initialisation
//	lcd_send_cmd (0x28); // Function set --> DL=0 (4 bit mode), N = 1 (2 line display) F = 0 (5x8 characters)
//	HAL_Delay(1);
//	lcd_send_cmd (0x08); //Display on/off control --> D=0,C=0, B=0  ---> display off
//	HAL_Delay(1);
//	lcd_send_cmd (0x01);  // clear display
//	HAL_Delay(1);
//	HAL_Delay(1);
//	lcd_send_cmd (0x06); //Entry mode set --> I/D = 1 (increment cursor) & S = 0 (no shift)
//	HAL_Delay(1);
//	lcd_send_cmd (0x0C); //Display on/off control --> D = 1, C and B = 0. (Cursor and blink, last two bits)
//}

void lcd_send_string (char *str)
{
	while (*str) lcd_send_data (*str++);
}

//keypad functions
char read_keypad_recording_mode (void)
{
	HAL_GPIO_WritePin (R1_GPIO_Port, R1_Pin, GPIO_PIN_SET);  //Pull the R1 low
	HAL_GPIO_WritePin (R2_GPIO_Port, R2_Pin, GPIO_PIN_SET);  // Pull the R2 High
	HAL_GPIO_WritePin (R3_GPIO_Port, R3_Pin, GPIO_PIN_SET);  // Pull the R3 High
	HAL_GPIO_WritePin (R4_GPIO_Port, R4_Pin, GPIO_PIN_RESET);  // Pull the R4 High

	if (!(HAL_GPIO_ReadPin (C3_GPIO_Port, C3_Pin)))   // if the Col 3 is low
		{ // wait till the button is pressed
			return '#';
		}
}


char read_keypad (void)
{
	/* Make ROW 1 LOW and all other ROWs HIGH */
	HAL_GPIO_WritePin (R1_GPIO_Port, R1_Pin, GPIO_PIN_RESET);  //Pull the R1 low
	HAL_GPIO_WritePin (R2_GPIO_Port, R2_Pin, GPIO_PIN_SET);  // Pull the R2 High
	HAL_GPIO_WritePin (R3_GPIO_Port, R3_Pin, GPIO_PIN_SET);  // Pull the R3 High
	HAL_GPIO_WritePin (R4_GPIO_Port, R4_Pin, GPIO_PIN_SET);  // Pull the R4 High

	if (!(HAL_GPIO_ReadPin (C1_GPIO_Port, C1_Pin)))   // if the Col 1 is low
	{
		while (!(HAL_GPIO_ReadPin (C1_GPIO_Port, C1_Pin)));   // wait till the button is pressed
		return '1';
	}

	if (!(HAL_GPIO_ReadPin (C2_GPIO_Port, C2_Pin)))   // if the Col 2 is low
	{
		while (!(HAL_GPIO_ReadPin (C2_GPIO_Port, C2_Pin)));   // wait till the button is pressed
		return '2';
	}

	if (!(HAL_GPIO_ReadPin (C3_GPIO_Port, C3_Pin)))   // if the Col 3 is low
	{
		while (!(HAL_GPIO_ReadPin (C3_GPIO_Port, C3_Pin)));   // wait till the button is pressed
		return '3';
	}

	if (!(HAL_GPIO_ReadPin (C4_GPIO_Port, C4_Pin)))   // if the Col 4 is low
	{
		while (!(HAL_GPIO_ReadPin (C4_GPIO_Port, C4_Pin)));   // wait till the button is pressed
		return 'A';
	}

	/* Make ROW 2 LOW and all other ROWs HIGH */
	HAL_GPIO_WritePin (R1_GPIO_Port, R1_Pin, GPIO_PIN_SET);  //Pull the R1 low
	HAL_GPIO_WritePin (R2_GPIO_Port, R2_Pin, GPIO_PIN_RESET);  // Pull the R2 High
	HAL_GPIO_WritePin (R3_GPIO_Port, R3_Pin, GPIO_PIN_SET);  // Pull the R3 High
	HAL_GPIO_WritePin (R4_GPIO_Port, R4_Pin, GPIO_PIN_SET);  // Pull the R4 High

	if (!(HAL_GPIO_ReadPin (C1_GPIO_Port, C1_Pin)))   // if the Col 1 is low
	{
		while (!(HAL_GPIO_ReadPin (C1_GPIO_Port, C1_Pin)));   // wait till the button is pressed
		return '4';
	}

	if (!(HAL_GPIO_ReadPin (C2_GPIO_Port, C2_Pin)))   // if the Col 2 is low
	{
		while (!(HAL_GPIO_ReadPin (C2_GPIO_Port, C2_Pin)));   // wait till the button is pressed
		return '5';
	}

	if (!(HAL_GPIO_ReadPin (C3_GPIO_Port, C3_Pin)))   // if the Col 3 is low
	{
		while (!(HAL_GPIO_ReadPin (C3_GPIO_Port, C3_Pin)));   // wait till the button is pressed
		return '6';
	}

	if (!(HAL_GPIO_ReadPin (C4_GPIO_Port, C4_Pin)))   // if the Col 4 is low
	{
		while (!(HAL_GPIO_ReadPin (C4_GPIO_Port, C4_Pin)));   // wait till the button is pressed
		return 'B';
	}


	/* Make ROW 3 LOW and all other ROWs HIGH */
	HAL_GPIO_WritePin (R1_GPIO_Port, R1_Pin, GPIO_PIN_SET);  //Pull the R1 low
	HAL_GPIO_WritePin (R2_GPIO_Port, R2_Pin, GPIO_PIN_SET);  // Pull the R2 High
	HAL_GPIO_WritePin (R3_GPIO_Port, R3_Pin, GPIO_PIN_RESET);  // Pull the R3 High
	HAL_GPIO_WritePin (R4_GPIO_Port, R4_Pin, GPIO_PIN_SET);  // Pull the R4 High

	if (!(HAL_GPIO_ReadPin (C1_GPIO_Port, C1_Pin)))   // if the Col 1 is low
	{
		while (!(HAL_GPIO_ReadPin (C1_GPIO_Port, C1_Pin)));   // wait till the button is pressed
		return '7';
	}

	if (!(HAL_GPIO_ReadPin (C2_GPIO_Port, C2_Pin)))   // if the Col 2 is low
	{
		while (!(HAL_GPIO_ReadPin (C2_GPIO_Port, C2_Pin)));   // wait till the button is pressed
		return '8';
	}

	if (!(HAL_GPIO_ReadPin (C3_GPIO_Port, C3_Pin)))   // if the Col 3 is low
	{
		while (!(HAL_GPIO_ReadPin (C3_GPIO_Port, C3_Pin)));   // wait till the button is pressed
		return '9';
	}

	if (!(HAL_GPIO_ReadPin (C4_GPIO_Port, C4_Pin)))   // if the Col 4 is low
	{
		while (!(HAL_GPIO_ReadPin (C4_GPIO_Port, C4_Pin)));   // wait till the button is pressed
		return 'C';
	}


	/* Make ROW 4 LOW and all other ROWs HIGH */
	HAL_GPIO_WritePin (R1_GPIO_Port, R1_Pin, GPIO_PIN_SET);  //Pull the R1 low
	HAL_GPIO_WritePin (R2_GPIO_Port, R2_Pin, GPIO_PIN_SET);  // Pull the R2 High
	HAL_GPIO_WritePin (R3_GPIO_Port, R3_Pin, GPIO_PIN_SET);  // Pull the R3 High
	HAL_GPIO_WritePin (R4_GPIO_Port, R4_Pin, GPIO_PIN_RESET);  // Pull the R4 High

	if (!(HAL_GPIO_ReadPin (C1_GPIO_Port, C1_Pin)))   // if the Col 1 is low
	{
		while (!(HAL_GPIO_ReadPin (C1_GPIO_Port, C1_Pin)));   // wait till the button is pressed
		return '*';
	}

	if (!(HAL_GPIO_ReadPin (C2_GPIO_Port, C2_Pin)))   // if the Col 2 is low
	{
		while (!(HAL_GPIO_ReadPin (C2_GPIO_Port, C2_Pin)));   // wait till the button is pressed
		return '0';
	}

	if (!(HAL_GPIO_ReadPin (C3_GPIO_Port, C3_Pin)))   // if the Col 3 is low
	{
		while (!(HAL_GPIO_ReadPin (C3_GPIO_Port, C3_Pin)));   // wait till the button is pressed
		return '#';
	}

	if (!(HAL_GPIO_ReadPin (C4_GPIO_Port, C4_Pin)))   // if the Col 4 is low
	{
		while (!(HAL_GPIO_ReadPin (C4_GPIO_Port, C4_Pin)));   // wait till the button is pressed
		return 'D';
	}

	return 0x01;  // /if nothing is pressed

}
