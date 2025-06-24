import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

class CatGhepCoBan:
    def __init__(self, temp_folder=None):
        self.temp_folder = temp_folder or "temp"
        os.makedirs(self.temp_folder, exist_ok=True)

    def clear_temp_folder(self):
        print("Đang dọn dẹp các file tạm...")
        for filename in os.listdir(self.temp_folder):
            file_path = os.path.join(self.temp_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Lỗi khi xóa file tạm {file_path}: {e}")

    def merge_videos(self, link1, link2):
        c1 = VideoFileClip(link1)
        c2 = VideoFileClip(link2)
        target_resolution = (720, 1280)
        target_fps = 30
        c1 = c1.resize(target_resolution).set_fps(target_fps)
        c2 = c2.resize(target_resolution).set_fps(target_fps)
        out = concatenate_videoclips([c1, c2])
        name = f"{os.path.splitext(os.path.basename(link1))[0]}_{os.path.splitext(os.path.basename(link2))[0]}.mp4"
        path = os.path.join(self.temp_folder, name)
        out.write_videofile(path, codec="libx264", fps=target_fps)
        c1.close()
        c2.close()
        out.close()
        return path

    def cut_head(self, input_path, duration):
        clip = VideoFileClip(input_path).subclip(duration)
        name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(self.temp_folder, f"{name}_cuthead.mp4")
        clip.write_videofile(output_path, codec='libx264')
        clip.close()
        return output_path

    def split_video_by_time(self, input_path, split_time):
        name = os.path.splitext(os.path.basename(input_path))[0]
        output1 = os.path.join(self.temp_folder, f"{name}_part1.mp4")
        output2 = os.path.join(self.temp_folder, f"{name}_part2.mp4")
        clip = VideoFileClip(input_path)
        # Đảm bảo thời gian cắt không vượt quá thời lượng video
        split_time = min(split_time, clip.duration)
        clip1 = clip.subclip(0, split_time)
        clip2 = clip.subclip(split_time)
        clip1.write_videofile(output1, codec='libx264')
        clip2.write_videofile(output2, codec='libx264')
        clip1.close()
        clip2.close()
        clip.close()
        return output1, output2

    def extract_audio(self, video_path):
        """Chỉ tách audio từ video và trả về đường dẫn file audio."""
        clip = VideoFileClip(video_path)
        name = os.path.splitext(os.path.basename(video_path))[0]
        audio_output = os.path.join(self.temp_folder, f"{name}_audio_only.mp3")

        if clip.audio is not None:
            clip.audio.write_audiofile(audio_output)
            clip.close()
            return audio_output
        else:
            clip.close()
            # Trả về None nếu video không có audio
            return None
            
    def extract_audio_and_video(self, video_path):
        clip = VideoFileClip(video_path)
        name = os.path.splitext(os.path.basename(video_path))[0]
        audio_output = os.path.join(self.temp_folder, f"{name}_extract_audio.mp3")
        video_output = os.path.join(self.temp_folder, f"{name}_extract_video.mp4")

        if clip.audio is not None:
            clip.audio.write_audiofile(audio_output)
        clip.without_audio().write_videofile(video_output, codec='libx264')
        clip.close()
        return video_output, audio_output

    def set_audio_video(self, video_link, audio_link, output_path=None):
        video = VideoFileClip(video_link)
        audio = AudioFileClip(audio_link)
        # Đảm bảo audio có cùng độ dài với video
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)
            
        name = os.path.splitext(os.path.basename(video_link))[0]
        output_path = output_path or os.path.join(self.temp_folder, f"{name}_set_audio_video.mp4")
        clip = video.set_audio(audio)
        clip.write_videofile(output_path, codec='libx264')
        video.close()
        audio.close()
        clip.close()
        return output_path


class VideoMerger:
    def __init__(self, output_folder):
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
        self.created_files = []
        self.CG = CatGhepCoBan()

    def merge_with_trimmed_second(self, link1, link2, output=None):
        # ... (Hàm này giữ nguyên như cũ) ...
        c1_check = VideoFileClip(link1)
        if c1_check.duration <= 0.5:
             c1_check.close()
             raise ValueError(f"Video {link1} quá ngắn")
        c1_check.close()
        
        # Cắt video thứ 2 thành 2 phần
        try:
            c1_duration = VideoFileClip(link1).duration
            trimmed1, trimmed2 = self.CG.split_video_by_time(link2, c1_duration)
        except Exception as e:
            print(f"Lỗi khi cắt video {link2}: {e}")
            return None
        if not (os.path.exists(trimmed1) and os.path.exists(trimmed2)):
            print("Trimmed video không tồn tại")
            return None
        # Tách audio từ phần đầu của video 2
        _, audio_part1 = self.CG.extract_audio_and_video(trimmed1)
        if not os.path.exists(audio_part1):
            print("Không tách được audio")
            return None
        # Gán phần audio đó cho video 1
        c1_audio_set = self.CG.set_audio_video(link1, audio_part1)
        if not os.path.exists(c1_audio_set):
            print("Không tạo được video c1_audio_set")
            return None
        name1 = os.path.splitext(os.path.basename(link1))[0]
        name2 = os.path.splitext(os.path.basename(link2))[0]
        final_name = f"{name1}_{name2}.mp4"
        final_path = output or os.path.join(self.output_folder, final_name)
        try:
            c1_clip = VideoFileClip(c1_audio_set)
            c2_clip = VideoFileClip(trimmed2)
            target_resolution = (720, 1280)
            target_fps = 30
            c1_clip = c1_clip.resize(target_resolution).set_fps(target_fps)
            c2_clip = c2_clip.resize(target_resolution).set_fps(target_fps)
            final_clip = concatenate_videoclips([c1_clip, c2_clip])
            final_clip.write_videofile(final_path, codec="libx264", fps=target_fps)
            c1_clip.close()
            c2_clip.close()
            final_clip.close()
            self.CG.clear_temp_folder()
            return final_path
        except Exception as e:
            print(f"Lỗi khi gộp video: {e}")
            self.CG.clear_temp_folder()
            return None


    def merge_with_audio_swap_at_start(self, audio_source_path, video_target_path, output=None):
        """
        Thay thế âm thanh ở phần đầu của video_target bằng âm thanh từ audio_source.
        - audio_source_path: Video nguồn để lấy âm thanh.
        - video_target_path: Video đích sẽ bị thay đổi âm thanh ở phần đầu.
        - output: Đường dẫn file output (tùy chọn).
        """
        print(f"Bắt đầu xử lý: Lấy audio từ '{os.path.basename(audio_source_path)}' chèn vào video '{os.path.basename(video_target_path)}'")
        try:
            # Lấy clip nguồn audio để biết thời lượng cần thay thế
            audio_source_clip = VideoFileClip(audio_source_path)
            swap_duration = audio_source_clip.duration
            audio_source_clip.close() 

            video_target_clip = VideoFileClip(video_target_path)
            if swap_duration > video_target_clip.duration:
                print(f"Lỗi: Video nguồn audio ({swap_duration:.2f}s) dài hơn video đích ({video_target_clip.duration:.2f}s). Bỏ qua.")
                video_target_clip.close()
                return None
            video_target_clip.close() 

            # 1. Tách âm thanh từ video nguồn (audio_source_path)
            audio_path = self.CG.extract_audio(audio_source_path)
            if not audio_path or not os.path.exists(audio_path):
                print("Lỗi: Không thể tách âm thanh từ video nguồn.")
                return None

            # 2. Cắt video đích (video_target_path) thành 2 phần dựa trên thời lượng của video nguồn
            part1_path, part2_path = self.CG.split_video_by_time(video_target_path, swap_duration)
            if not (os.path.exists(part1_path) and os.path.exists(part2_path)):
                print("Lỗi: Không thể cắt video đích.")
                return None

            # 3. Gán âm thanh đã tách ở bước 1 vào phần đầu của video đích (part1_path)
            part1_with_new_audio_path = self.CG.set_audio_video(part1_path, audio_path)
            if not os.path.exists(part1_with_new_audio_path):
                print("Lỗi: Không thể gán audio mới cho phần đầu video.")
                return None

            # 4. Ghép phần đầu đã thay đổi âm thanh với phần còn lại của video đích
            clip1 = VideoFileClip(part1_with_new_audio_path)
            clip2 = VideoFileClip(part2_path)
            
            target_resolution = (720, 1280)
            target_fps = 30
            clip1 = clip1.resize(target_resolution).set_fps(target_fps)
            clip2 = clip2.resize(target_resolution).set_fps(target_fps)

            final_clip = concatenate_videoclips([clip1, clip2])

            name1 = os.path.splitext(os.path.basename(audio_source_path))[0]
            name2 = os.path.splitext(os.path.basename(video_target_path))[0]
            final_name = f"{name2}_audioby_{name1}.mp4"
            final_path = output or os.path.join(self.output_folder, final_name)

            final_clip.write_videofile(final_path, codec="libx264", fps=target_fps)
            
            clip1.close()
            clip2.close()
            final_clip.close()
            
            print(f"Tạo video thành công: {final_path}")
            self.created_files.append(final_path)
            return final_path

        except Exception as e:
            print(f"Đã xảy ra lỗi không xác định trong quá trình xử lý: {e}")
            return None
        finally:
            self.CG.clear_temp_folder()

    def stats(self):
        print(f"\n--- THỐNG KÊ ---")
        print(f"Tổng số video đã tạo: {len(self.created_files)}")
        for f in self.created_files:
            print(f"- {f}")


if __name__ == "__main__":
    # Giả sử bạn có thư mục 'audios' chứa các video dùng để lấy nhạc
    # và thư mục 'videos_to_edit' chứa các video cần được chèn nhạc
    # và thư mục 'output_audioswap' để lưu kết quả
    
    # Tạo các thư mục và file giả để test
    os.makedirs("audios", exist_ok=True)
    os.makedirs("videos_to_edit", exist_ok=True)
    os.makedirs("output_audioswap", exist_ok=True)
    # Bạn cần có sẵn các file video trong các thư mục này. 
    # Ví dụ: 'audios/nhac1.mp4', 'videos_to_edit/canh_dep.mp4'

    merger = VideoMerger("output_audioswap")

    # ---- VÍ DỤ SỬ DỤNG HÀM MỚI ----
    # Giả sử bạn muốn chạy cho tất cả các kết hợp
    audio_folder = "videos2"
    video_folder = "videos1"
    
    audio_files = sorted([f for f in os.listdir(audio_folder) if f.lower().endswith(('.mp4', '.avi', '.mov'))])
    video_files = sorted([f for f in os.listdir(video_folder) if f.lower().endswith(('.mp4', '.avi', '.mov'))])

    for audio_file in audio_files:
        for video_file in video_files:
            audio_path = os.path.join(audio_folder, audio_file)
            video_path = os.path.join(video_folder, video_file)
            
            # Gọi hàm mới
            merger.merge_with_audio_swap_at_start(audio_path, video_path)

    merger.stats()