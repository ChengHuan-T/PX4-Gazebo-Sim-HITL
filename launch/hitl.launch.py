import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument, TimerAction, LogInfo, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration, PythonExpression, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # --- Directory Setup ---
    home = os.path.expanduser("~")
    # pkg_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    # px4_dir = os.path.abspath(os.path.join(pkg_dir, '..', '..'))
    px4_dir = os.path.join(home, "repos/PX4-Autopilot")                       # PX4 Dir
    bridge_script_dir = os.path.join(home, "ros_ws/src/HITL")                 # hitl_bridge Dir
    venv_python = os.path.join(home, "hitl_bridge_venv/bin/python3")          # Venv for HITL

    # pkg_share = FindPackageShare('HITL')

    # --------------------------------- #
    # Launch Arguments                  #
    # --------------------------------- #

    vehicle = LaunchConfiguration('vehicle')
    world = LaunchConfiguration('world')
    bridge_config_file = LaunchConfiguration('bridge')

    declare_vehicle_cmd = DeclareLaunchArgument(
        'vehicle',
        default_value='x500_gimbal',
        description='PX4 vehicle model (e.g., x500)')

    declare_world_cmd = DeclareLaunchArgument(
        'world',
        default_value='baylands',
        description='Gazebo world (e.g., default, baylands)')
    
    declare_bridge_config_cmd = DeclareLaunchArgument(
        'bridge',
        default_value='x500',
        description='Configuration YAML file for ROS-Gazebo bridge')
    
    # --------------------------------- #
    # Environment Variables             #
    # --------------------------------- #

    setup_gz_path = [
        SetEnvironmentVariable(name='PYTHONUNBUFFERED', value='1'),
        SetEnvironmentVariable(name='use_sim_time', value='True'),
        SetEnvironmentVariable(name='PYTHONPATH', value='/usr/lib/python3/dist-packages'),
        SetEnvironmentVariable(name='GZ_SIM_RESOURCE_PATH', value=[
            os.path.join(bridge_script_dir, 'models'), ':',
            os.path.join(px4_dir, 'Tools/simulation/gz/models'), ':',
            os.path.join(px4_dir, 'Tools/simulation/gz/worlds'), ':',
        ]),
        SetEnvironmentVariable(name='GZ_SIM_SERVER_CONFIG_PATH', 
            value=os.path.join(px4_dir, "Tools/simulation/gz/server.config")),

        # Using GPU
        SetEnvironmentVariable(name='__NV_PRIME_RENDER_OFFLOAD', value='1'),
        SetEnvironmentVariable(name='__GLX_VENDOR_LIBRARY_NAME', value='nvidia'),
    ]

    # ----------------------------------- #
    # 1. Gazebo Sim                       #
    # ----------------------------------- #

    # Use a combined command or separate server/gui calls
    start_gz_server = ExecuteProcess(
        cmd=[
            'gz', 'sim', '-s', '-r', 
            PythonExpression(["'", world, "' + '.sdf'"]) # Added inner quotes
        ],
        output='screen'
    )

    start_gz_gui = TimerAction(
        period=2.0,
        actions=[ExecuteProcess(cmd=['gz', 'sim', '-g'], output='screen')]
    )

    model_path = [px4_dir, '/Tools/simulation/gz/models/', vehicle, '/model.sdf']

    start_gz_spawn_model = TimerAction(
        period=10.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                output='screen',
                arguments=[
                    '-world', world,      
                    '-file', model_path,
                    '-name', vehicle,     
                    '-z', '0.0',          # Initial Height
                ],
            ),
        ]
    )

    # ------------------------------ #
    # 2. HITL Bridge                 #
    # ------------------------------ #

    start_hitl_bridge = ExecuteProcess(
        # cmd=[venv_python, os.path.join(bridge_script_dir, 'hitl_bridge.py')],
        cmd=[
            venv_python, 
            os.path.join(bridge_script_dir, 'hitl_bridge.py'),
            '--world', world,
            '--model', vehicle
        ],
        output='screen'
    )

    # ---------------------------- #
    # 3. QGroundControl            #
    # ---------------------------- #

    start_qgc = TimerAction(
        period=20.0,
        actions=[
            ExecuteProcess(
                cmd=['/home/william/william/QGroundControl-x86_64.AppImage'],   # QGC Dir
                output='log'
            )
        ]
    )
    
    # ------------------------------ #
    # 4. Gazebo Bridge               #
    # ------------------------------ #

    clock_bridge_arg = PythonExpression(["'/world/' + '", world, "' + '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'"])
    air_pressure_bridge_arg = PythonExpression(["'/world/' + '", world, "' + '/model/' + '", vehicle, "' + '/link/base_link/sensor/air_pressure_sensor/air_pressure@sensor_msgs/msg/FluidPressure[gz.msgs.FluidPressure'"])
    imu_bridge_arg = PythonExpression(["'/world/' + '", world, "' + '/model/' + '", vehicle, "' + '/link/base_link/sensor/imu_sensor/imu@sensor_msgs/msg/Imu[gz.msgs.IMU'"])
    mag_bridge_arg = PythonExpression(["'/world/' + '", world, "' + '/model/' + '", vehicle, "' + '/link/base_link/sensor/magnetometer_sensor/magnetometer@sensor_msgs/msg/MagneticField[gz.msgs.Magnetometer'"])
    navsat_bridge_arg = PythonExpression(["'/world/' + '", world, "' + '/model/' + '", vehicle, "' + '/link/base_link/sensor/navsat_sensor/navsat@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat'"])

    gz_ros_bridge_node = TimerAction(
        period=20.0,
        actions=[
            LogInfo(msg=["Launching ros_gz_bridge with dynamic arguments..."]),
            Node(
                package='ros_gz_bridge',
                executable='parameter_bridge',
                arguments=[
                    clock_bridge_arg,
                    air_pressure_bridge_arg,
                    imu_bridge_arg,
                    mag_bridge_arg,
                    navsat_bridge_arg
                ],
                output='screen',
            ),
            
            # Image Topic
            Node(
                package='ros_gz_image',
                executable='image_bridge',
                name='gz_image_bridge',
                arguments=[
                    PythonExpression(["'/world/",world,"/model/' + '", vehicle, "' + '/link/camera_link/sensor/camera/image'"])
                ],
                parameters=[{
                    "compressed.jpeg_quality": 30,     # Lower is worse quality
                    "unsubscribed_idle_timeout": 1.0,  # Timeout to stop publishing if no one is watching
                    "lazy": True,
                    
                }],
                output='screen',
            ),
        ],
    ) 

    return LaunchDescription([
        *setup_gz_path,
        declare_vehicle_cmd,
        declare_world_cmd,
        declare_bridge_config_cmd,
        start_gz_server,
        start_gz_gui,
        start_gz_spawn_model,
        start_hitl_bridge,
        start_qgc,
        gz_ros_bridge_node,
    ])
