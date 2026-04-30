################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Core/Src/LCD1602.c \
../Core/Src/dma.c \
../Core/Src/gpio.c \
../Core/Src/i2s.c \
../Core/Src/integration_functions.c \
../Core/Src/main.c \
../Core/Src/postprocessing.c \
../Core/Src/preprocessing.c \
../Core/Src/sd_benchmark.c \
../Core/Src/sd_diskio_spi.c \
../Core/Src/sd_functions.c \
../Core/Src/sd_spi.c \
../Core/Src/spi.c \
../Core/Src/stm32f4xx_hal_msp.c \
../Core/Src/stm32f4xx_it.c \
../Core/Src/syscalls.c \
../Core/Src/sysmem.c \
../Core/Src/system_stm32f4xx.c \
../Core/Src/tim.c \
../Core/Src/to_midi.c \
../Core/Src/yin.c 

OBJS += \
./Core/Src/LCD1602.o \
./Core/Src/dma.o \
./Core/Src/gpio.o \
./Core/Src/i2s.o \
./Core/Src/integration_functions.o \
./Core/Src/main.o \
./Core/Src/postprocessing.o \
./Core/Src/preprocessing.o \
./Core/Src/sd_benchmark.o \
./Core/Src/sd_diskio_spi.o \
./Core/Src/sd_functions.o \
./Core/Src/sd_spi.o \
./Core/Src/spi.o \
./Core/Src/stm32f4xx_hal_msp.o \
./Core/Src/stm32f4xx_it.o \
./Core/Src/syscalls.o \
./Core/Src/sysmem.o \
./Core/Src/system_stm32f4xx.o \
./Core/Src/tim.o \
./Core/Src/to_midi.o \
./Core/Src/yin.o 

C_DEPS += \
./Core/Src/LCD1602.d \
./Core/Src/dma.d \
./Core/Src/gpio.d \
./Core/Src/i2s.d \
./Core/Src/integration_functions.d \
./Core/Src/main.d \
./Core/Src/postprocessing.d \
./Core/Src/preprocessing.d \
./Core/Src/sd_benchmark.d \
./Core/Src/sd_diskio_spi.d \
./Core/Src/sd_functions.d \
./Core/Src/sd_spi.d \
./Core/Src/spi.d \
./Core/Src/stm32f4xx_hal_msp.d \
./Core/Src/stm32f4xx_it.d \
./Core/Src/syscalls.d \
./Core/Src/sysmem.d \
./Core/Src/system_stm32f4xx.d \
./Core/Src/tim.d \
./Core/Src/to_midi.d \
./Core/Src/yin.d 


# Each subdirectory must supply rules for building sources it contributes
Core/Src/%.o Core/Src/%.su Core/Src/%.cyclo: ../Core/Src/%.c Core/Src/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32F411xE -c -I../Core/Inc -I../Drivers/CMSIS/DSP/Include -I../Drivers/CMSIS/DSP/PrivateInclude -I../FATFS/Target -I../FATFS/App -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Middlewares/Third_Party/FatFs/src -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Core-2f-Src

clean-Core-2f-Src:
	-$(RM) ./Core/Src/LCD1602.cyclo ./Core/Src/LCD1602.d ./Core/Src/LCD1602.o ./Core/Src/LCD1602.su ./Core/Src/dma.cyclo ./Core/Src/dma.d ./Core/Src/dma.o ./Core/Src/dma.su ./Core/Src/gpio.cyclo ./Core/Src/gpio.d ./Core/Src/gpio.o ./Core/Src/gpio.su ./Core/Src/i2s.cyclo ./Core/Src/i2s.d ./Core/Src/i2s.o ./Core/Src/i2s.su ./Core/Src/integration_functions.cyclo ./Core/Src/integration_functions.d ./Core/Src/integration_functions.o ./Core/Src/integration_functions.su ./Core/Src/main.cyclo ./Core/Src/main.d ./Core/Src/main.o ./Core/Src/main.su ./Core/Src/postprocessing.cyclo ./Core/Src/postprocessing.d ./Core/Src/postprocessing.o ./Core/Src/postprocessing.su ./Core/Src/preprocessing.cyclo ./Core/Src/preprocessing.d ./Core/Src/preprocessing.o ./Core/Src/preprocessing.su ./Core/Src/sd_benchmark.cyclo ./Core/Src/sd_benchmark.d ./Core/Src/sd_benchmark.o ./Core/Src/sd_benchmark.su ./Core/Src/sd_diskio_spi.cyclo ./Core/Src/sd_diskio_spi.d ./Core/Src/sd_diskio_spi.o ./Core/Src/sd_diskio_spi.su ./Core/Src/sd_functions.cyclo ./Core/Src/sd_functions.d ./Core/Src/sd_functions.o ./Core/Src/sd_functions.su ./Core/Src/sd_spi.cyclo ./Core/Src/sd_spi.d ./Core/Src/sd_spi.o ./Core/Src/sd_spi.su ./Core/Src/spi.cyclo ./Core/Src/spi.d ./Core/Src/spi.o ./Core/Src/spi.su ./Core/Src/stm32f4xx_hal_msp.cyclo ./Core/Src/stm32f4xx_hal_msp.d ./Core/Src/stm32f4xx_hal_msp.o ./Core/Src/stm32f4xx_hal_msp.su ./Core/Src/stm32f4xx_it.cyclo ./Core/Src/stm32f4xx_it.d ./Core/Src/stm32f4xx_it.o ./Core/Src/stm32f4xx_it.su ./Core/Src/syscalls.cyclo ./Core/Src/syscalls.d ./Core/Src/syscalls.o ./Core/Src/syscalls.su ./Core/Src/sysmem.cyclo ./Core/Src/sysmem.d ./Core/Src/sysmem.o ./Core/Src/sysmem.su ./Core/Src/system_stm32f4xx.cyclo ./Core/Src/system_stm32f4xx.d ./Core/Src/system_stm32f4xx.o ./Core/Src/system_stm32f4xx.su ./Core/Src/tim.cyclo ./Core/Src/tim.d ./Core/Src/tim.o ./Core/Src/tim.su ./Core/Src/to_midi.cyclo ./Core/Src/to_midi.d ./Core/Src/to_midi.o ./Core/Src/to_midi.su ./Core/Src/yin.cyclo ./Core/Src/yin.d ./Core/Src/yin.o ./Core/Src/yin.su

.PHONY: clean-Core-2f-Src

