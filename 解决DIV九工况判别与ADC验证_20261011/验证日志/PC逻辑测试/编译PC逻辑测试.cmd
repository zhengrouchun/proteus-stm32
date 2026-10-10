@echo off
rem Use UTF-8 for Chinese paths.
chcp 65001 >nul
rem Set up the installed x64 compiler.
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
rem Compile the delivered application with a fake HAL for unit tests only.
cl /nologo /LD /O2 /utf-8 /W4 /I"D:\Proteus\project\fix_missing_cubemx_adc_hex\ADC_CubeMX_Keil\Inc" /I"D:\Proteus\project\解决DIV九工况判别与ADC验证_20261011\验证日志\PC逻辑测试" /Fe"D:\Proteus\project\解决DIV九工况判别与ADC验证_20261011\验证日志\PC逻辑测试\div_logic_test.dll" /Fo"D:\Proteus\project\解决DIV九工况判别与ADC验证_20261011\验证日志\PC逻辑测试\div_logic_test.obj" "D:\Proteus\project\解决DIV九工况判别与ADC验证_20261011\工具\测试真实应用逻辑.c"
