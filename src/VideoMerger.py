import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips


class CatGhepCoBan:
    def __init__(self, temp_folder=None):
        self.temp_folder = temp_folder or "temp"
        os.makedirs(self.temp_folder, exist_ok=True)

    def clear_temp_folder(self):
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
        # Đảm bảo đồng bộ resolution và fps
        target_resolution = (720, 1280)
        target_fps = 30
        c1 = c1.resize(target_resolution).set_fps(target_fps)
        c2 = c2.resize(target_resolution).set_fps(target_fps)
        out = concatenate_videoclips([c1, c2])
        name = f"{os.path.splitext(os.path.basename(link1))[0]}_{os.path.splitext(os.path.basename(link2))[0]}.mp4"
        path = os.path.join(self.temp_folder, name)
        # Ghi rõ fps khi xuất
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
        clip1 = clip.subclip(0, split_time)
        clip2 = clip.subclip(split_time)
        clip1.write_videofile(output1, codec='libx264')
        clip2.write_videofile(output2, codec='libx264')
        clip1.close()
        clip2.close()
        clip.close()
        return output1, output2

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
        audio = AudioFileClip(audio_link).subclip(0, video.duration)
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
        c1 = VideoFileClip(link1)
        if c1.duration <= 0.5:
            raise ValueError(f"Video {link1} quá ngắn")
        # Cắt video thứ 2 thành 2 phần
        try:
            trimmed1, trimmed2 = self.CG.split_video_by_time(link2, c1.duration)
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
            c1.close()
            self.CG.clear_temp_folder()
            return final_path
        except Exception as e:
            print(f"Lỗi khi gộp video: {e}")
            return None

    def merge_all_combinations(self, folder1, folder2):
        files1 = sorted([f for f in os.listdir(folder1) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))])
        files2 = sorted([f for f in os.listdir(folder2) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))])
        for file1 in files1:
            for file2 in files2:
                path1 = os.path.join(folder1, file1)
                path2 = os.path.join(folder2, file2)
                out = self.merge_with_trimmed_second(path1, path2)
                final_path = os.path.join(self.output_folder, os.path.basename(out))
                os.rename(out, final_path)
                self.created_files.append(final_path)

    def merge_all_combinations_trimmed(self, folder1, folder2):
        files1 = sorted([f for f in os.listdir(folder1) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))])
        files2 = sorted([f for f in os.listdir(folder2) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))])
        for file1 in files1:
            for file2 in files2:
                path1 = os.path.join(folder1, file1)
                path2 = os.path.join(folder2, file2)
                self.merge_with_trimmed_second(path1, path2)

    def stats(self):
        print(f"Tổng số video đã tạo: {len(self.created_files)}")
        for f in self.created_files:
            print(f"- {f}")


# Example usage:
if __name__ == "__main__":
    merger = VideoMerger("output")
    # result = merger.merge_with_trimmed_second("1.mp4", "15.mp4")
    result = merger.merge_all_combinations_trimmed("videos1", "videos2")
    print(f"Video created: {result}")
    merger.stats()
