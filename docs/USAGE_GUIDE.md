# 🗺️ Daily Usage Guide

Everything is set up. Follow these steps each time you want to map.

---

## Step 1: Start the Lidar on the Uno Q

SSH from your laptop:
```bash
ssh arduino@192.168.1.17
# Password: Askaban78@#

bash /home/arduino/start_rplidar.sh
```

Verify it's running:
```bash
sudo docker logs -f rplidar
# You should see: "RPLIDAR running on /dev/ttyUSB0"
# Press Ctrl+C to exit the log (the container keeps running)
exit
```

---

## Step 2: Start Mapping on the Laptop

Open a terminal on your laptop:
```bash
cd ~/my_robot_ws
colcon build --packages-select my_robot_nav
source install/setup.bash
./scripts/start_handheld_mapping.sh
```

Wait ~7 seconds until you see:
```
[slam_toolbox]: Configuring
[slam_toolbox]: Activating
Registering sensor: [Custom Described Lidar]
```

---

## Step 3: View the Map in RViz

1. Set **Fixed Frame** → `map`
2. Click **Add** → **By topic** → `/map` → **Map**
3. (Optional) Also add `/scan_reliable` → **LaserScan** to see live laser points

---

## Step 4: Walk and Map

Pick up the Uno Q + Lidar (powered by a power bank) and walk slowly around the room.  
The map grows in real-time in RViz.

**Tips:**
- Move slowly, especially when turning
- Revisit areas to help the algorithm close loops
- Keep the Lidar level (don't tilt it)

---

## Step 5: Save the Map

Open a **second terminal** while the mapping is still running:
```bash
cd ~/my_robot_ws
source install/setup.bash
ros2 run nav2_map_server map_saver_cli -f src/my_robot_nav/maps/my_map
```

This saves `my_map.pgm` + `my_map.yaml` in the `maps/` directory.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No `/scan` data on laptop | SSH to Uno Q and run `bash /home/arduino/start_rplidar.sh` |
| Lidar not spinning | Run `sudo chmod a+rw /dev/ttyUSB0 && python3 /home/arduino/spin_test.py` on the Uno Q, then restart the container |
| Map not appearing in RViz | Wait for `Registering sensor` message in the terminal. Make sure Fixed Frame is `map` |
| Power bank reconnect reboots Uno Q | SSH back in and run `bash /home/arduino/start_rplidar.sh` again |
