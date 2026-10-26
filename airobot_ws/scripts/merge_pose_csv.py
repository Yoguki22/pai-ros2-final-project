import csv
import os
import bisect

base = os.path.expanduser("~/dataset/csv/drop_cube/ep3")


def load_csv(filename):
    path = os.path.join(base, filename)
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        row["_time"] = (
            float(row["stamp_sec"])
            + float(row["stamp_nanosec"]) / 1e9
        )

    return rows


cube1 = load_csv("cube1_pose.csv")
cube2 = load_csv("cube2_pose.csv")
hand = load_csv("hand_pose.csv")

if not hand:
    raise RuntimeError("hand_pose.csv is empty")

hand_times = [r["_time"] for r in hand]

output_path = os.path.join(base, "merged_pose.csv")
max_time_difference = 0.075  # seconds

with open(output_path, "w", newline="") as f:
    writer = csv.writer(f)

    header = [
        "time_sec",
        "hand_time_sec",
        "hand_time_diff_sec",
        "hand_x_base", "hand_y_base", "hand_z_base",
        "hand_qx", "hand_qy", "hand_qz", "hand_qw",
    ]

    for prefix in ("cube1", "cube2"):
        header += [
            f"{prefix}_x_world",
            f"{prefix}_y_world",
            f"{prefix}_z_world",
            f"{prefix}_qx",
            f"{prefix}_qy",
            f"{prefix}_qz",
            f"{prefix}_qw",
        ]

    writer.writerow(header)

    hand_matched = 0
    hand_unmatched = 0

    # Use cube1 timestamps as the main time series.
    cube2_times = [r["_time"] for r in cube2]
    cube2_index = 0

    for c1 in cube1:
        t = c1["_time"]

        # Find nearest hand sample.
        i = bisect.bisect_left(hand_times, t)
        candidates = []
        if i < len(hand):
            candidates.append(i)
        if i > 0:
            candidates.append(i - 1)

        hi = min(candidates, key=lambda j: abs(hand_times[j] - t))
        h = hand[hi]
        dt = abs(h["_time"] - t)

        # Find nearest cube2 sample.
        j = bisect.bisect_left(cube2_times, t)
        candidates2 = []
        if j < len(cube2):
            candidates2.append(j)
        if j > 0:
            candidates2.append(j - 1)

        if candidates2:
            c2 = cube2[min(
                candidates2,
                key=lambda k: abs(cube2_times[k] - t)
            )]
        else:
            c2 = None

        if dt <= max_time_difference:
            hand_matched += 1
            hand_values = [
                h["x"], h["y"], h["z"],
                h["qx"], h["qy"], h["qz"], h["qw"],
            ]
        else:
            hand_unmatched += 1
            hand_values = [""] * 7

        if c2 is not None:
            cube2_values = [
                c2["x"], c2["y"], c2["z"],
                c2["qx"], c2["qy"], c2["qz"], c2["qw"],
            ]
        else:
            cube2_values = [""] * 7

        writer.writerow([
            t,
            h["_time"] if dt <= max_time_difference else "",
            dt if dt <= max_time_difference else "",
            *hand_values,
            c1["x"], c1["y"], c1["z"],
            c1["qx"], c1["qy"], c1["qz"], c1["qw"],
            *cube2_values,
        ])

print(f"Output: {output_path}")
print(f"Rows: {len(cube1)}")
print(f"Hand matched within {max_time_difference:.3f} s: {hand_matched}")
print(f"Hand unmatched: {hand_unmatched}")
