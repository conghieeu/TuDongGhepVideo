import os
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
)

class CatGhepCoBan:
    def __init__(
        self,
        output_folder=None,
        target_resolution=(720, 1280),
        target_fps=30,
        video_codec="libx264",
    ):
        self.temp_folder = output_folder or "temp"
        os.makedirs(self.temp_folder, exist_ok=True) 
        self.target_resolution = target_resolution
        self.target_fps = target_fps
        self.video_codec = video_codec
    
    def inspect_video_clips(file_paths):
        pass

if __name__ == "__main__":
    cg = CatGhepCoBan()
    # cg.mix_two_audios("audio1.mp3", "audio2.mp3")
    # cg.mix_audio_with_video("video2.mp4", "audio2.mp3")
    # cg.split_video_by_time("video2.mp4", 2)
    cg.inspect_video_clips("media/video1.mp4", "media/video2.mp4")