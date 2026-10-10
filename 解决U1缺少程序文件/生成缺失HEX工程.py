"""从已有 CubeMX/Keil STM32F103C8 工程复制必要文件，形成独立的 ADC 工程。"""
from pathlib import Path
from shutil import copy2, copytree
import xml.etree.ElementTree as ET

source = Path(r"D:\Proteus\project\P1_CreateProject")
target = Path(__file__).resolve().parent / "ADC_U1_HEX_FIX"

for relative_directory in (
    "Drivers/CMSIS/Include",
    "Drivers/CMSIS/Device/ST/STM32F1xx/Include",
    "Drivers/STM32F1xx_HAL_Driver/Inc",
):
    copytree(source / relative_directory, target / relative_directory, dirs_exist_ok=True)

for relative_file in (
    "Core/Inc/stm32f1xx_hal_conf.h",
    "Core/Src/system_stm32f1xx.c",
    "MDK-ARM/startup_stm32f103xb.s",
):
    destination = target / relative_file
    destination.parent.mkdir(parents=True, exist_ok=True)
    copy2(source / relative_file, destination)

driver_names = (
    "stm32f1xx_hal.c",
    "stm32f1xx_hal_adc.c",
    "stm32f1xx_hal_adc_ex.c",
    "stm32f1xx_hal_cortex.c",
    "stm32f1xx_hal_dma.c",
    "stm32f1xx_hal_exti.c",
    "stm32f1xx_hal_flash.c",
    "stm32f1xx_hal_flash_ex.c",
    "stm32f1xx_hal_gpio.c",
    "stm32f1xx_hal_gpio_ex.c",
    "stm32f1xx_hal_pwr.c",
    "stm32f1xx_hal_rcc.c",
    "stm32f1xx_hal_rcc_ex.c",
    "stm32f1xx_hal_uart.c",
)
for driver_name in driver_names:
    relative_file = Path("Drivers/STM32F1xx_HAL_Driver/Src") / driver_name
    destination = target / relative_file
    destination.parent.mkdir(parents=True, exist_ok=True)
    copy2(source / relative_file, destination)

configuration_path = target / "Core/Inc/stm32f1xx_hal_conf.h"
configuration = configuration_path.read_text(encoding="utf-8")
configuration = configuration.replace("/*#define HAL_ADC_MODULE_ENABLED   */", "#define HAL_ADC_MODULE_ENABLED")
configuration = configuration.replace("/*#define HAL_UART_MODULE_ENABLED   */", "#define HAL_UART_MODULE_ENABLED")
configuration_path.write_text(configuration, encoding="utf-8")

main_header = target / "Core/Inc/main.h"
main_header.write_text(
    '#ifndef ADC_U1_HEX_FIX_MAIN_H\n'
    '#define ADC_U1_HEX_FIX_MAIN_H\n'
    '#include "stm32f1xx_hal.h" /* 让应用访问 HAL 的 ADC、UART 和 RCC 定义。 */\n'
    'void Error_Handler(void); /* 声明统一错误处理函数。 */\n'
    '#endif\n',
    encoding="utf-8",
)

project = ET.parse(source / "MDK-ARM/P1_CreateProject.uvprojx")
root = project.getroot()
for element in root.iter():
    if element.text and "P1_CreateProject" in element.text:
        element.text = element.text.replace("P1_CreateProject", "ADC_U1_HEX_FIX")
for group in root.findall(".//Group"):
    files = group.find("Files")
    if files is None:
        continue
    for file in list(files):
        name = file.findtext("FileName", default="")
        if name in ("tim.c", "gpio.c", "stm32f1xx_it.c", "stm32f1xx_hal_msp.c") or "hal_tim" in name:
            files.remove(file)
    group_name = group.findtext("GroupName", default="")
    if group_name == "Drivers/STM32F1xx_HAL_Driver":
        for driver_name in ("stm32f1xx_hal_adc.c", "stm32f1xx_hal_adc_ex.c", "stm32f1xx_hal_uart.c"):
            file = ET.SubElement(files, "File")
            ET.SubElement(file, "FileName").text = driver_name
            ET.SubElement(file, "FileType").text = "1"
            ET.SubElement(file, "FilePath").text = f"../Drivers/STM32F1xx_HAL_Driver/Src/{driver_name}"
for after_make in root.findall(".//AfterMake"):
    second_program = after_make.find("RunUserProg2")
    if second_program is not None:
        second_program.text = "0"
project.write(target / "MDK-ARM/ADC_U1_HEX_FIX.uvprojx", encoding="utf-8", xml_declaration=True)
print(target / "MDK-ARM/ADC_U1_HEX_FIX.uvprojx")
