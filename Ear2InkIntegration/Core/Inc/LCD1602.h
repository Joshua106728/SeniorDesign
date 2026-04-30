/*
 * lcd1602.h
 *
 *  Created on: Jan 21, 2020
 *      Author: Controllerstech
 */

/*********** Define the LCD and Keypad PINS below ****************/

#define RS_Pin GPIO_PIN_1
#define RS_GPIO_Port GPIOA
#define RW_Pin GPIO_PIN_2
#define RW_GPIO_Port GPIOA
#define EN_Pin GPIO_PIN_4
#define EN_GPIO_Port GPIOA
#define D4_Pin GPIO_PIN_5
#define D4_GPIO_Port GPIOA
#define D5_Pin GPIO_PIN_8////on the pcb this is pa8
#define D5_GPIO_Port GPIOA
#define D6_Pin GPIO_PIN_7
#define D6_GPIO_Port GPIOA
#define D7_Pin GPIO_PIN_0
#define D7_GPIO_Port GPIOA

#define R1_GPIO_Port GPIOB  // row 1 port
#define R1_Pin  GPIO_PIN_7  // row 1 pin
#define R2_GPIO_Port GPIOB
#define R2_Pin  GPIO_PIN_6
#define R3_GPIO_Port GPIOB
#define R3_Pin  GPIO_PIN_5
#define R4_GPIO_Port GPIOB
#define R4_Pin  GPIO_PIN_4
#define C1_GPIO_Port GPIOB
#define C1_Pin  GPIO_PIN_3
#define C2_GPIO_Port GPIOB
#define C2_Pin  GPIO_PIN_2
#define C3_GPIO_Port GPIOB
#define C3_Pin  GPIO_PIN_1
#define C4_GPIO_Port GPIOB
#define C4_Pin  GPIO_PIN_0


#ifndef INC_LCD1602_H_
#define INC_LCD1602_H_


void lcd_init (void);   // initialize lcd

void lcd_send_cmd (char cmd);  // send command to the lcd

void lcd_send_data (char data);  // send data to the lcd

void lcd_send_string (char *str);  // send string to the lcd

void lcd_put_cur(int row, int col);  // put cursor at the entered position row (0 or 1), col (0-15);

void lcd_clear (void);

char read_keypad_recording_mode (void);

char read_keypad (void);

#endif /* INC_LCD1602_H_ */


