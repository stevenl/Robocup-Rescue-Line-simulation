# this file has the main class that allows you to simulate your robot

import cv2
import time
from threading import Thread
import numpy as np
import sys

# constant for the "shape" of the image
from image_shape_definition import X, Y, C, BLUE, GREEN, RED, ALPHA

from util import copy_and_paste_image

# the default dimension in centimeter that the camera see horizontally
DEFAULT_CAMERA_X_DIMENSION: float = 10.0

# the default dimension in centimeter that the camera see vertically
DEFAULT_CAMERA_Y_DIMENSION: float = 10.0

# the centimeters the camera is offset from the center of the robot
DEFAULT_CAMERA_X_OFFSET: float = 5.0

# the default wight dimension of the robot in centimeter
DEFAULT_ROBOT_WIGHT: float = 17

# the default PPI (pixel per inch) of the image that get read
DEFAULT_PPI: int = 17

# the default maximum speed of the robot (in cm/s)
DEFAULT_MAX_SPEED: float = 20.0

# the default starting position of the robot presented in cm
DEFAULT_START_POS_X: float = 20.0

# the default starting position of the robot presented in cm
DEFAULT_START_POS_Y: float = 20.0

# the default starting angle of the robot presented in radiant
DEFAULT_START_ANGLE: float = -np.pi * 3 / 4

# the resolution of the top view
DEFAULT_TOP_VIEW_RES_X: int = 1100
# the resolution of the top view
DEFAULT_TOP_VIEW_RES_Y: int = 700

# whether the top vew is enabled or not
DEFAULT_TOP_VIEW_ENABLE: bool = True

# the eventual zoom of the top view
DEFAULT_TOP_VIEW_ZOOM: float = 1.0

# the time step of the simulation, the lower it is the more precise the simulation is
DEFAULT_SIMULATION_TIME_STEP: float = 0.01

# the resolution of the image view by the robot
DEFAULT_OUTPUT_RESOLUTION_X: int = 64
DEFAULT_OUTPUT_RESOLUTION_Y: int = 64


# sum to an x value a vector and return the new x vaue
def vec_sum_x(x: float, angle: float, module: float) -> float:
    return x - np.sin(angle) * module


# sum to an y value a vector and return the new x vaue
def vec_sum_y(y: float, angle: float, module: float) -> float:
    return y - np.cos(angle) * module


class Robot:
    """
    Robot is a class that allows you to simulate a robot.

    to customize it you can change the default parameter when you construct it...

    the robot has one output: the view of the camera that you can access using `get_camera_view`

    and one input: the speed of the motors, that you can control using `set_motors_speeds`
    """

    # set the speed of the motors
    def set_motors_speeds(self, right: int, left: int):
        """use this function to set the speed of the motors of the robot

        Args:
            right (int): speed to set to the right motor, has to be in the -255 to 255 range
            left (int): speed to set to the left motor, has to be in the -255 to 255 range

        """
        right = int(right)
        left = int(left)

        assert (
            -255 <= right <= 255 and -255 <= left <= 255
        ), "the speeds of the motor MUST be in the -255 to 255 range"
        self.__speed_right = right
        self.__speed_left = left

    # return the image
    def get_camera_view(self) -> np.ndarray:
        """
        use this function to get what the robot is seeing from the camera
        """
        image = self.__map
        center = (
            self.__cm_to_pixel(
                vec_sum_x(self.__pos_x, self.__angle, self.__camera_x_offset)
            ),
            self.__cm_to_pixel(
                vec_sum_y(self.__pos_y, self.__angle, self.__camera_x_offset)
            ),
        )
        theta = -self.__angle
        width = self.__cm_to_pixel(self.__camera_x_dimension)
        height = self.__cm_to_pixel(self.__camera_y_dimension)

        theta *= 180 / np.pi

        shape = (
            image.shape[1],
            image.shape[0],
        )  # cv2.warpAffine expects shape in (length, height)

        matrix = cv2.getRotationMatrix2D(center=center, angle=theta, scale=1)
        image = cv2.warpAffine(src=image, M=matrix, dsize=shape)

        x = int(center[0] - width / 2)
        y = int(center[1] - height / 2)

        image = image[y : y + height, x : x + width]

        if image.shape[C] == 4:
            image = image[:, :, 0:3]

        image = cv2.resize(
            image, (self.__output_resolution_x, self.__output_resolution_y)
        )

        return image

    def __init__(
        self,
        map_path: str,
        start_pos_x: float = DEFAULT_START_POS_X,
        start_pos_y: float = DEFAULT_START_POS_Y,
        start_angle: float = DEFAULT_START_ANGLE,
        max_speed: float = DEFAULT_MAX_SPEED,
        ppi: int = DEFAULT_PPI,
        camera_x_dimension: float = DEFAULT_CAMERA_X_DIMENSION,
        camera_y_dimension: float = DEFAULT_CAMERA_Y_DIMENSION,
        camera_y_offset: float = DEFAULT_CAMERA_X_OFFSET,
        robot_wight: float = DEFAULT_ROBOT_WIGHT,
        top_view_res_x: float = DEFAULT_TOP_VIEW_RES_X,
        top_view_res_y: float = DEFAULT_TOP_VIEW_RES_Y,
        top_view_enable: bool = DEFAULT_TOP_VIEW_ENABLE,
        top_view_zoom: float = DEFAULT_TOP_VIEW_ZOOM,
        simulation_time_step: float = DEFAULT_SIMULATION_TIME_STEP,
        output_resolution_x: int = DEFAULT_OUTPUT_RESOLUTION_X,
        output_resolution_y: int = DEFAULT_OUTPUT_RESOLUTION_Y,
    ):
        """
        this is the default constructor, you can use it to do create an instance of the robot

        Args:
            map_path (str): the path of an image that contains a simulation map

            start_pos_x (float): the starting position of the robot in cm, make share to keep it inside the map,
                                    the x ax go left to right.

            start_pos_y (float): the starting position of the robot in cm, make share to keep it inside the map,
                                    the y ax go top to bottom.

            start_angle (float): the starting angle of the robot in radiant,
                                    an alge of 0 make the robot facing up,
                                    the direction of rotation is counter clock wise

            max_speed (float): the maximum speed the robot cna go, in cm/s

            ppi (int): the pixel per inch of the map loaded

            camera_x_dimension (float): how many cm of the floor the camera can see horizontally

            camera_y_dimension (float): how many cm of the floor the camera can see horizontally

            camera_y_offset (float): how many cm the camera is offset from the center of the robot

            robot_wight (float): the wight in cm of the robot, this effects the turning radius

            top_view_res_x (float): the x resolution of the top view the robot will create

            top_view_res_y (float): the y resolution of the top view the robot will create

            top_view_enable (bool): whether the top vew is or not, you can disable it if your CPU is struggling

            top_view_zoom (float): the xoom of the top view, it is used if you are loading a big map

            simulation_time_step (float): what is the lowest time step (in seconds) the simulation will consider,
                                        if this number is lower your simulation will be more precise, but heavier for
                                        your CPU

            output_resolution_x (int): the x resolution of the image that the robot will give you as a result when
                                        calling `get_camera_view`

            output_resolution_y (int): the y resolution of the image that the robot will give you as a result when
                                        calling `get_camera_view`
        """

        # x position in cm of the robot
        self.__pos_x: float = start_pos_x
        # y position in cm of the robot
        self.__pos_y: float = start_pos_y
        # x angle of the robot orientation (in radians)
        self.__angle: float = start_angle
        # maximum speed of the robot in cm/s
        self.__max_speed: float = max_speed
        # pixel per inch of the map the robot has memorized
        self.__ppi: float = ppi
        # the map the robot has memorized
        self.__map = cv2.imread(map_path)
        # the dimension in cm of the horizontal camera view
        self.__camera_x_dimension: float = camera_x_dimension
        # the dimension in cm of the vertical camera view
        self.__camera_y_dimension: float = camera_y_dimension
        # the offset the camera has from the center of the robot in cm
        self.__camera_x_offset: float = camera_y_offset
        # the wight of the robot
        self.__robot_wight: float = robot_wight
        # relative speed (from -255 to 255) of the left motor
        self.__speed_left: int = 0
        # relative speed (from -255 to 255) of the right motor
        self.__speed_right: int = 0
        # a boolean flag used to stopp the updater thread
        self.__thread_running: bool = True
        # the image representing the robot itself
        self.__robot_image = self.__get_robot_image()
        # resolution of the rop view
        self.__top_view_res_x = top_view_res_x
        # resolution of the rop view
        self.__top_view_res_y = top_view_res_y
        # the zoom of the top view
        self.__top_view_zoom = top_view_zoom
        # the time step of the simulation
        self.__simulation_time_step = simulation_time_step
        # the resolution of the output image
        self.__output_resolution_x = output_resolution_x
        self.__output_resolution_y = output_resolution_y
        # launch the top view
        if top_view_enable:
            self.__top_view_thread = Thread(
                target=self.__update_top_view_thread, args=()
            )
            self.__top_view_thread.start()
            if not sys.platform.startswith("win"):
                print(
                    "the automatic top view generation don't work in linux, and is untested in macos, disable",
                    "it using: top_view_enable=False in the robot constructor",
                    "actualy the function works if you don't use cv2.imshow in your program, but it will broke"
                    "if you try to do so",
                    file=sys.stderr,
                )
        # launching the thread that update the position
        self.__updater_thread = Thread(target=self.__position_updater, args=())
        self.__updater_thread.start()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Robot at X:{self.__pos_x} Y:{self.__pos_y} angle:{self.__angle}"

    # disable the thread when finish using it
    def __del__(self):
        self.__thread_running = False

    # the thread that constantly update the position of the robot
    def __position_updater(self):

        min_pos_x = 0
        min_pos_y = 0

        max_pos_x = self.__pixel_to_cm(self.__map.shape[X])
        max_pos_y = self.__pixel_to_cm(self.__map.shape[Y])

        time_sample = time.time()

        input_time = time.time()

        c = 0

        while self.__thread_running:

            c += 1

            actual_time_stamp = (time.time() - input_time) / c

            # self.__pos_x += self.__speed_left/100
            # self.__pos_y += self.__speed_right/100

            # middle point of the right track of the robot
            right_track_x = vec_sum_x(
                self.__pos_x, self.__angle - np.pi / 2, self.__robot_wight / 2
            )
            right_track_y = vec_sum_y(
                self.__pos_y, self.__angle - np.pi / 2, self.__robot_wight / 2
            )

            # middle point of the left track of the robot
            left_track_x = vec_sum_x(
                self.__pos_x, self.__angle + np.pi / 2, self.__robot_wight / 2
            )
            left_track_y = vec_sum_y(
                self.__pos_y, self.__angle + np.pi / 2, self.__robot_wight / 2
            )

            # update the position using the speed information
            right_track_x = vec_sum_x(
                right_track_x,
                self.__angle,
                self.__speed_right / 255.0 * actual_time_stamp * self.__max_speed,
            )
            right_track_y = vec_sum_y(
                right_track_y,
                self.__angle,
                self.__speed_right / 255.0 * actual_time_stamp * self.__max_speed,
            )
            left_track_x = vec_sum_x(
                left_track_x,
                self.__angle,
                self.__speed_left / 255.0 * actual_time_stamp * self.__max_speed,
            )
            left_track_y = vec_sum_y(
                left_track_y,
                self.__angle,
                self.__speed_left / 255.0 * actual_time_stamp * self.__max_speed,
            )

            # update the position of the robot
            self.__pos_x = (right_track_x + left_track_x) / 2
            self.__pos_y = (right_track_y + left_track_y) / 2

            # update the angle
            delta_x = right_track_x - left_track_x
            delta_y = right_track_y - left_track_y

            if delta_x == 0:
                if delta_y >= 0:
                    angle = np.pi / 2
                else:
                    angle = -np.pi / 2
            else:
                angle = np.arctan(-delta_y / delta_x)

                if delta_x <= 0:
                    angle += np.pi

            # keep it in range
            while angle < 0 or angle > np.pi * 2:
                if angle < 0:
                    angle += np.pi * 2
                elif angle > np.pi * 2:
                    angle -= np.pi * 2

            self.__angle = angle

            # keep the robot inside the map
            self.__pos_x = np.clip(self.__pos_x, min_pos_x, max_pos_x)
            self.__pos_y = np.clip(self.__pos_y, min_pos_y, max_pos_y)

            time_to_wait = self.__simulation_time_step - (time.time() - time_sample)
            if time_to_wait < 0:
                print(
                    "Lack of precision due to CPU too slow... try increase the simulation time step",
                    file=sys.stderr,
                )
            else:
                time.sleep(time_to_wait)
            time_sample = time.time()

    # a thread that constantly update the top view (only works in windows)
    def __update_top_view_thread(self):
        while self.__thread_running:
            self.update_top_view()

    # update the top view
    def update_top_view(self):
        robot = self.__get_robot_image()
        image_center = tuple(np.array(robot.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, self.__angle * 180 / np.pi, 1.0)
        robot = cv2.warpAffine(
            robot, rot_mat, robot.shape[1::-1], flags=cv2.INTER_LINEAR
        )

        # put the robot inside the map
        img = copy_and_paste_image(
            paste_to_=self.__map,
            copy_from_=robot,
            middle_point_x=self.__cm_to_pixel(self.__pos_x),
            middle_point_y=self.__cm_to_pixel(self.__pos_y),
        )

        # eventual zoom the image
        if self.__top_view_zoom > 1:
            new_res_x = self.__map.shape[X] / self.__top_view_zoom
            new_res_y = self.__map.shape[Y] / self.__top_view_zoom

            center_x = self.__cm_to_pixel(self.__pos_x)
            center_y = self.__cm_to_pixel(self.__pos_y)

            # the new coordinates of the new map
            x1 = int(center_x - new_res_x / 2)
            y1 = int(center_y - new_res_y / 2)
            x2 = int(center_x + new_res_x / 2)
            y2 = int(center_y + new_res_y / 2)

            # be careful not to overflow
            x1 = np.clip(x1, 0, img.shape[X])
            x2 = np.clip(x2, 0, img.shape[X])
            y1 = np.clip(y1, 0, img.shape[Y])
            y2 = np.clip(y2, 0, img.shape[Y])

            # zoom the image
            img = img[y1:y2, x1:x2, :]

        # resize the image according to user inputs
        og_res_x = img.shape[X]
        og_res_y = img.shape[Y]

        if og_res_x / self.__top_view_res_x > og_res_y / self.__top_view_res_y:
            # res x is ok, scale res y
            new_res_x = self.__top_view_res_x
            new_res_y = int(self.__top_view_res_x / og_res_x * og_res_y)
        else:
            # res y is ok, scale res x
            new_res_y = self.__top_view_res_y
            new_res_x = int(self.__top_view_res_y / og_res_y * og_res_x)

        img = cv2.resize(img, (new_res_x, new_res_y))

        cv2.imshow("TOP VIEW use Robot(..., top_view_enable = False) to disable", img)
        cv2.waitKey(1)
        # time.sleep(0.001)

    # return an image that represent the robot for the visualization
    def __get_robot_image(self):

        # find the max dimension possible
        x_max = float(np.abs(self.__camera_x_offset)) + self.__camera_x_dimension / 2
        y_max = self.__robot_wight / 2

        # find the biggest dimension
        dimension_max = x_max
        if y_max > dimension_max:
            dimension_max = y_max

        # find rhe final dimension with a 1.5 safety margin
        dimension = self.__cm_to_pixel(dimension_max * 2 * np.sqrt(2) * 1.5)

        # create the image
        image = np.zeros(shape=[dimension, dimension, 4], dtype=np.uint8)

        # load the body
        body = cv2.imread("../images/body.png", cv2.IMREAD_UNCHANGED)
        body_dim = self.__cm_to_pixel(self.__robot_wight * 0.7)
        body = cv2.resize(body, (body_dim, body_dim))

        # load the track
        track = cv2.imread("../images/track.png", cv2.IMREAD_UNCHANGED)
        track_y = int(body_dim * 1.3)
        track_x = self.__cm_to_pixel(3)
        track = cv2.resize(track, (track_x, track_y))

        # calculate the center of the image
        center_x = int(image.shape[X] / 2)
        center_y = int(image.shape[Y] / 2)

        # put the track in
        image = copy_and_paste_image(
            image,
            track,
            center_x - self.__cm_to_pixel(self.__robot_wight / 2 * 0.8),
            center_y,
        )
        # put the track in
        image = copy_and_paste_image(
            image,
            track,
            center_x + self.__cm_to_pixel(self.__robot_wight / 2 * 0.8),
            center_y,
        )

        # put the body in
        image = copy_and_paste_image(image, body, center_x, center_y)

        # the coordinates of the camera view
        camera_x_center = center_x - self.__cm_to_pixel(self.__camera_x_offset)
        camera_y_center = center_y

        camera_delta_x = self.__cm_to_pixel(self.__camera_x_dimension / 2)
        camera_delta_y = self.__cm_to_pixel(self.__camera_y_dimension / 2)

        camera_x1 = camera_x_center - camera_delta_x
        camera_y1 = camera_y_center - camera_delta_y

        camera_x2 = camera_x_center + camera_delta_x
        camera_y2 = camera_y_center + camera_delta_y

        # insert the square of the camera
        image = cv2.rectangle(
            image, (camera_y1, camera_x1), (camera_y2, camera_x2), (255, 0, 0, 255), 4
        )

        # insert the transparency

        temp = image[:, :, ALPHA].copy()

        temp = cv2.rectangle(
            temp, (camera_y1, camera_x1), (camera_y2, camera_x2), 0, -1
        )

        image[:, :, ALPHA] = temp

        return image

    def __pixel_to_cm(self, pixel: int) -> float:
        inches = float(pixel) / self.__ppi
        cm = inches * 2.54
        return cm

    def __cm_to_pixel(self, cm: float) -> int:
        inches = cm / 2.54
        pixel = int(inches * self.__ppi)
        return pixel


def test():

    r = Robot(
        "../maps/map_1.png",
        top_view_zoom=8,
        start_angle=0,
        start_pos_x=100,
        start_pos_y=100,
    )

    r.set_motors_speeds(0, 255)

    for i in range(1000):
        img = r.get_camera_view()
        cv2.imshow("view", img)
        cv2.waitKey(1)
        time.sleep(0.02)

    r.__del__()

    # track = cv2.imread("../images/track.png", cv2.IMREAD_UNCHANGED)
    #
    # print(np.shape(track))
    #
    # cv2.imshow("test", track[:,:,3])
    # cv2.waitKey(1000000000)


# test()
