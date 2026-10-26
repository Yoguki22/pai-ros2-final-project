from pathlib import Path
import xml.etree.ElementTree as ET

source = Path("sorting_table.sdf")
output = Path("sorting_table_pose.sdf")

targets = {"cube1", "cube2"}

plugin_xml = """
<plugin filename="ignition-gazebo-pose-publisher-system"
        name="gz::sim::systems::PosePublisher">
  <publish_link_pose>true</publish_link_pose>
  <publish_collision_pose>false</publish_collision_pose>
  <publish_visual_pose>false</publish_visual_pose>
  <publish_nested_model_pose>false</publish_nested_model_pose>
</plugin>
"""

tree = ET.parse(source)
root = tree.getroot()

found = set()

for model in root.iter("model"):
    name = model.get("name")

    if name not in targets:
        continue

    found.add(name)

    # 二重挿入を防止
    exists = any(
        p.get("name") == "gz::sim::systems::PosePublisher"
        for p in model.findall("plugin")
    )

    if not exists:
        plugin = ET.fromstring(plugin_xml)
        model.append(plugin)
        print(f"追加: {name}")
    else:
        print(f"設定済み: {name}")

missing = targets - found
if missing:
    raise SystemExit(f"エラー: モデルが見つかりません: {missing}")

ET.indent(tree, space="  ")
tree.write(output, encoding="UTF-8", xml_declaration=True)

# 出力ファイルを再読み込みして XML 構文を検証
ET.parse(output)

print(f"\n完了: {output}")
print("元の sorting_table.sdf は変更していません。")
