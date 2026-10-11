@echo off
rem Load the installed Visual Studio C compiler environment.
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
rem Keep every test output inside this delivery directory.
cd /d "%~dp0"
rem Compile the single C harness with actual firmware code and mocked HAL.
for %%T in (*.c) do cl /nologo /utf-8 /W3 /wd4505 /Fe:power_behavior_tests.exe /Fo:power_behavior_tests.obj "%%T"
rem Return the compiler status. Run the test executable separately.
exit /b %errorlevel%
