import csv
import os
import sys
from collections import defaultdict

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

from geometry_msgs.msg import TransformStamped
from tf2_ros import Buffer
from rclpy.time import Time


if len(sys.argv) != 3:
    print("Usage: python3 tf_to_csv.py BAG_PATH OUTPUT_DIR")
    sys.exit(1)

bag_path = os.path.expanduser(sys.argv[1])
output_dir = os.path.expanduser(sys.argv[2])
os.makedirs(output_dir, exist_ok=True)

reader = rosbag2_py.SequentialReader()
reader.open(
    rosbag2_py.StorageOptions(
        uri=bag_path,
        storage_id="sqlite3"
    ),
    rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr"
    )
)

topic_types = {
    item.name: item.type
    for item in reader.get_all_topics_and_types()
}

tf_topics = ["/tf", "/tf_static"]
available = [t for t in tf_topics if t in topic_types]

if not available:
    print("ERROR: Neither /tf nor /tf_static exists in this bag.")
    sys.exit(1)

# Read all TF messages first.
# Store dynamic TFs by timestamp and static TFs separately.
dynamic_by_time = defaultdict(list)
static_transforms = []
bag_times_by_stamp = defaultdict(list)

while reader.has_next():
    topic, data, bag_timestamp_ns = reader.read_next()

    if topic not in tf_topics:
        continue

    msg_type = get_message(topic_types[topic])
    msg = deserialize_message(data, msg_type)

    for tf in msg.transforms:
        if topic == "/tf_static":
            static_transforms.append(tf)
        else:
            sec = tf.header.stamp.sec
            nsec = tf.header.stamp.nanosec
            stamp_ns = sec * 1_000_000_000 + nsec

            dynamic_by_time[stamp_ns].append(tf)
            bag_times_by_stamp[stamp_ns].append(
                bag_timestamp_ns / 1e9
            )

print(f"Dynamic TF timestamps: {len(dynamic_by_time)}")
print(f"Static transforms: {len(static_transforms)}")

# Build a fresh buffer for each timestamp so that only transforms
# available up to that timestamp are used.
output_path = os.path.join(output_dir, "hand_pose.csv")
count = 0
failed = 0

with open(output_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "bag_time_sec",
        "stamp_sec",
        "stamp_nanosec",
        "frame_id",
        "child_frame_id",
        "x", "y", "z",
        "qx", "qy", "qz", "qw"
    ])

    buffer = Buffer()

    # Insert static transforms once.
    for tf in static_transforms:
        try:
            buffer.set_transform_static(tf, "rosbag")
        except Exception as e:
            print(
                "WARN: static TF insert failed:",
                tf.header.frame_id,
                "->",
                tf.child_frame_id,
                str(e)
            )

    for stamp_ns in sorted(dynamic_by_time):
        transforms = dynamic_by_time[stamp_ns]

        for tf in transforms:
            try:
                buffer.set_transform(tf, "rosbag")
            except Exception:
                pass

        sec = stamp_ns // 1_000_000_000
        nsec = stamp_ns % 1_000_000_000

        try:
            result = buffer.lookup_transform(
                "crane_plus_base",
                "crane_plus_link_hand",
                Time(seconds=int(sec), nanoseconds=int(nsec))
            )

            t = result.transform.translation
            q = result.transform.rotation

            bag_times = bag_times_by_stamp[stamp_ns]
            bag_time = min(bag_times) if bag_times else ""

            writer.writerow([
                bag_time,
                sec,
                nsec,
                result.header.frame_id,
                result.child_frame_id,
                t.x, t.y, t.z,
                q.x, q.y, q.z, q.w
            ])
            count += 1

        except Exception:
            failed += 1

print(f"hand rows: {count}")
print(f"failed TF lookups: {failed}")
print(f"CSV saved to: {output_path}")
