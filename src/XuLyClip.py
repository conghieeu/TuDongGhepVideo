import os
from moviepy import concatenate_videoclips, VideoFileClip, AudioFileClip

class ClipProccess:
    def __init__(
        self,
        temp_folder=None,
        target_resolution=(720, 1280),
        target_fps=30,
        video_codec="libx264",
    ):
        self.temp_folder = temp_folder or "temp"
        os.makedirs(self.temp_folder, exist_ok=True)
        self.target_resolution = target_resolution
        self.target_fps = target_fps
        self.video_codec = video_codec