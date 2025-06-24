import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
from CatGhepCoBan import CatGhepCoBan

# === CẤU HÌNH TẬP TRUNG ===
# Thay đổi các giá trị này sẽ ảnh hưởng đến tất cả các hàm bên dưới
TARGET_RESOLUTION = (720, 1280)
TARGET_FPS = 30
VIDEO_CODEC = "libx264"

class VideoMerger:
    """
    Lớp chứa các logic nghiệp vụ phức tạp để ghép video theo các kịch bản khác nhau.
    """
    def __init__(self, output_folder):
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
        self.created_files = []
        self.CG = CatGhepCoBan()
        # Cập nhật cấu hình cho đối tượng CatGhepCoBan nếu cần
        self.CG.TARGET_RESOLUTION = TARGET_RESOLUTION
        self.CG.TARGET_FPS = TARGET_FPS
        self.CG.VIDEO_CODEC = VIDEO_CODEC


    def get_video_details(self, video_path):
        """
        Lấy độ phân giải (resolution), FPS và thời lượng (duration) của video.

        Args:
            video_path (str): Đường dẫn đến file video.

        Returns:
            tuple: Chứa (resolution, fps, duration). 
                   Ví dụ: ([720, 1280], 30, 15.49).
                   Trả về (None, None, None) nếu có lỗi.
        """
        if not os.path.exists(video_path):
            print(f"Lỗi: File không tồn tại tại '{video_path}'")
            return None, None, None
        
        clip = None
        try:
            clip = VideoFileClip(video_path)
            resolution = clip.size
            fps = clip.fps
            duration = clip.duration # <-- Dòng mới được thêm vào
            clip.close()
            return resolution, fps, duration # <-- Trả về 3 giá trị
        except Exception as e:
            print(f"Lỗi khi đọc file video '{video_path}': {e}")
            if clip:
                clip.close()
            return None, None, None # <-- Trả về 3 giá trị


    def merge_with_trimmed_second(self, link1, link2, output=None):
        """
        Kịch bản 1: Ghép video1 vào đầu video2, lấy audio của đầu video2 gán cho video1.
        """
        c1_clip_check = None
        try:
            c1_clip_check = VideoFileClip(link1)
            if c1_clip_check.duration <= 0.5:
                raise ValueError(f"Video {link1} quá ngắn để xử lý.")
            c1_duration = c1_clip_check.duration
            c1_clip_check.close()
            
            trimmed1, trimmed2 = self.CG.split_video_by_time(link2, c1_duration)
            _, audio_part1 = self.CG.extract_audio_and_video(trimmed1)
            c1_audio_set = self.CG.mix_audio_with_video(link1, audio_part1)

            c1_clip = VideoFileClip(c1_audio_set)
            c2_clip = VideoFileClip(trimmed2)

            if c2_clip.audio and c2_clip.audio.duration > c2_clip.duration:
                c2_clip = c2_clip.set_audio(c2_clip.audio.subclip(0, c2_clip.duration))

            final_clip = concatenate_videoclips([c1_clip, c2_clip])
            
            name1 = os.path.splitext(os.path.basename(link1))[0]
            name2 = os.path.splitext(os.path.basename(link2))[0]
            final_name = f"{name1}_{name2}.mp4"
            final_path = output or os.path.join(self.output_folder, final_name)

            final_clip.write_videofile(final_path, codec=VIDEO_CODEC, fps=TARGET_FPS)
            
            self.created_files.append(final_path)
            c1_clip.close()
            c2_clip.close()
            final_clip.close()
            return final_path
            
        except Exception as e:
            print(f"Lỗi khi xử lý {os.path.basename(link1)} và {os.path.basename(link2)}: {e}")
            if c1_clip_check: c1_clip_check.close()
            return None
        finally:
            self.CG.clear_temp_folder() 


    def merge_with_audio_swap_at_start(self, audio_source_path, video_target_path, output=None):
        """
        Kịch bản 2 (thông minh hơn): 
        - Sử dụng độ phân giải và FPS của video đích làm chuẩn.
        - Nếu audio nguồn dài hơn video đích: chuyển sang thay thế toàn bộ audio.
        - Nếu audio nguồn ngắn hơn video đích: tráo audio ở phần đầu.
        """
        try:
            # Lấy thông tin chi tiết của cả hai file
            _, _, swap_duration = self.get_video_details(audio_source_path)
            
            # --- THAY ĐỔI QUAN TRỌNG: Lấy cả resolution và fps của video ĐÍCH ---
            target_resolution, target_fps, target_duration = self.get_video_details(video_target_path)

            # Kiểm tra nếu việc lấy thông tin thất bại
            if swap_duration is None or target_duration is None or target_resolution is None or target_fps is None:
                print("Lỗi: Không thể lấy thông tin đầy đủ từ một trong các file video. Bỏ qua.")
                return None

            # Logic rẽ nhánh dựa trên thời lượng
            if swap_duration > target_duration:
                # Trường hợp 1: Audio nguồn dài hơn video đích
                print(f"Thông báo: Audio nguồn ({swap_duration:.2f}s) dài hơn video đích ({target_duration:.2f}s).")
                print("--> Chuyển sang chế độ thay thế toàn bộ audio.")
                
                video_name = os.path.splitext(os.path.basename(video_target_path))[0]
                audio_name = os.path.splitext(os.path.basename(audio_source_path))[0]
                output_name = f"{video_name}.mp4"

                return self.set_new_audio_for_video(video_target_path, audio_source_path, output_file_name=output_name)
            
            else:
                # Trường hợp 2: Audio nguồn ngắn hơn video đích
                print(f"--> Thực hiện tráo audio phần đầu (thời lượng: {swap_duration:.2f}s).")

                audio_path = self.CG.extract_audio(audio_source_path)
                part1_path, part2_path = self.CG.split_video_by_time(video_target_path, swap_duration)
                part1_with_new_audio_path = self.CG.mix_audio_with_video(part1_path, audio_path)

                clip1 = VideoFileClip(part1_with_new_audio_path)
                clip2 = VideoFileClip(part2_path)
                
                # --- THAY ĐỔI QUAN TRỌNG: Sử dụng resolution và fps động của video ĐÍCH ---
                # Thay vì dùng hằng số TARGET_RESOLUTION, TARGET_FPS
                print(f"    Áp dụng độ phân giải {target_resolution} và FPS {target_fps:.2f} của video gốc.")
                clip1 = clip1.resize(target_resolution).set_fps(target_fps)
                clip2 = clip2.resize(target_resolution).set_fps(target_fps)
                
                final_clip = concatenate_videoclips([clip1, clip2])

                # Tạo tên file output
                name1 = os.path.splitext(os.path.basename(audio_source_path))[0]
                name2 = os.path.splitext(os.path.basename(video_target_path))[0]
                final_name = f"{name2}.mp4"
                final_path = output or os.path.join(self.output_folder, final_name)

                # Sử dụng fps động khi ghi file
                final_clip.write_videofile(final_path, codec=VIDEO_CODEC, fps=target_fps)
                
                clip1.close()
                clip2.close()
                final_clip.close()
                print(f"    Tạo video thành công: {final_path}")
                self.created_files.append(final_path)
                return final_path

        except Exception as e:
            print(f"    Đã xảy ra lỗi nghiêm trọng khi xử lý: {e}")
            return None
        finally:
            self.CG.clear_temp_folder()


    def set_new_audio_for_video(self,audio_path, video_path, output_file_name=None):
        """
        Gán một file audio mới cho một file video và lưu kết quả vào thư mục output.
        Hàm này sẽ tự động xử lý chênh lệch thời lượng giữa video và audio.
        
        Args:
            video_path (str): Đường dẫn đến file video.
            audio_path (str): Đường dẫn đến file audio (.mp3, .wav, etc.).
            output_file_name (str, optional): Tên file output mong muốn (ví dụ: 'ket_qua.mp4'). 
                                              Nếu không có, tên sẽ được tạo tự động.

        Returns:
            str: Đường dẫn đến file video đã tạo, hoặc None nếu có lỗi.
        """
        print(f"--> Bắt đầu gán audio '{os.path.basename(audio_path)}' cho video '{os.path.basename(video_path)}'")
        try:
            if not os.path.exists(video_path):
                print(f"    Lỗi: File video không tồn tại tại '{video_path}'")
                return None
            if not os.path.exists(audio_path):
                print(f"    Lỗi: File audio không tồn tại tại '{audio_path}'")
                return None

            if output_file_name:
                final_path = os.path.join(self.output_folder, output_file_name)
            else:
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                audio_name = os.path.splitext(os.path.basename(audio_path))[0]
                auto_name = f"{video_name}_voi_audio_{audio_name}.mp4"
                final_path = os.path.join(self.output_folder, auto_name)

            created_path = self.CG.mix_audio_with_video(video_path, audio_path, output_path=final_path)

            if created_path and os.path.exists(created_path):
                print(f"    Tạo video thành công: {created_path}")
                self.created_files.append(created_path)
                return created_path
            else:
                print("    Lỗi: Không tạo được file output.")
                return None

        except Exception as e:
            print(f"    Đã xảy ra lỗi nghiêm trọng khi gán audio: {e}")
            return None


    def stats(self):
        """In ra thống kê các file đã được tạo."""
        print("\n--- THỐNG KÊ ---")
        print(f"Tổng số video đã tạo: {len(self.created_files)}")
        for f in self.created_files:
            print(f"- {f}")



def main():
    """Hàm chính để chạy chương trình."""
    # Các thư mục chứa video
    # videos1 là video chính, videos2 là video lấy audio
    video_folder = "videos1"
    audio_folder = "videos2"
    output_folder = "output_videos"
    
    # Tạo các thư mục nếu chưa tồn tại
    os.makedirs(video_folder, exist_ok=True)
    os.makedirs(audio_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    # Khởi tạo đối tượng xử lý
    merger = VideoMerger(output_folder)

    # Lấy danh sách các file video
    audio_files = sorted([f for f in os.listdir(audio_folder) if f.lower().endswith(('.mp4', '.avi', '.mov'))])
    video_files = sorted([f for f in os.listdir(video_folder) if f.lower().endswith(('.mp4', '.avi', '.mov'))])

    print(f"Tìm thấy {len(video_files)} video chính và {len(audio_files)} video audio.")
    
    # Chạy vòng lặp để ghép video
    for video_file in video_files:  
        for audio_file in audio_files:
            video_path = os.path.join(video_folder, video_file)
            audio_path = os.path.join(audio_folder, audio_file)
            
            # Gọi hàm xử lý chính
            merger.merge_with_audio_swap_at_start(audio_path, video_path)

    # In thống kê kết quả
    merger.stats()

if __name__ == "__main__":
    main()