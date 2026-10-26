import csv
import os
import matplotlib.pyplot as plt

base = os.path.expanduser("~/dataset/csv/drop_cube/ep3")

def load_cube(filename):
    with open(os.path.join(base, filename), newline="") as f:
        rows = list(csv.DictReader(f))

    t = [
        float(r["stamp_sec"]) + float(r["stamp_nanosec"]) / 1e9
        for r in rows
    ]

    x = [float(r["x"]) for r in rows]
    y = [float(r["y"]) for r in rows]
    z = [float(r["z"]) for r in rows]

    return t, x, y, z

fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)

for name in ["cube1_pose.csv", "cube2_pose.csv"]:
    t, x, y, z = load_cube(name)
    t = [v - t[0] for v in t]
    label = name.replace("_pose.csv", "")

    axes[0].plot(t, x, label=label)
    axes[1].plot(t, y, label=label)
    axes[2].plot(t, z, label=label)

axes[0].set_ylabel("X (m)")
axes[1].set_ylabel("Y (m)")
axes[2].set_ylabel("Z (m)")
axes[2].set_xlabel("Time from start (s)")

for ax in axes:
    ax.grid(True)
    ax.legend()

fig.suptitle("Cube position over time")
fig.tight_layout()

output = os.path.join(base, "cube_position.png")
fig.savefig(output, dpi=150)
print(f"Saved: {output}")

plt.show()
