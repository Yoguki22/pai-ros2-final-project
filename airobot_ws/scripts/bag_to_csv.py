import csv
import os
import sys

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

if len(sys.argv) != 3:
    print("Usage: python3 bag_to_csv.py BAG_PATH OUTPUT_DIR")
    sys.exit(1)

bag_path = os.path.expanduser(sys.argv[1])
output_dir = os.path.expanduser(sys.argv[2])
os.makedirs(output_dir, exist_ok=True)

reader = rosbag2_py.SequentialReader()
reader.open(
    rosbag2_py.StorageOptions(uri=bag_path, storage_id="sqlite3"),
    rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    ),
)

topic_types = {
    item.name: item.type
    for item in reader.get_all_topics_and_types()
}

targets = ["/cube1/pose", "/cube2/pose"]
missing = [t for t in targets if t not in topic_types]
if missing:
    print("ERROR: Missing topics:", missing)
    sys.exit(1)

hand_target = ("crane_plus_base", "crane_plus_link_hand")
has_tf = "/tf" in topic_types
if not has_tf:
    print("WARNING: /tf not found; hand CSV will not be created.")

files = {}
writers = {}
counts = {}

def open_csv(name, header):
    f = open(
        os.path.join(output_dir, name),
        "w",
        newline="",
        encoding="utf-8",
    )
    w = csv.writer(f)
    w.writerow(header)
    files[name] = f
    writers[name] = w
    counts[name] = 0

pose_header = [
    "bag_time_sec", "stamp_sec", "stamp_nanosec", "frame_id",
    "x", "y", "z", "qx", "qy", "qz", "qw"
]

for topic in targets:
    name = topic.strip("/").replace("/", "_") + ".csv"
    open_csv(name, pose_header)

if has_tf:
    open_csv(
        "hand_tf.csv",
        [
            "bag_time_sec", "stamp_sec", "stamp_nanosec",
            "parent_frame", "child_frame",
            "x", "y", "z", "qx", "qy", "qz", "qw",
        ],
    )

while reader.has_next():
    topic, data, timestamp_ns = reader.read_next()
    bag_time = timestamp_ns / 1e9

    if topic in targets:
        msg = deserialize_message(data, get_message(topic_types[topic]))
        p = msg.pose.position
        q = msg.pose.orientation
        s = msg.header.stamp
        name = topic.strip("/").replace("/", "_") + ".csv"

        writers[name].writerow([
            bag_time, s.sec, s.nanosec, msg.header.frame_id,
            p.x, p.y, p.z, q.x, q.y, q.z, q.w,
        ])
        counts[name] += 1

    elif topic == "/tf":
        msg = deserialize_message(data, get_message(topic_types[topic]))

        for tr in msg.transforms:
            parent = tr.header.frame_id.lstrip("/")
            child = tr.child_frame_id.lstrip("/")

            if (parent, child) != hand_target:
                continue

            p = tr.transform.translation
            q = tr.transform.rotation
            s = tr.header.stamp

            writers["hand_tf.csv"].writerow([
                bag_time, s.sec, s.nanosec, parent, child,
                p.x, p.y, p.z, q.x, q.y, q.z, q.w,
            ])
            counts["hand_tf.csv"] += 1

for f in files.values():
    f.close()

print("\nConversion complete:")
for name, count in counts.items():
    print(f"{name}: {count} rows")

print(f"Output directory: {output_dir}")
if has_tf and counts.get("hand_tf.csv", 0) == 0:
    print(
        "WARNING: No direct base->hand transform found in /tf. "
        "The TF may use intermediate links; a TF-chain reconstruction "
        "will be needed."
    )
