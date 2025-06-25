import os
import logging
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips

# Thiết lập logging cơ bản để thấy output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Class giả lập để code có thể chạy
class VideoProcessor:
    def __init__(self, output_folder="output"):
        self.output_folder = output_folder
        self.created_files = []
        os.makedirs(self.output_folder, exist_ok=True)
        class Config:
            video_codec = 'libx264'
            target_fps = 30
        self.CG = Config()

    def get_video_details(self, video_path):
        with VideoFileClip(video_path) as clip:
            return clip.size, clip.fps, clip.duration

    def merge_with_audio_swap_at_start(self, video_path, new_audio_path, output_filename=None):
        videoClip = None
        audioClip = None
        try:
            is_audio_file = new_audio_path.lower().endswith(('.mp3', '.wav', '.aac'))
            if is_audio_file:
                audioClip = AudioFileClip(new_audio_path)
            else:
                temp_video_clip = VideoFileClip(new_audio_path)
                audioClip = temp_video_clip.audio
                temp_video_clip.close()

            videoClip = VideoFileClip(video_path)

            video_resolution, video_fps, video_duration = self.get_video_details(video_path)
            
            if audioClip is None or getattr(audioClip, 'duration', None) is None:
                logging.error(f"Không thể đọc được audio từ file: {new_audio_path}")
                return None
            audio_duration = audioClip.duration

            final_name = output_filename or f"swapped_{os.path.basename(video_path)}"
            final_output_path = os.path.join(self.output_folder, final_name)

            final_clip = None

            if audio_duration >= video_duration:
                logging.info(f"Audio dài hơn video. Cắt audio cho khớp với thời lượng video ({video_duration}s).")
                
                # --- GIẢI PHÁP DUY NHẤT cho moviepy==2.2.1 mà không thêm import ---
                # Thay đổi trực tiếp thuộc tính .end và .duration của đối tượng audioClip.
                # Đây là một "cách lách" (workaround) cho phiên bản cũ này.
                audioClip.end = video_duration
                audioClip.duration = video_duration
                
                # Sử dụng trực tiếp đối tượng audioClip đã bị thay đổi thuộc tính
                final_clip = videoClip.with_audio(audioClip)
                
            else:
                logging.info("Audio ngắn hơn video. Chỉ thay thế audio ở đoạn đầu.")
                part1 = videoClip.subclipped(0, audio_duration)
                part2 = videoClip.subclipped(audio_duration)
                part1_with_new_audio = part1.with_audio(audioClip)
                final_clip = concatenate_videoclips([part1_with_new_audio, part2], method="compose")

            final_clip.write_videofile(
                final_output_path,
                codec=self.CG.video_codec,
                fps=video_fps or self.CG.target_fps,
                audio_codec='aac',
                size=video_resolution
            )

            logging.info(f"Tạo video thành công: {final_output_path}")
            self.created_files.append(final_output_path)
            return final_output_path

        except Exception as e:
            logging.error(f"Đã xảy ra lỗi nghiêm trọng khi xử lý '{os.path.basename(video_path)}': {e}", exc_info=True)
            return None
        finally:
            if videoClip:
                videoClip.close()
            if audioClip:
                audioClip.close()
                
vp = VideoProcessor()
vp.merge_with_audio_swap_at_start("video1.mp4", "audio1.mp3", "output_long_audio.mp4")