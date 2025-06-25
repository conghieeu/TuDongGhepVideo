import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from moviepy import concatenate_videoclips, VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip, ImageClip
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
        
    # Đặt hàm này bên trong lớp VideoMerger, gần hàm get_video_details
    def get_audio_duration(self, audio_path):
        """
        Lấy thời lượng của một tệp âm thanh.
        """
        if not os.path.exists(audio_path):
            logging.error(f"File audio không tồn tại tại '{audio_path}'")
            return None
        try:
            # Sử dụng AudioFileClip để mở tệp âm thanh
            with AudioFileClip(audio_path) as clip:
                return clip.duration
        except Exception as e:
            logging.error(f"Không thể đọc file audio '{audio_path}': {e}")
            return None
    
    # Thay thế hàm cũ bằng phiên bản mới này trong lớp VideoMerger
    def merge_with_audio_swap_at_start(self, audio_source_path, video_target_path, output_filename=None):
        """
        Kịch bản tráo audio thông minh, xử lý được cả nguồn audio là video hoặc file audio.
        """
        try:
            # ---- BƯỚC 1: XÁC ĐỊNH LOẠI FILE VÀ LẤY THỜI LƯỢNG ----
            is_audio_file = audio_source_path.lower().endswith(('.mp3', '.wav', '.aac', '.m4a'))
            
            if is_audio_file:
                logging.info(f"Nguồn '{os.path.basename(audio_source_path)}' là file audio.")
                swap_duration = self.get_audio_duration(audio_source_path)
                # Nếu nguồn là audio, không cần trích xuất, dùng trực tiếp
                audio_path_to_mix = audio_source_path
            else:
                logging.info(f"Nguồn '{os.path.basename(audio_source_path)}' là file video, sẽ trích xuất audio.")
                _, _, swap_duration = self.get_video_details(audio_source_path)
                # Trích xuất audio từ video nguồn
                audio_path_to_mix = self.CG.extract_audio(audio_source_path)

            # Lấy thông tin video đích
            target_resolution, target_fps, target_duration = self.get_video_details(video_target_path)

            # Kiểm tra nếu không lấy được thông tin cần thiết
            if swap_duration is None or target_duration is None:
                logging.error("Không thể lấy thông tin thời lượng từ file nguồn hoặc đích, bỏ qua.")
                return None
            
            # ---- BƯỚC 2: CHUẨN BỊ TÊN FILE OUTPUT ----
            final_name = output_filename or f"swapped_{os.path.basename(video_target_path)}"
            final_output_path = os.path.join(self.output_folder, final_name)

            # ---- BƯỚC 3: SO SÁNH THỜI LƯỢNG VÀ XỬ LÝ ----
            # Kịch bản 1: Audio nguồn dài hơn video đích -> Thay thế toàn bộ audio
            if swap_duration >= target_duration:
                logging.info(f"Audio nguồn dài hơn hoặc bằng video đích, tiến hành thay thế toàn bộ audio.")
                return self.CG.mix_audio_with_video(video_target_path, audio_path_to_mix, final_output_path)
            
            # Kịch bản 2: Audio nguồn ngắn hơn -> Chỉ tráo đoạn đầu
            else:
                logging.info(f"Thực hiện tráo audio cho {swap_duration:.2f} giây đầu.")
                
                # Cắt video đích thành 2 phần
                part1_path, part2_path = self.CG.split_video_by_time(video_target_path, swap_duration)
                
                # Trộn audio vào phần đầu
                part1_with_new_audio_path = self.CG.replace_audio(part1_path, audio_path_to_mix)

                # Ghép 2 phần video lại với nhau
                logging.info("Ghép các phần video đã xử lý lại...")
                # Sử dụng context manager để đảm bảo tài nguyên được giải phóng
                with VideoFileClip(part1_with_new_audio_path) as clip1, \
                    VideoFileClip(part2_path) as clip2:
                    
                    # Sử dụng method="compose" để tránh lỗi nếu có sự khác biệt nhỏ về kích thước
                    final_clip = concatenate_videoclips([clip1, clip2], method="compose")
                    
                    final_clip.write_videofile(
                        final_output_path, 
                        codec=self.CG.video_codec, 
                        fps=target_fps or self.CG.target_fps
                    )
                    
                    logging.info(f"Tạo video thành công: {final_output_path}")
                    self.created_files.append(final_output_path)
                    return final_output_path
                    
        except Exception as e:
            logging.error(f"Đã xảy ra lỗi nghiêm trọng khi xử lý '{os.path.basename(video_target_path)}': {e}", exc_info=True)
            return None
        finally:
            # Dọn dẹp các file tạm đã tạo ra trong quá trình xử lý
            logging.info("Dọn dẹp file tạm...")
            self.CG.clear_temp_folder()

    def stats(self):
        """In ra thống kê các file đã được tạo."""
        logging.info("\n--- THỐNG KÊ ---")
        logging.info(f"Tổng số video đã tạo: {len(self.created_files)}")
        for f in self.created_files:
            logging.info(f"- {f}")