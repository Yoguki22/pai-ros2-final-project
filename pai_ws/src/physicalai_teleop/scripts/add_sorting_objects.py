#!/usr/bin/env python3

import sys
import rclpy
from rclpy.node import Node
from moveit_msgs.srv import ApplyPlanningScene
from moveit_msgs.msg import PlanningScene, CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose


class AddSortingObjects(Node):
    def __init__(self):
        super().__init__('add_sorting_objects')
        self.client = self.create_client(
            ApplyPlanningScene, '/apply_planning_scene'
        )

    def add_box(self, scene, name, x, y, z, sx, sy, sz, color=None):
        obj = CollisionObject()
        obj.header.frame_id = 'world'
        obj.id = name

        shape = SolidPrimitive()
        shape.type = SolidPrimitive.BOX
        shape.dimensions = [sx, sy, sz]

        pose = Pose()
        pose.position.x = x
        pose.position.y = y
        pose.position.z = z
        pose.orientation.w = 1.0

        obj.primitives.append(shape)
        obj.primitive_poses.append(pose)
        obj.operation = CollisionObject.ADD
        scene.world.collision_objects.append(obj)

    def run(self):
        self.get_logger().info('Waiting for MoveIt service...')
        if not self.client.wait_for_service(timeout_sec=10.0):
            self.get_logger().error('/apply_planning_scene is unavailable')
            return False

        scene = PlanningScene()
        scene.is_diff = True

        # 仕分け箱：底面と4枚の側面
        for prefix, x, y in [
            ('red_bin', 0.15, 0.20),
            ('white_bin', 0.15, -0.20),
        ]:
            self.add_box(
                scene, prefix + '_floor',
                x, y, 0.925, 0.14, 0.14, 0.01
            )
            self.add_box(
                scene, prefix + '_wall_y_plus',
                x, y + 0.07, 0.965, 0.14, 0.01, 0.08
            )
            self.add_box(
                scene, prefix + '_wall_y_minus',
                x, y - 0.07, 0.965, 0.14, 0.01, 0.08
            )
            self.add_box(
                scene, prefix + '_wall_x_plus',
                x + 0.07, y, 0.965, 0.01, 0.14, 0.08
            )
            self.add_box(
                scene, prefix + '_wall_x_minus',
                x - 0.07, y, 0.965, 0.01, 0.14, 0.08
            )

        # 物体
        self.add_box(
            scene, 'cube1_blue',
            0.00, 0.00, 0.96, 0.04, 0.04, 0.04
        )
        self.add_box(
            scene, 'cube2_yellow',
            0.00, -0.10, 0.96, 0.04, 0.04, 0.04
        )

        request = ApplyPlanningScene.Request()
        request.scene = scene
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)

        if future.done() and future.result() is not None:
            success = future.result().success
            self.get_logger().info(f'Planning Scene update success: {success}')
            return success

        self.get_logger().error('Timed out while updating Planning Scene')
        return False


def main():
    rclpy.init()
    node = AddSortingObjects()
    try:
        success = node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
