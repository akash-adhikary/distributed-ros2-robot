#!/usr/bin/env python3
"""
Manhattan Map Regularizer & Orthogonal Wall Snapper
===================================================
Responsibilities:
  1. Ingest raw 2D occupancy grid maps (from /map or saved YAML/PGM).
  2. Detect dominant building orientation via wall angle histogram clustering.
  3. Snap wall line segments to orthogonal (0°, 90°, 180°, 270°) Manhattan orientations.
  4. Fill gaps, extend corners to 90° intersections, and produce CAD-like architectural boxy maps.
  5. Publish /map_regularized (nav_msgs/msg/OccupancyGrid) and export high-res SVG & PGM.
"""
import os
import sys
import math
import numpy as np
import cv2
import yaml
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid, MapMetaData
from std_msgs.msg import Header

def regularize_occupancy_grid(grid_data, width, height, resolution, origin_x, origin_y):
    """
    Applies Manhattan World Orthogonal Regularization to an OccupancyGrid array.
    Returns: regularized_grid (1D list), svg_content (str), stats (dict)
    """
    # 1. Convert 1D occupancy data (-1=unknown, 0=free, 100=occupied) to 2D image
    img = np.zeros((height, width), dtype=np.uint8)
    raw = np.array(grid_data, dtype=np.int8).reshape((height, width))
    
    # Threshold wall pixels (occupied > 65)
    wall_mask = np.uint8(raw >= 65) * 255
    if np.count_nonzero(wall_mask) < 20:
        return grid_data, "", {"walls_detected": 0, "status": "Insufficient wall pixels"}

    # 2. Morphological cleanup: close small gaps along walls
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    cleaned_walls = cv2.morphologyEx(wall_mask, cv2.MORPH_CLOSE, kernel)

    # 3. Detect line segments using Probabilistic Hough Transform
    min_line_len = max(5, int(0.25 / resolution)) # at least 25cm
    max_line_gap = max(3, int(0.15 / resolution)) # connect gaps <= 15cm
    lines = cv2.HoughLinesP(cleaned_walls, rho=1, theta=np.pi / 180, threshold=15,
                            minLineLength=min_line_len, maxLineGap=max_line_gap)

    if lines is None or len(lines) == 0:
        return grid_data, "", {"walls_detected": 0, "status": "No continuous walls found"}

    # 4. Determine dominant building orientation angle (modulo 90°)
    angles = []
    weights = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = math.hypot(x2 - x1, y2 - y1)
        angle = math.atan2(y2 - y1, x2 - x1) % (math.pi / 2.0) # Fold to [0, 90)
        angles.append(angle)
        weights.append(length)

    # Weighted median / histogram peak for dominant orientation
    hist, bin_edges = np.histogram(angles, bins=36, weights=weights, range=(0, math.pi / 2.0))
    dom_bin = np.argmax(hist)
    dominant_theta = (bin_edges[dom_bin] + bin_edges[dom_bin + 1]) / 2.0

    # 5. Snap all line segments to closest orthogonal Manhattan orientation
    snapped_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        mx = (x1 + x2) / 2.0
        my = (y1 + y2) / 2.0
        length = math.hypot(x2 - x1, y2 - y1)
        raw_angle = math.atan2(y2 - y1, x2 - x1)

        # Find closest multiple of 90° relative to dominant_theta
        rel_angle = (raw_angle - dominant_theta) % math.pi
        if rel_angle < math.pi / 4.0:
            target_angle = dominant_theta
        elif rel_angle < 3.0 * math.pi / 4.0:
            target_angle = dominant_theta + math.pi / 2.0
        else:
            target_angle = dominant_theta

        # Reconstruct snapped line centered at midpoint
        half_len = length / 2.0
        dx = half_len * math.cos(target_angle)
        dy = half_len * math.sin(target_angle)
        snapped_lines.append((int(mx - dx), int(my - dy), int(mx + dx), int(my + dy)))

    # 6. Render clean CAD-like regularized occupancy grid
    reg_img = np.full((height, width), -1, dtype=np.int8) # default unknown
    
    # Mark free space wherever raw map was free
    reg_img[raw == 0] = 0

    # Draw snapped walls with 2-pixel thickness (~10cm wall thickness)
    wall_canvas = np.zeros((height, width), dtype=np.uint8)
    for sx1, sy1, sx2, sy2 in snapped_lines:
        cv2.line(wall_canvas, (sx1, sy1), (sx2, sy2), 255, thickness=2)

    # Corner closure / morphological union
    wall_canvas = cv2.dilate(wall_canvas, kernel, iterations=1)
    reg_img[wall_canvas > 0] = 100

    # 7. Generate clean SVG architectural floor plan
    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background-color: #0f172a;">')
    for sx1, sy1, sx2, sy2 in snapped_lines:
        # SVG coordinates (flip Y for standard image view)
        svg_lines.append(f'  <line x1="{sx1}" y1="{height - sy1}" x2="{sx2}" y2="{height - sy2}" stroke="#38bdf8" stroke-width="3" stroke-linecap="square" />')
    svg_lines.append('</svg>')
    svg_content = '\n'.join(svg_lines)

    stats = {
        "walls_detected": len(lines),
        "dominant_angle_deg": round(math.degrees(dominant_theta), 1),
        "snapped_walls": len(snapped_lines),
        "status": "Success"
    }

    return reg_img.flatten().tolist(), svg_content, stats

class MapRegularizerNode(Node):
    def __init__(self):
        super().__init__('map_regularizer')
        self.sub_map = self.create_subscription(OccupancyGrid, '/map', self.map_cb, 10)
        self.pub_reg_map = self.create_publisher(OccupancyGrid, '/map_regularized', 10)
        self.get_logger().info("Manhattan Map Regularizer Node online on Domain 42.")

    def map_cb(self, msg: OccupancyGrid):
        w = msg.info.width
        h = msg.info.height
        res = msg.info.resolution
        ox = msg.info.origin.position.x
        oy = msg.info.origin.position.y

        reg_data, _, stats = regularize_occupancy_grid(msg.data, w, h, res, ox, oy)
        
        reg_msg = OccupancyGrid()
        reg_msg.header = msg.header
        reg_msg.header.frame_id = 'map'
        reg_msg.info = msg.info
        reg_msg.data = reg_data
        self.pub_reg_map.publish(reg_msg)

def regularize_saved_map_file(yaml_path):
    """Utility to regularize an existing saved map .yaml/.pgm on disk."""
    if not os.path.exists(yaml_path):
        return False, f"File {yaml_path} not found"
    
    with open(yaml_path, 'r') as f:
        meta = yaml.safe_load(f)

    img_filename = meta['image']
    img_dir = os.path.dirname(yaml_path)
    img_path = os.path.join(img_dir, img_filename)
    
    pgm = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if pgm is None:
        return False, f"Could not read image {img_path}"

    h, w = pgm.shape
    res = float(meta.get('resolution', 0.05))
    ox, oy = meta.get('origin', [0, 0, 0])[:2]

    # Convert PGM to OccupancyGrid (-1, 0, 100)
    grid = np.full((h, w), -1, dtype=np.int8)
    grid[pgm > 240] = 0   # Free
    grid[pgm < 50] = 100  # Wall

    reg_data, svg_content, stats = regularize_occupancy_grid(grid.flatten().tolist(), w, h, res, ox, oy)

    # Save regularized PGM & SVG
    reg_arr = np.array(reg_data, dtype=np.int8).reshape((h, w))
    out_pgm = np.full((h, w), 205, dtype=np.uint8) # 205 = unknown grey
    out_pgm[reg_arr == 0] = 254                   # 254 = free white
    out_pgm[reg_arr == 100] = 0                   # 0 = wall black

    base_name = os.path.splitext(yaml_path)[0]
    reg_yaml_path = f"{base_name}_regularized.yaml"
    reg_pgm_path = f"{base_name}_regularized.pgm"
    reg_svg_path = f"{base_name}_regularized.svg"

    cv2.imwrite(reg_pgm_path, out_pgm)
    with open(reg_svg_path, 'w') as f:
        f.write(svg_content)

    meta['image'] = os.path.basename(reg_pgm_path)
    with open(reg_yaml_path, 'w') as f:
        yaml.dump(meta, f)

    return True, {
        "regularized_yaml": reg_yaml_path,
        "regularized_svg": reg_svg_path,
        "stats": stats
    }

def main(args=None):
    rclpy.init(args=args)
    node = MapRegularizerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
