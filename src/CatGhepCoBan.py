import os
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
)


class CatGhepCoBan:
    """
    Lớp chứa các hàm tiện ích cơ bản để cắt, ghép, xử lý video và audio.
    Hàm __init__ cho phép tùy chỉnh cấu hình hoặc dùng giá trị mặc định.
    """

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

    def clear_temp_folder(self):
        """Xóa tất cả các file trong thư mục tạm."""
        for filename in os.listdir(self.temp_folder):
            file_path = os.path.join(self.temp_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Lỗi khi xóa file tạm {file_path}: {e}")

    def merge_videos(self, link1, link2, output_path=None):
        """Ghép hai video lại với nhau."""
        c1 = (
            VideoFileClip(link1).resize(self.target_resolution).set_fps(self.target_fps)
        )
        c2 = (
            VideoFileClip(link2).resize(self.target_resolution).set_fps(self.target_fps)
        )
        out = concatenate_videoclips([c1, c2])
        default_name = f"{os.path.splitext(os.path.basename(link1))[0]}_{os.path.splitext(os.path.basename(link2))[0]}.mp4"
        final_path = output_path or os.path.join(self.temp_folder, default_name)
        out.write_videofile(final_path, codec=self.video_codec, fps=self.target_fps)
        c1.close()
        c2.close()
        out.close()
        return final_path

    def extract_audio(self, video_path, output_path=None):
        """Chỉ tách audio từ video."""
        with VideoFileClip(video_path) as clip:
            if clip.audio:
                name = os.path.splitext(os.path.basename(video_path))[0]
                final_audio_output = output_path or os.path.join(
                    self.temp_folder, f"{name}_audio_only.mp3"
                )
                clip.audio.write_audiofile(final_audio_output)
                return final_audio_output
        return None

    def set_audio_video(self, video_link, audio_link, output_path=None):
        """Gán một audio mới cho video. Tự động cắt audio nếu dài hơn video."""
        video = VideoFileClip(video_link)
        # SỬA LỖI: Tải audio thông qua VideoFileClip để có đối tượng audio ổn định hơn
        audio_temp_clip = VideoFileClip(audio_link)
        audio = audio_temp_clip.audio

        if audio.duration > video.duration:
            # SỬA LỖI: Quay lại dùng subclip() trên đối tượng audio mới
            audio = audio.subclip(0, video.duration)

        video_with_new_audio = video.set_audio(audio)

        name = os.path.splitext(os.path.basename(video_link))[0]
        final_output_path = output_path or os.path.join(
            self.temp_folder, f"{name}_new_audio.mp4"
        )

        video_with_new_audio.write_videofile(
            final_output_path, codec=self.video_codec, fps=self.target_fps
        )

        video.close()
        audio_temp_clip.close()  # Nhớ đóng file tạm
        video_with_new_audio.close()
        return final_output_path

    def replace_audio(self, video_path, new_audio_path, output_path=None):
        """
        Thay thế hoàn toàn audio gốc của video bằng một audio mới.
        Nếu audio mới dài hơn video, nó sẽ được cắt để bằng thời lượng của video.
        """
        video_clip = VideoFileClip(video_path)
        # SỬA LỖI: Tải audio thông qua VideoFileClip
        audio_temp_clip = VideoFileClip(new_audio_path)
        audio_clip = audio_temp_clip.audio

        if audio_clip.duration > video_clip.duration:
            # SỬA LỖI: Quay lại dùng subclip() trên đối tượng audio mới
            audio_clip = audio_clip.subclip(0, video_clip.duration)

        final_clip = video_clip.set_audio(audio_clip)

        base_name = os.path.splitext(os.path.basename(video_path))[0]
        default_output_name = f"{base_name}_audio_replaced.mp4"
        final_output_path = output_path or os.path.join(
            self.temp_folder, default_output_name
        )

        final_clip.write_videofile(
            final_output_path, codec=self.video_codec, fps=self.target_fps
        )

        video_clip.close()
        audio_temp_clip.close()  # Nhớ đóng file tạm
        final_clip.close()
        return final_output_path

    def split_video_by_time(
        self, input_path, split_time, output_path1=None, output_path2=None
    ):
        """Chia video thành 2 phần tại một thời điểm."""
        with VideoFileClip(input_path) as clip:
            split_time = min(split_time, clip.duration)
            clip1 = clip.subclip(0, split_time)
            clip2 = clip.subclip(split_time)

            name = os.path.splitext(os.path.basename(input_path))[0]
            final_output1 = output_path1 or os.path.join(
                self.temp_folder, f"{name}_part1.mp4"
            )
            final_output2 = output_path2 or os.path.join(
                self.temp_folder, f"{name}_part2.mp4"
            )

            # SỬA LỖI: Thêm tham số fps=self.target_fps để đảm bảo FPS đồng nhất
            clip1.write_videofile(
                final_output1, codec=self.video_codec, fps=self.target_fps
            )
            clip2.write_videofile(
                final_output2, codec=self.video_codec, fps=self.target_fps
            )

            return final_output1, final_output2

    def mix_two_audios(
        self, audio_path1, audio_path2, output_path=None, duration_limit=None
    ):
        """Trộn hai file audio lại với nhau và lưu thành file mới."""
        # SỬA LỖI: Tải audio thông qua VideoFileClip
        temp_audio1 = VideoFileClip(audio_path1)
        audio1 = temp_audio1.audio
        temp_audio2 = VideoFileClip(audio_path2)
        audio2 = temp_audio2.audio

        clips_to_mix = []
        for aud in [audio1, audio2]:
            if duration_limit and aud.duration > duration_limit:
                # SỬA LỖI: Quay lại dùng subclip() trên đối tượng audio mới
                clips_to_mix.append(aud.subclip(0, duration_limit))
            else:
                clips_to_mix.append(aud)

        combined_audio = CompositeAudioClip(clips_to_mix)

        name1 = os.path.splitext(os.path.basename(audio_path1))[0]
        name2 = os.path.splitext(os.path.basename(audio_path2))[0]
        default_name = f"{name1}_{name2}_mixed.mp3"
        final_output_path = output_path or os.path.join(self.temp_folder, default_name)

        combined_audio.write_audiofile(final_output_path)

        temp_audio1.close()
        temp_audio2.close()
        return final_output_path

    def mix_audio_with_video(self, video_path, new_audio_path, output_path=None):
        """
        Trộn một audio mới vào audio gốc của video.
        """
        video_clip = VideoFileClip(video_path)
        # SỬA LỖI: Tải audio thông qua VideoFileClip
        new_audio_temp_clip = VideoFileClip(new_audio_path)
        new_audio_clip = new_audio_temp_clip.audio

        if new_audio_clip.duration > video_clip.duration:
            # SỬA LỖI: Quay lại dùng subclip() trên đối tượng audio mới
            # Đây là dòng gây lỗi trong log của bạn.
            new_audio_clip = new_audio_clip.subclip(0, video_clip.duration)

        if video_clip.audio:
            final_audio = CompositeAudioClip([video_clip.audio, new_audio_clip])
        else:
            final_audio = new_audio_clip

        final_clip = video_clip.set_audio(final_audio)

        name = os.path.splitext(os.path.basename(video_path))[0]
        final_output_path = output_path or os.path.join(
            self.temp_folder, f"{name}_da_tron_am_thanh.mp4"
        )

        final_clip.write_videofile(
            final_output_path, codec=self.video_codec, fps=self.target_fps
        )

        video_clip.close()
        new_audio_temp_clip.close()  # Nhớ đóng file tạm
        final_clip.close()

        return final_output_path
