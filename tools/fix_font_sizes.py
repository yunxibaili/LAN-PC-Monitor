"""批量替换硬编码 font-size: Npx → TT token"""
import os, re

ROOT = "host/gui"
MAP = {
    32: "TT.NUMERIC_LARGE['size']",
    28: "TT.NUMERIC_LARGE['size']",
    24: "TT.TITLE_LARGE['size']",
    20: "TT.TITLE_MEDIUM['size']",
    18: "TT.TITLE_SMALL['size']",
    16: "TT.TITLE_SMALL['size']",
    15: "TT.TITLE_SMALL['size']",
    14: "TT.BODY['size']",
    13: "TT.BODY['size']",
    12: "TT.BODY_SMALL['size']",
    11: "TT.CAPTION['size']",
    10: "TT.CAPTION['size']",
    9:  "TT.CAPTION['size']",
}
TT_IMPORT = "from host.gui.theme.typography import ThemeTypography as TT"
total = 0

for dirpath, _, filenames in os.walk(ROOT):
    for fn in filenames:
        if not fn.endswith(".py") or "archive" in dirpath:
            continue
        fp = os.path.join(dirpath, fn)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        orig = content

        # font-size: Npx 或 font-size:Npx，后面跟 ; 或 " 或 空格
        for px, token in sorted(MAP.items(), key=lambda x: -x[0]):
            pattern = rf"(font-size:\s?){px}px(?=[;\"'\s])"
            content = re.sub(pattern, rf"\g<1>{token}px", content)

        if content != orig:
            count = len(re.findall(r"font-size:\s?\d+px", orig)) - len(re.findall(r"font-size:\s?\d+px", content))
            total += count
            # 添加 TT import
            if "TT." in content and TT_IMPORT not in content:
                content = content.replace(
                    "from host.gui.theme.colors import ThemeColors as TC",
                    "from host.gui.theme.colors import ThemeColors as TC\n" + TT_IMPORT
                )
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  {fn}: {count} 处")

print(f"\n总计替换: {total} 处")
