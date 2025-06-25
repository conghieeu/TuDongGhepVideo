import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from moviepy import VideoFileClip, concatenate_videoclips
from src.CatGhepCoBan import CatGhepCoBan
import logging 

class VideoMerger:
    """
    Lớp chứa các logic nghiệp vụ phức tạp để ghép video theo các kịch bản khác nhau.
    """
    def __init__(self, output_folder, **kwargs):
        """
        Hàm khởi tạo nhận cấu hình một cách linh hoạt.
        """
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
        self.created_files = []
        self.CG = CatGhepCoBan(**kwargs)

    def get_video_details(self, video_path):
        """Lấy thông tin chi tiết của video."""
        if not os.path.exists(video_path):
            logging.error(f"File không tồn tại tại '{video_path}'")
            return None, None, None
        try:
            with VideoFileClip(video_path) as clip:
                return clip.size, clip.fps, clip.duration
        except Exception as e:
            logging.error(f"Lỗi khi đọc file video '{video_path}': {e}")
            return None, None, None

    def merge_with_audio_swap_at_start(self, audio_source_path, video_target_path, output_filename=None):
        """
        Kịch bản tráo audio thông minh.
        """
        try:
            _, _, swap_duration = self.get_video_details(audio_source_path)
            target_resolution, target_fps, target_duration = self.get_video_details(video_target_path)

            if swap_duration is None or target_duration is None:
                logging.error("Không thể lấy thông tin từ file, bỏ qua.")
                return None
            
            # Đảm bảo output_filename có giá trị mặc định nếu là None
            final_name = output_filename or f"{os.path.splitext(os.path.basename(video_target_path))[0]}.mp4"
            final_output_path = os.path.join(self.output_folder, final_name)

            if swap_duration > target_duration:
                logging.info(f"Audio nguồn dài hơn, chuyển sang thay thế toàn bộ audio.")
                # Logic thay thế toàn bộ audio
                return self.CG.mix_audio_with_video(video_target_path, audio_source_path, final_output_path)
            else:
                logging.info(f"Thực hiện tráo audio phần đầu (thời lượng: {swap_duration:.2f}s).")
                audio_path = self.CG.extract_audio(audio_source_path)
                part1_path, part2_path = self.CG.split_video_by_time(video_target_path, swap_duration)
                part1_with_new_audio_path = self.CG.mix_audio_with_video(part1_path, audio_path)

                with VideoFileClip(part1_with_new_audio_path) as clip1, \
                     VideoFileClip(part2_path) as clip2:
                    
                    final_clip = concatenate_videoclips([clip1, clip2])
                    
                    final_clip.write_videofile(final_output_path, codec=self.CG.video_codec, fps=target_fps or self.CG.target_fps)
                    
                    logging.info(f"Tạo video thành công: {final_output_path}")
                    self.created_files.append(final_output_path)
                    return final_output_path
        except Exception as e:
            logging.error(f"Đã xảy ra lỗi nghiêm trọng khi xử lý: {e}", exc_info=True)
            return None
        finally:
            self.CG.clear_temp_folder()

    def stats(self):
        """In ra thống kê các file đã được tạo."""
        logging.info("\n--- THỐNG KÊ ---")
        logging.info(f"Tổng số video đã tạo: {len(self.created_files)}")
        for f in self.created_files:
            logging.info(f"- {f}")