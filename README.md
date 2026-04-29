# PX4-Gazebo-Sim-HITL
This repository is for using a python launch code to integrate the **hitl_bridge.py** and **gazebo harmonic(gz_sim 8)** for **hardware-in-the-loop(HITL)**. The launch code includes the ros_gz_bridge and image_transport to publish the gz topics by ROS2. You can modify it to publish your customize gz_topics. The code supports with the PX4-Autopilot's simulation worlds and models.

## License

This project includes the `hitl_bridge` module, originally created by Noah Olsen and released under the MIT License. You can find the original repository here: https://github.com/noah23olsen/px4-hitl-gazebo-bridge

All other source code in this repository that is not part of the `hitl_bridge` module is developed by the author of this project and is also licensed under the MIT License, unless otherwise noted.

You are free to use, modify, and distribute this software under the terms of the MIT License, as long as the original copyright notice and permission notice are preserved.

## Architecture
<img width="681" height="421" alt="0428" src="https://github.com/user-attachments/assets/1384fe82-5f75-4604-a677-8420132f70ac" />

## Environment
-Ubuntu 24.04

-ROS2 Jazzy

-Gazebo Harmonic (Gz-Sim 8)

-PX4-Autopilot

-QGroundControl

## Virtual Python Environment
I built the environment folder in the HOME Dir
```
cd

# Setup Python environment
python3 -m venv hitl_bridge_venv
source hitl_bridge_venv/bin/activate
pip3 install pymavlink pyserial
```

## Quick Start
```
cd ros_ws/src
mkdir -p HITL
cd HITL
git clone https://github.com/ChengHuan-T/PX4-Gazebo-Sim-HITL.git
```
Open the launch.py in 'HITL/launch/'.

Modify the path with your own (Including PX4, QGC, etc.).

Then build the workspace.
```
cd ~/ros_ws
colcon build
source install/setup.bash
```

## PX4 Flight Controller Setting
1. Connect the autopilot directly to **QGroundControl** via USB.
2. Select Airframe
    1. Open **Setup > Airframes**
    2. Select a **compatible airframe** you want to test. Then click **Apply and Restart** on top-right of the *Airframe Setup* page.
3. Calibrate your **Manual Controller** (RC or Joystick), if needed.
4. Setup HITL Enabled
    1. Under the Vehicle Configuration tab, set the Hardware in the Loop Simulation to Enabled.
       
       <img width="1252" height="1115" alt="image" src="https://github.com/user-attachments/assets/51136cea-9ffa-41eb-840d-b24a1a0e1a0e" />

5. Setup UDP
    1. Under the Application Settings tab of the settings menu, uncheck all *AutoConnect* boxes except for **UDP.**

       <img width="1173" height="618" alt="image" src="https://github.com/user-attachments/assets/3d120b60-9969-4d82-8207-c2e35087332e" />

        
6. Reboot the Flight Controller

## Launch
```
ros2 launch HITL hitl_test.launch.py  # Default world and model are baylands and x500_gimbal
```
It will show some plugin errors like 'libOpticalFlowSystem.so', 'libGstCameraSystem.so', and 'MotorFailurePlugin'. But they don't really matter and can be ignore.

Once you see something like this below and the frequencies of the sensors then it launched successfully.
```
[python3-2]   === SENSOR DUMP (first HIL_SENSOR) ===
[python3-2]   time_us:  177735046544
[python3-2]   accel:    (0.0064, 0.0161, -0.0096)  [expect ~(0, 0, 0)]
[python3-2]   gyro:     (-0.0016, -0.0005, -0.0004)  [expect ~(0, 0, 0)]
[python3-2]   mag:      (0.223725, -0.053569, 0.426391)
[python3-2]   baro:     1013.26 hPa  alt=-0.04 m
[python3-2]   fields:   0x1bff
[python3-2]   ========================================
```
Also you can launch with different world and model.
```
ros2 launch HITL hitl_test.launch.py world:=lawn    # Launch with different world
ros2 launch HITL hitl_test.launch.py vehicle:=x500  # Launch with different model
ros2 launch HITL hitl_test.launch.py world"=lawn vehicle:=x500
```

You can monitor with:
```
gz topic -l
# Or
ros2 topic list
```

Once you want to see the image topic, you can use rqt to subscribe it.
```
ros2 run rqt_image_view rqt_image_view /world/baylands/model/x500_gimbal/link/camera_link/sensor/camera/image  # Default setting
```
