#include "stdio.h"

#define BUFF_SIZE 2048

void start_recording(uint32_t frequency);

void write2sd(uint8_t *data, uint16_t data_size);

void stop_recording();
