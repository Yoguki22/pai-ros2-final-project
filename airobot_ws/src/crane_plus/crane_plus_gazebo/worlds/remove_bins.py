import xml.etree.ElementTree as ET
from pathlib import Path

sdf_file = Path("sorting_table.sdf")

# SDFファイルを読み込む
tree = ET.parse(sdf_file)
root = tree.getroot()

# world要素を取得する
world = root.find("world")
if world is None:
    raise RuntimeError("SDF内にworld要素が見つかりません")

# 削除対象のモデル名
targets = {"red_bin", "white_bin"}

removed = []
for model in list(world.findall("model")):
    if model.get("name") in targets:
        removed.append(model.get("name"))
        world.remove(model)

# 削除結果を確認する
missing = targets - set(removed)
if missing:
    raise RuntimeError(
        f"削除対象が見つかりません: {', '.join(sorted(missing))}"
    )

# 元ファイルへ保存する
ET.indent(tree, space="  ")
tree.write(sdf_file, encoding="UTF-8", xml_declaration=True)

print("削除完了:", ", ".join(removed))
print("cube1、cube2、机、床、太陽などは維持しました")
print("保存先:", sdf_file.resolve())
