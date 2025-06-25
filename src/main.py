import os
import logging
from VideoMerger import VideoMerger 

def setup_logging():
    """Cấu hình hệ thống logging cơ bản."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    """Hàm chính để chạy toàn bộ logic."""
    setup_logging()

    # === CẤU HÌNH TẬP TRUNG ===
    CONFIG = {
        "target_resolution": (720, 1280),
        "target_fps": 30,
        "video_codec": "libx264",
        "temp_folder": "temp_files"
    }

    # Các thư mục chứa video
    video_folder = "videos1"
    audio_folder = "videos2"
    output_folder = "output_videos"
    
    os.makedirs(video_folder, exist_ok=True)
    os.makedirs(audio_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    merger = VideoMerger(output_folder, **CONFIG)

    audio_files = sorted([
        f for f in os.listdir(audio_folder)
        if f.lower().endswith(('.mp4', '.avi', '.mov', '.mp3', '.wav', '.aac', '.m4a'))
    ])
    video_files = sorted([f for f in os.listdir(video_folder) if f.lower().endswith(('.mp4', '.avi', '.mov'))])

    logging.info(f"Tìm thấy {len(video_files)} video chính và {len(audio_files)} video audio.")
    
    for video_file in video_files:  
        for audio_file in audio_files:
            video_path = os.path.join(video_folder, video_file)
            audio_path = os.path.join(audio_folder, audio_file)
            
            merger.merge_with_audio_swap_at_start(audio_path, video_path)

    merger.stats()

if __name__ == "__main__":
    main()