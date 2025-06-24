import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips

class CatGhepCoBan:
    """
    Lớp chứa các hàm tiện ích cơ bản để cắt, ghép, xử lý video và audio.
    """
    # === CẤU HÌNH TẬP TRUNG ===
    TARGET_RESOLUTION = (720, 1280)
    TARGET_FPS = 30
    VIDEO_CODEC = 'libx264'

    def __init__(self, temp_folder=None):
        self.temp_folder = temp_folder or "temp"
        os.makedirs(self.temp_folder, exist_ok=True)

    def clear_temp_folder(self):
        """Xóa tất cả các file trong thư mục tạm."""
        print("Đang dọn dẹp các file tạm...")
        for filename in os.listdir(self.temp_folder):
            file_path = os.path.join(self.temp_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Lỗi khi xóa file tạm {file_path}: {e}")

    def merge_videos(self, link1, link2, output_path=None):
        """Ghép hai video lại với nhau."""
        c1 = VideoFileClip(link1).resize(self.TARGET_RESOLUTION).set_fps(self.TARGET_FPS)
        c2 = VideoFileClip(link2).resize(self.TARGET_RESOLUTION).set_fps(self.TARGET_FPS)
        out = concatenate_videoclips([c1, c2])
        default_name = f"{os.path.splitext(os.path.basename(link1))[0]}_{os.path.splitext(os.path.basename(link2))[0]}.mp4"
        final_path = output_path or os.path.join(self.temp_folder, default_name)
        
        out.write_videofile(final_path, codec=self.VIDEO_CODEC, fps=self.TARGET_FPS)
        c1.close()
        c2.close()
        out.close()
        return final_path

    def cut_head(self, input_path, duration, output_path=None):
        """Cắt bỏ phần đầu của video."""
        clip = VideoFileClip(input_path).subclip(duration)
        name = os.path.splitext(os.path.basename(input_path))[0]
        final_output_path = output_path or os.path.join(self.temp_folder, f"{name}_cuthead.mp4")
        clip.write_videofile(final_output_path, codec=self.VIDEO_CODEC)
        clip.close()
        return final_output_path

    def split_video_by_time(self, input_path, split_time, output_path1=None, output_path2=None):
        """Chia video thành 2 phần tại một thời điểm."""
        clip = VideoFileClip(input_path)
        split_time = min(split_time, clip.duration)
        clip1 = clip.subclip(0, split_time)
        clip2 = clip.subclip(split_time)
        name = os.path.splitext(os.path.basename(input_path))[0]
        final_output1 = output_path1 or os.path.join(self.temp_folder, f"{name}_part1.mp4")
        final_output2 = output_path2 or os.path.join(self.temp_folder, f"{name}_part2.mp4")
        clip1.write_videofile(final_output1, codec=self.VIDEO_CODEC)
        clip2.write_videofile(final_output2, codec=self.VIDEO_CODEC)
        
        clip1.close()
        clip2.close()
        clip.close()
        return final_output1, final_output2

    def extract_audio(self, video_path, output_path=None):
        """Chỉ tách audio từ video."""
        clip = VideoFileClip(video_path)
        name = os.path.splitext(os.path.basename(video_path))[0]
        final_audio_output = output_path or os.path.join(self.temp_folder, f"{name}_audio_only.mp3")
        if clip.audio:
            clip.audio.write_audiofile(final_audio_output)
            clip.close()
            return final_audio_output
        clip.close()
        return None

    def extract_audio_and_video(self, video_path, output_video_path=None, output_audio_path=None):
        """Tách riêng video không tiếng và audio."""
        clip = VideoFileClip(video_path)
        name = os.path.splitext(os.path.basename(video_path))[0]
        final_audio_output = output_audio_path or os.path.join(self.temp_folder, f"{name}_extract_audio.mp3")
        final_video_output = output_video_path or os.path.join(self.temp_folder, f"{name}_extract_video.mp4")
        if clip.audio:
            clip.audio.write_audiofile(final_audio_output)
        clip.without_audio().write_videofile(final_video_output, codec=self.VIDEO_CODEC)
        clip.close()
        return final_video_output, final_audio_output

    def set_audio_video(self, video_link, audio_link, output_path=None):
        """Gán một audio mới cho video. Tự động cắt audio nếu dài hơn video."""
        video = VideoFileClip(video_link)
        audio = AudioFileClip(audio_link)
        
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)
            
        name = os.path.splitext(os.path.basename(video_link))[0]
        final_output_path = output_path or os.path.join(self.temp_folder, f"{name}_set_audio_video.mp4")
        
        clip_with_new_audio = video.set_audio(audio)
        clip_with_new_audio.write_videofile(final_output_path, codec=self.VIDEO_CODEC)
        
        video.close()
        audio.close()
        clip_with_new_audio.close()
        return final_output_path

    def mix_audio_with_video(self, video_path, audio_path, output_path=None):
        """
        Trộn một audio mới vào audio gốc của video (đè âm thanh).
        Âm thanh mới sẽ được phát cùng lúc với âm thanh gốc.
        Nếu audio mới dài hơn video, nó sẽ tự động bị cắt ngắn.
        Args:
            video_path (str): Đường dẫn đến file video gốc.
            audio_path (str): Đường dẫn đến file audio cần trộn vào.
            output_path (str, optional): Đường dẫn file video đầu ra. Mặc định là None.
        Returns:
            str: Đường dẫn đến file video đã được trộn âm thanh.
        """
        print(f"Bắt đầu quá trình trộn audio từ '{audio_path}' vào video '{video_path}'...")
        video_clip = VideoFileClip(video_path)
        new_audio_clip = AudioFileClip(audio_path)
        # Cắt audio mới nếu nó dài hơn video
        if new_audio_clip.duration > video_clip.duration:
            print("Audio mới dài hơn video, đang cắt bớt...")
            new_audio_clip = new_audio_clip.subclip(0, video_clip.duration)
        # Lấy audio gốc của video
        original_audio = video_clip.audio
        # Kiểm tra xem video có audio gốc hay không
        if original_audio:
            print("Video có âm thanh gốc. Đang tiến hành trộn...")
            # Trộn audio gốc và audio mới lại với nhau
            combined_audio = CompositeAudioClip([original_audio, new_audio_clip])
        else:
            print("Video không có âm thanh gốc. Sẽ chỉ thêm audio mới.")
            # Nếu video không có audio, chỉ cần gán audio mới
            combined_audio = new_audio_clip
            
        # Gán luồng audio đã trộn vào video clip
        final_clip = video_clip.set_audio(combined_audio)
        
        # Xác định đường dẫn file output
        name = os.path.splitext(os.path.basename(video_path))[0]
        final_output_path = output_path or os.path.join(self.temp_folder, f"{name}_da_tron_am_thanh.mp4")
        
        # Ghi file video kết quả
        print(f"Đang ghi file kết quả ra '{final_output_path}'...")
        final_clip.write_videofile(final_output_path, codec=self.VIDEO_CODEC, fps=self.TARGET_FPS)
        
        # Đóng các clip để giải phóng bộ nhớ
        video_clip.close()
        new_audio_clip.close()
        final_clip.close()
        
        if original_audio:
            original_audio.close()
            
        print("Hoàn thành!")
        
        return final_output_path