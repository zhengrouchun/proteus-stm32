"""验证真实 C 应用逻辑、区间来源和 HEX；PC 合成输入不写入实测 CSV。"""
from pathlib import Path  # 统一定位工程、参数和日志。
import csv  # 按原表字段读取区间和记录。
import ctypes  # 调用实际编译的 C 函数。
import difflib  # 保存原工程与修改后工程的差异。
import hashlib  # 核对原资料和交付文件摘要。
import json  # 保存机器可读的验证报告。
import re  # 原样提取 USER CODE 和 C 参数表。
import subprocess  # 启动已安装的 MSVC 编译测试 DLL。

delivery = Path(__file__).resolve().parents[1]  # 本次交付目录。
workspace = delivery.parent  # 用户工程所在工作区。
project = workspace / "fix_missing_cubemx_adc_hex" / "ADC_CubeMX_Keil"  # 最终 STM32 工程。
backup = delivery / "修改前_ADC_CubeMX_Keil_完整备份"  # 完整保留的修改前工程。
logs = delivery / "验证日志"  # 所有 PC 检查证据存于此处。
pc_build = logs / "PC逻辑测试"  # PC 产物与 MCU HEX 分开，防止误加载。
pc_build.mkdir(exist_ok=True)  # 创建独立的测试输出目录。
main = (project / "Src" / "main.c").read_text(encoding="utf-8")  # 使用实际交付主程序。
header = (project / "Inc" / "div_diagnosis.h").read_text(encoding="utf-8")  # 使用实际交付判别函数。
regions = []  # 收集被测应用部分，不修改其中任何语句。
for label in ("PD", "PTD", "0"):  # 分别提取常量、记录类型、完整采样与报告函数。
    match = re.search(r"/\* USER CODE BEGIN " + label + r" \*/(.*?)/\* USER CODE END " + label + r" \*/", main, re.S)  # 按 CubeMX 标记提取。
    assert match is not None, label  # 标记不存在就终止测试，避免测错代码。
    regions.append(match[1])  # 保存原样的区域内容。
(pc_build / "被测应用_USER_CODE.inc").write_text("\n".join(regions), encoding="utf-8")  # 让测试编译器包含真实代码。
vs_tools = Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat")  # 已检查本机存在的 MSVC 环境脚本。
dll_path = pc_build / "div_logic_test.dll"  # 生成 PC DLL，仅供测试调用。
batch = pc_build / "编译PC逻辑测试.cmd"  # 用批处理确保调用 vcvars 后继承环境。
batch.write_text('@echo off\nrem Use UTF-8 for Chinese paths.\nchcp 65001 >nul\nrem Set up the installed x64 compiler.\ncall "' + str(vs_tools) + '"\nrem Compile the delivered application with a fake HAL for unit tests only.\ncl /nologo /LD /O2 /utf-8 /W4 /I"' + str(project / "Inc") + '" /I"' + str(pc_build) + '" /Fe"' + str(dll_path) + '" /Fo"' + str(pc_build / "div_logic_test.obj") + '" "' + str(delivery / "工具" / "测试真实应用逻辑.c") + '"\n', encoding="utf-8")  # 使用明确的 UTF-8 页解决中文路径被错误解码的问题。
compiled = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=pc_build, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  # 真正编译 C 测试。
(logs / "PC测试编译日志.txt").write_bytes(compiled.stdout)  # 保存完整编译输出。
assert compiled.returncode == 0, compiled.stdout.decode("utf-8", errors="replace")  # 编译失败时不报告测试成功。
library = ctypes.CDLL(str(dll_path))  # 载入刚刚生成的测试库。
library.TestClassify.argtypes = [ctypes.c_int32, ctypes.c_int32]  # 保留负区间下界语义。
library.TestClassify.restype = ctypes.c_int  # 返回 DIV 编号或负一。
library.TestConvert.argtypes = [ctypes.c_uint32]  # ADC 原码为无符号整数。
library.TestConvert.restype = ctypes.c_uint32  # 换算结果为非负 mV。
library.TestRun.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]  # 设置两点原码、错误阶段和节拍。
library.TestRun.restype = ctypes.c_char_p  # 取回实际报告文本。
rows = list(csv.DictReader((delivery / "原始资料" / "特征区间_v2.csv").read_text(encoding="utf-8-sig").splitlines()))  # 从原表而不是 C 常量生成独立期望值。
div_rows = [row for row in rows if row["模板"] == "DIV"]  # 当前只验证九个 DIV 状态。
keys = ["VB下界_mV", "VB上界_mV", "VA下界_mV", "VA上界_mV"]  # 固定参数顺序与结构字段对应。
bounds = [tuple(int(row[key]) for key in keys) for row in div_rows]  # 转为带符号的独立参考边界。
source_bounds = [tuple(map(int, match)) for match in re.findall(r"\{\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\s*\}", header)]  # 提取 C 实际编译常量。
assert source_bounds == bounds and len(bounds) == 9  # 严格核对所有 36 个边界，不容许改变验收区间。
checks = 0  # 统计本次真实执行的测试断言组。
nominal_results = []  # 仅供 PC 单元测试记录，明确不是实测值。
for index, row in enumerate(div_rows):  # 九个标称理论点分别用于合成测试。
    raw = [round(float(row[key]) * 4095 / 3300) for key in ("标称VB_mV", "标称VA_mV")]  # 合成理想 12 位量化输入。
    report = library.TestRun(*raw, 0, 0, 100).decode("ascii").strip()  # 实际执行 C 应用成功路径。
    fields = dict(item.split("=", 1) for item in report.split())  # 解析输出以核验所有字段。
    assert fields["STATE"] == f"DIV{index}" and fields["KIND"] == ("NORMAL" if index == 0 else "FAULT")  # 核对判别和分类。
    assert fields["FEATURE_READS"] == fields["ADC_CONVERSIONS"] == "2"  # 两个节点各进行一次转换。
    assert fields["ERROR"] == "OK" and fields["RUN_POWER"] == "NOT_IMPLEMENTED"  # 不得虚报运行供电状态。
    assert fields["ELAPSED_MS"] == "7" and library.TestStopCalls() == 2  # 计时不含模拟串口开销，并正确停止两次。
    for name, value in zip(("VB", "VA"), raw):  # 分别核验节点映射与换算。
        assert int(fields[name + "_RAW"]) == value and int(fields[name + "_MV"]) == (value * 3300 + 2047) // 4095  # 真实应用使用该节点原码。
    nominal_results.append({"case": f"DIV{index}", "evidence_type": "PC_SYNTHETIC_NOT_PROTEUS", "output": report})  # 明确标注证据类别。
    checks += 1  # 记录一个成功路径测试组。
for raw in range(4096):  # 穷举全部有效 12 位 ADC 原码。
    assert library.TestConvert(raw) == (raw * 3300 + 2047) // 4095  # 独立核验整数换算，包括零与满量程。
    checks += 1  # 记录一项换算检查。
vb_edges = sorted({value + offset for bound in bounds for value in bound[:2] for offset in (-1, 0, 1)} | {0, 1000, 3300})  # 选取每个 VB 边界内外相邻点。
va_edges = sorted({value + offset for bound in bounds for value in bound[2:] for offset in (-1, 0, 1)} | {0, 1000, 3300})  # VA 同样覆盖闭区间与间隙。
for vb in vb_edges:  # 遍历独立电压边界测试网格。
    for va in va_edges:  # 检查二维组合，包含无匹配和交叉区间。
        matches = [i for i, b in enumerate(bounds) if b[0] <= vb <= b[1] and b[2] <= va <= b[3]]  # 按原 CSV 构造独立期望结果。
        expected = matches[0] if len(matches) == 1 else -1  # 仅接受唯一匹配。
        assert library.TestClassify(vb, va) == expected, (vb, va, expected)  # 对比真实 C 实现。
        checks += 1  # 记录一个边界网格点。
for stage in range(1, 5):  # 覆盖配置、启动、等待、停止四种 HAL 失败阶段。
    for channel in range(2):  # 每个阶段分别在 VB 与 VA 注入错误。
        fields = dict(item.split("=", 1) for item in library.TestRun(564, 1128, stage, channel, 100).decode().split())  # 即使输入看似正常也必须拒绝错误结果。
        assert fields["STATE"] == fields["KIND"] == "UNKNOWN" and fields["ERROR"] != "OK"  # 错误不能判成正常。
        assert fields["FEATURE_READS"] == str(channel)  # 出错节点不算有效特征。
        assert fields["ADC_CONVERSIONS"] == str(channel + (stage == 4))  # 停止失败发生在真正取值之后，必须保留转换计数。
        assert fields["VA_RAW"] == fields["VA_MV"] == "NA"  # 未完成的 VA 不得填入零或旧值。
        assert library.TestStopCalls() == channel + (stage != 1)  # 启动后失败和轮询失败都尝试停止 ADC。
        checks += 1  # 记录一个错误路径测试组。
for vb, va, expected, count, features in ((4096, 1128, "ADC_RANGE_FAILED", 1, 0), (564, 4096, "ADC_RANGE_FAILED", 2, 1), (0, 0, "OK", 2, 2)):  # 覆盖越界原码和有效但不在模型内的输入。
    fields = dict(item.split("=", 1) for item in library.TestRun(vb, va, 0, 0, 100).decode().split())  # 调用同一真实应用函数。
    assert fields["STATE"] == "UNKNOWN" and fields["ERROR"] == expected  # 区分采样错误和电压不匹配。
    assert fields["ADC_CONVERSIONS"] == str(count) and fields["FEATURE_READS"] == str(features)  # 检查计数不虚报。
    checks += 1  # 记录一组异常输入。
wrapped = library.TestRun(564, 1128, 0, 0, 4294967292).decode()  # 让无符号毫秒计数在检测期间回绕。
assert "ELAPSED_MS=7 " in wrapped  # 无符号减法必须保持正确的时间差。
checks += 1  # 记录一次回绕检查。
hex_path = project / "MDK-ARM" / "ADC_CubeMX_Keil" / "ADC_CubeMX_Keil.hex"  # 本轮 Keil 实际生成的 HEX。
memory = {}  # 收集 HEX 中装入 Flash 的字节。
base = 0  # 保存扩展地址记录提供的高位地址。
eof = False  # 必须存在有效结束记录。
for line in hex_path.read_text(encoding="ascii").splitlines():  # 验证每条 Intel HEX 记录。
    assert line.startswith(":"), "HEX 缺少冒号"  # 拒绝损坏的文本行。
    record = bytes.fromhex(line[1:])  # 解码实际数据和校验和。
    assert len(record) == record[0] + 5 and sum(record) % 256 == 0  # 核验长度与校验和。
    count, address, kind = record[0], int.from_bytes(record[1:3], "big"), record[3]  # 读取记录属性。
    if kind == 4: base = int.from_bytes(record[4:6], "big") << 16  # 更新线性基地址。
    elif kind == 0: memory.update({base + address + i: value for i, value in enumerate(record[4:4 + count])})  # 收集有效代码字节。
    elif kind == 1: eof = True  # 确认结束记录。
assert eof and min(memory) == 0x08000000 and max(memory) < 0x08010000  # 全部代码应位于本芯片 64 KB Flash。
vectors = bytes(memory[0x08000000 + i] for i in range(8))  # 读取初始栈指针和复位向量。
stack = int.from_bytes(vectors[:4], "little")  # 提取初始 MSP。
reset = int.from_bytes(vectors[4:], "little")  # 提取 Thumb 复位入口。
assert 0x20000000 < stack <= 0x20005000 and reset & 1 and (reset & ~1) in memory  # 栈位于 20 KB SRAM 且复位向量可执行。
image = bytes(memory[i] for i in sorted(memory))  # 组成代码映像以核验固件标识。
assert b"BOOT=DIV_20261011" in image and b"ADC_CONVERSIONS" in image  # 防止误交旧 HEX。
record_path = delivery / "实测记录" / "仿真记录_18工况.csv"  # 当前尚无真实数据的原样记录副本。
assert record_path.read_bytes() == (workspace / "文件" / "仿真记录_18工况.csv").read_bytes()  # 不能将 PC 合成数据写入实测表。
records = list(csv.reader(record_path.read_text(encoding="utf-8-sig").splitlines()))  # 核对保留的原始结构。
assert len(records) == 19 and all(len(row) == 16 for row in records)  # 一行表头、十八行工况、每行十六列。
assert all(all(value == "" for value in row[7:]) for row in records[1:])  # 全部未测字段仍为空白。
for name in ("特征区间_v2.csv", "理论复核结果.json", "仿真记录_18工况.csv"):  # 核验原参数及理论资料完整性。
    assert (delivery / "原始资料" / name).read_bytes() == (workspace / "文件" / name).read_bytes()  # 原文件不得被本任务改变。
diffs = []  # 汇总对源码及配置的可读差异。
for relative in ("Src/main.c", "ADC_CubeMX_Keil.ioc"):  # 两个原工程文件被修改。
    before = (backup / relative).read_text(encoding="utf-8-sig").splitlines(keepends=True)  # 完整备份提供原始版本。
    after = (project / relative).read_text(encoding="utf-8-sig").splitlines(keepends=True)  # 当前实际交付版本。
    diffs.extend(difflib.unified_diff(before, after, fromfile="修改前/" + relative, tofile="修改后/" + relative))  # 生成逐行差异。
(logs / "原工程与修改后工程.diff").write_text("".join(diffs), encoding="utf-8")  # 保存审核依据。
summary = {"type": "PC_LOGIC_TEST_NOT_PROTEUS", "check_groups": checks, "all_passed": True, "nominal_synthetic_cases": nominal_results, "hex_sha256": hashlib.sha256(hex_path.read_bytes()).hexdigest(), "hex_flash_bytes": len(memory), "initial_stack": hex(stack), "reset_vector": hex(reset), "csv_actual_rows_filled": 0, "proteus_nine_cases": "尚未执行"}  # 仅报告实际执行范围。
(logs / "代码与HEX验证结果.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")  # 保存机器可读报告。
print(f"PASS: {checks} 组 PC 逻辑检查；HEX 校验通过；原 CSV 18 行 16 列、实测栏全空；Proteus 尚未执行。")  # 明确区分编译、逻辑测试与电路实测。
