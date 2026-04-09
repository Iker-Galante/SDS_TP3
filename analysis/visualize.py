"""
OVITO visualization script for the Event-Driven Molecular Dynamics simulation.
Creates animations showing particles with color-coded states:
  - Green: Fresh particles
  - Violet/Purple: Used particles
  - Red: Fixed central obstacle
  - Gray: Boundary particles (enclosure wall)
"""

import ovito
from ovito.io import import_file
from ovito.vis import *
from ovito.modifiers import *
from ovito.data import *
import numpy as np
import sys
import os
import glob


def setup_visualization(pipeline, enclosure_diameter=80.0):
    """Configure visualization settings for the simulation."""
    
    # Color coding modifier based on particle state
    def color_by_state(frame, data):
        """Assign colors based on particle state."""
        state = data.particles['state']
        colors = np.zeros((len(state), 3))
        
        for i in range(len(state)):
            if state[i] == 0:      # FRESH - green
                colors[i] = [0.2, 0.8, 0.2]
            elif state[i] == 1:    # USED - violet/purple
                colors[i] = [0.6, 0.1, 0.8]
            elif state[i] == 2:    # OBSTACLE - red
                colors[i] = [0.9, 0.1, 0.1]
            elif state[i] == 3:    # BOUNDARY - gray
                colors[i] = [0.5, 0.5, 0.5]
        
        data.particles_.create_property('Color', data=colors)
    
    pipeline.modifiers.append(color_by_state)
    
    return pipeline


def render_animation(xyz_file, output_video, enclosure_diameter=80.0, fps=30, resolution=(1920, 1080)):
    """Render an animation from the XYZ file."""
    
    # Import data
    pipeline = import_file(xyz_file, columns=[
        "Particle Identifier", "Position.X", "Position.Y", "Position.Z",
        "Velocity.X", "Velocity.Y", "Velocity.Z", "Radius", "state"
    ])
    
    # Setup visualization
    pipeline = setup_visualization(pipeline, enclosure_diameter)
    pipeline.add_to_scene()
    
    # Configure viewport
    vp = Viewport(type=Viewport.Type.Top)
    R = enclosure_diameter / 2.0
    vp.camera_pos = (0, 0, 100)
    vp.camera_dir = (0, 0, -1)
    vp.fov = enclosure_diameter * 1.1
    
    # Configure renderer
    renderer = TachyonRenderer()
    renderer.ambient_occlusion = True
    renderer.antialiasing_samples = 12
    
    # Render
    num_frames = pipeline.source.num_frames
    print(f"Rendering {num_frames} frames at {resolution[0]}x{resolution[1]}...")
    
    vp.render_anim(
        filename=output_video,
        size=resolution,
        fps=fps,
        renderer=renderer,
        range=(0, num_frames - 1)
    )
    
    pipeline.remove_from_scene()
    print(f"Animation saved to: {output_video}")


def render_snapshot(xyz_file, output_image, frame=0, enclosure_diameter=80.0, resolution=(1920, 1080)):
    """Render a single frame from the XYZ file."""
    
    pipeline = import_file(xyz_file, columns=[
        "Particle Identifier", "Position.X", "Position.Y", "Position.Z",
        "Velocity.X", "Velocity.Y", "Velocity.Z", "Radius", "state"
    ])
    
    pipeline = setup_visualization(pipeline, enclosure_diameter)
    pipeline.add_to_scene()
    
    vp = Viewport(type=Viewport.Type.Top)
    vp.camera_pos = (0, 0, 100)
    vp.camera_dir = (0, 0, -1)
    vp.fov = enclosure_diameter * 1.1
    
    renderer = TachyonRenderer()
    renderer.ambient_occlusion = True
    renderer.antialiasing_samples = 12
    
    vp.render_image(
        filename=output_image,
        size=resolution,
        frame=frame,
        renderer=renderer
    )
    
    pipeline.remove_from_scene()
    print(f"Snapshot saved to: {output_image}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OVITO visualization for EDMD simulation")
    parser.add_argument("--input", "-i", required=True, help="Input XYZ file")
    parser.add_argument("--output", "-o", required=True, help="Output file (video or image)")
    parser.add_argument("--mode", "-m", choices=["animation", "snapshot"], default="animation",
                        help="Rendering mode")
    parser.add_argument("--frame", type=int, default=0, help="Frame number for snapshot mode")
    parser.add_argument("--fps", type=int, default=30, help="FPS for animation")
    parser.add_argument("--width", type=int, default=1920, help="Output width")
    parser.add_argument("--height", type=int, default=1080, help="Output height")
    parser.add_argument("--L", type=float, default=80.0, help="Enclosure diameter")
    
    args = parser.parse_args()
    resolution = (args.width, args.height)
    
    if args.mode == "animation":
        render_animation(args.input, args.output, args.L, args.fps, resolution)
    else:
        render_snapshot(args.input, args.output, args.frame, args.L, resolution)
