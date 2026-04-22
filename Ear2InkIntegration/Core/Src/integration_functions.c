#include "main.h"
#include "fatfs.h"
#include "integration_functions.h"
#include "sd_functions.h"
#include <stdio.h>
#include "LCD1602.h"

FILE* fptr;
size_t bytes_read;
//static char file_name[] = "testing.txt";



void start_recording(uint32_t frequency)
{
	// GOOD PLACE TO START MIDI HEADERS IN THE FILE AND DEFINE THE FILE NAME

	sd_write_file("testing.txt", "start recording");
}

void write2sd(uint8_t *data, uint16_t data_size)
{
	printf("w\n");
	sd_append_file("testing.txt", "working perhaps");
}

void stop_recording()
{
//	fclose(fptr);

}


