"""仅在新 Proteus 副本中修改可读的电源轨脚本，不修改未知格式的二进制原理图。"""
from pathlib import Path  # 明确定位源文件和新输出文件。
import zipfile  # Proteus pdsprj 是包含原理图、缓存和脚本的 ZIP 容器。
import hashlib  # 记录修改前后摘要以便核对。

delivery = Path(__file__).resolve().parents[1]  # 定位本次独立交付目录。
source = delivery / "Proteus工程副本" / "DIVject.pdsprj"  # 使用已经复制的工程，原始工程保持不变。
target = source.with_name("解决隐藏VDD误接5V_DIVject.pdsprj")  # 新工程用所解决的问题命名。
assert not target.exists(), "目标已存在，停止以免覆盖"  # 防止重复执行覆盖本地变更。
with zipfile.ZipFile(source) as original:  # 读取容器，保留成员名称与元信息。
    old_rails = original.read("SCRIPTS/PWRRAILS.DAT")  # 读取文本电源轨定义。
    assert b"{VCC/VDD=5,POWER}" in old_rails, "原始电源轨与检查结果不一致"  # 必须匹配实际发现的问题。
    new_rails = old_rails.replace(b"{VCC/VDD=5,POWER}", b"{VCC/VDD=3.3,POWER}")  # 将 VDD 与 3.3V 已绑定的轨电压修正为 3.3V。
    with zipfile.ZipFile(target, "w") as changed:  # 只写入新命名文件。
        for entry in original.infolist():  # 保留完整工程所有成员。
            content = new_rails if entry.filename == "SCRIPTS/PWRRAILS.DAT" else original.read(entry.filename)  # 其余成员逐字节保持原样。
            changed.writestr(entry, content)  # 使用原 ZIP 元信息写回该成员。
with zipfile.ZipFile(source) as original, zipfile.ZipFile(target) as changed:  # 重新打开输出验证容器完整性。
    assert changed.testzip() is None, "新工程 ZIP 校验失败"  # 检查每个成员 CRC。
    differences = [name for name in original.namelist() if original.read(name) != changed.read(name)]  # 找到实际变更成员。
    assert differences == ["SCRIPTS/PWRRAILS.DAT"], differences  # 保证没有改动二进制 DSN 和 CDB。
report = "原工程 SHA256=" + hashlib.sha256(source.read_bytes()).hexdigest() + "\n"  # 记录源工程摘要。
report += "新工程 SHA256=" + hashlib.sha256(target.read_bytes()).hexdigest() + "\n"  # 记录输出摘要。
report += "唯一变更成员：SCRIPTS/PWRRAILS.DAT\n原内容：\n" + old_rails.decode() + "新内容：\n" + new_rails.decode()  # 留下可复核的文本差异。
report += "ZIP CRC 验证通过；ROOT.DSN、ROOT.CDB、GRAPHS.DAT、PROJECT.XML 保持一致。\nProteus 图形界面复开、SW4/SW5 添加、115200 设置及九工况仿真：尚未执行。\n"  # 不把容器检查冒充实际仿真。
(delivery / "验证日志" / "电源轨修改验证.txt").write_text(report, encoding="utf-8")  # 保存真实执行日志。
print(report)  # 将核查结果显示给当前任务。
