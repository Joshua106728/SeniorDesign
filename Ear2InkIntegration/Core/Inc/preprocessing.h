/*
 * preprocessing.h
 *
 *  Created on: Apr 3, 2026
 *      Author: jhwjh
 */

#ifndef INC_PREPROCESSING_H_
#define INC_PREPROCESSING_H_

#include "constants.h"

void preprocessing_init(void);
float32_t preprocess_audio(const float32_t *frame);

#endif /* INC_PREPROCESSING_H_ */
