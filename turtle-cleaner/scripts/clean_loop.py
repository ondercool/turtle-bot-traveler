#!/usr/bin/env python3
import rospy
import argparse
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from math import atan2, sqrt, pow


class Cleaner:
    def __init__(self):
        self.argparser = argparse.ArgumentParser()

        self.argparser.add_argument(
            "--coordinates",
            required=True,
            nargs="+",
            type=float,
            help="Coordinates you want your robot to clean",
        )
        self.args = self.argparser.parse_args()

        self.validate_arguments()

        # defining pub,sub, vel_msg, pose_msg and rate
        rospy.init_node("turtle_cleaner_node", anonymous=True)

        rospy.loginfo("Turtle Cleaner Node has started!!!")
        self.pose_sub = rospy.Subscriber(
            "/turtle1/pose", Pose, callback=self.update_pose
        )
        self.vel_pub = rospy.Publisher("/turtle1/cmd_vel", Twist, queue_size=10)
        self.pose = Pose()
        self.rate = rospy.Rate(10)

        # having (x,y) coordinates list and turning them into an array of goal_points
        # for ex: [1, 2, 3, 4] will be turned into [(1, 2),(3, 4)]
        self.spot_list = [
            (self.args.coordinates[i], self.args.coordinates[i + 1])
            for i in range(0, len(self.args.coordinates) - 1, 2)
        ]

    def validate_arguments(self):
        if len(self.args.coordinates) % 2 != 0:
            raise ValueError(
                "Enter a set of coordinates, e.g even number of entries is required!!!"
            )
        if all([(i >= 0.0 and i <= 11.0) for i in self.args.coordinates]) != True:
            raise ValueError("Turtle-bot moves between 0-11 for both the axes!!!")

    def update_pose(self, pose_msg):
        self.pose = pose_msg
        self.pose.x = round(self.pose.x, 4)
        self.pose.y = round(self.pose.y, 4)

    def steering_angle(self, goal_pose):
        return atan2(goal_pose.y - self.pose.y, goal_pose.x - self.pose.x)

    def euclidian_distance(self, goal_pose):
        return sqrt(
            pow(goal_pose.x - self.pose.x, 2) + pow(goal_pose.y - self.pose.y, 2)
        )

    def angular_vel(self, goal_pose, constant=7):
        return constant * (self.steering_angle(goal_pose) - self.pose.theta)

    def linear_vel(self, goal_pose, constant=1.5):
        return constant * self.euclidian_distance(goal_pose)

    def move_to_goal(self, goal_coordinates):
        goal_pose = Pose()
        goal_pose.x = goal_coordinates[0]
        goal_pose.y = goal_coordinates[1]

        distance_tolerance = 0.5
        vel_msg = Twist()

        while self.euclidian_distance(goal_pose) >= distance_tolerance:
            vel_msg.linear.x = self.linear_vel(goal_pose)
            vel_msg.linear.y = 0.0
            vel_msg.linear.z = 0.0
            vel_msg.angular.x = 0.0
            vel_msg.angular.y = 0.0
            vel_msg.angular.z = self.angular_vel(goal_pose)

            self.vel_pub.publish(vel_msg)

            self.rate.sleep()

        vel_msg.linear.x = 0
        vel_msg.angular.z = 0
        self.vel_pub.publish(vel_msg)

        rospy.loginfo(f"Current Location: ({self.pose.x}, {self.pose.y})")

    def execute_path(self):
        for point in self.spot_list:
            self.move_to_goal(point)
        print("Given spots are fully cleaned!!!")


if __name__ == "__main__":
    try:
        turtle_cleaner = Cleaner()
        turtle_cleaner.execute_path()
    except rospy.ROSInterruptException as err:
        print(err)
