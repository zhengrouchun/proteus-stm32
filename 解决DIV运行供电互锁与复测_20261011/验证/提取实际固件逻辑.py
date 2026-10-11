from pathlib import Path  # 用交付目录定位真实固件和主机测试文件。

root = Path(__file__).resolve().parents[1]  # 定位交付目录。
source = (root / "工程/Src/main.c").read_text(encoding="utf-8")  # 每次测试重新读取已编译的真实固件源码。
parts = []  # 收集真实类型、常量、状态和控制函数，不另写一套模拟算法。
for section in ["PTD", "PD", "PV", "PFP", "0"]:  # 按源文件依赖顺序提取用户代码区。
    begin = f"/* USER CODE BEGIN {section} */"  # 指定区段开始标记。
    end = f"/* USER CODE END {section} */"  # 指定区段结束标记。
    parts.append(source.split(begin, 1)[1].split(end, 1)[0])  # 将区段原样加入测试编译单元。
start = source.index("static void MX_GPIO_Init(void)\n{")  # 定位真实 GPIO 初始化实现。
brace = source.index("{", start)  # 找到函数体开始。
depth = 1  # 使用配对大括号找到整个函数体。
cursor = brace + 1  # 从第一个开括号之后扫描。
while depth:  # 扫描到整个函数体结束。
    depth += (source[cursor] == "{") - (source[cursor] == "}")  # 累加开括号，扣除闭括号。
    cursor += 1  # 前进到下一个字符。
parts.append(source[start:cursor])  # 将真实初始化函数也放入测试。
(root / "验证/实际固件逻辑.inc").write_text("\n".join(parts), encoding="utf-8")  # 保存供 C 编译器包含的真实逻辑。
print("已提取真实固件控制、采样、报告、消抖及 GPIO 初始化代码。")  # 显示测试范围。
