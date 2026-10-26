import csv
import os
import sys

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

bag_path = os.path.expanduser(sys.argv[1])
output_dir = os.path.expanduser(sys.argv[2])

os.makedirs(output_dir, exist_ok=True)

reader = rosbag2_py.SequentialReader()
reader.open(
    rosbag2_py.StorageOptions(uri=bag_path, storage_id='sqlite3'),
    rosbag2_py.ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr'
    )
)

topic_types = {
    item.name: item.type
    for item in reader.get_all_topics_and_types()
}

targets = ['/cube1/pose', '/cube2/pose']
writers = {}
files = {}
counts = {topic: 0 for topic in targets}

for topic in targets:
    if topic not in topic_types:
        print(f'ERROR: {topic} not found in bag')
        sys.exit(1)

    filename = topic.strip('/').replace('/', '_') + '.csv'
    f = open(os.path.join(output_dir, filename), 'w', newline='')
    writer = csv.writer(f)
    writer.writerow([
        'bag_time_sec', 'stamp_sec', 'stamp_nanosec', 'frame_id',
        'x', 'y', 'z', 'qx', 'qy', 'qz', 'qw'
    ])
    files[topic] = f
    writers[topic] = writer

while reader.has_next():
    topic, data, timestamp_ns = reader.read_next()

    if topic not in targets:
        continue

    msg_type = get_message(topic_types[topic])
    msg = deserialize_message(data, msg_type)

    p = msg.pose.position
    q = msg.pose.orientation
    stamp = msg.header.stamp

    writers[topic].writerow([
        timestamp_ns / 1e9,
        stamp.sec, stamp.nanosec, msg.header.frame_id,
        p.x, p.y, p.z,
        q.x, q.y, q.z, q.w
    ])
    counts[topic] += 1

for f in files.values():
    f.close()

for topic, count in counts.items():
    print(f'{topic}: {count} rows')

print(f'CSV saved to: {output_dir}')
