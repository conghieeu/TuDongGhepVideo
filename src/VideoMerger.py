import os 
from moviepy import VideoFileClip, concatenate_videoclips
import ffmpeg

class VideoMerger:
    def __init__(self, output_folder):
        self.output_folder = output_folder
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.created_files = []

    def merge_videos(self, link1, link2):
        clip1 = VideoFileClip(link1)
        clip2 = VideoFileClip(link2)
        final_clip = concatenate_videoclips([clip1, clip2])
        name1 = os.path.splitext(os.path.basename(link1))[0]
        name2 = os.path.splitext(os.path.basename(link2))[0]
        output_name = f"{name1}_{name2}.mp4"
        output_path = os.path.join(self.output_folder, output_name)
        final_clip.write_videofile(output_path, codec="libx264")
        clip1.close()
        clip2.close()
        final_clip.close()
        self.created_files.append(output_name)
        print(f"Đã ghép: {link1} + {link2} -> {output_path}")

    def cut_head(self, input_path, duration, output_path=None):
        """
        Cắt đoạn đầu của video với thời lượng 'duration' (tính bằng giây).
        Kết quả là video mới bắt đầu từ thời điểm 'duration' đến hết.
        """
        if output_path is None:
            name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(self.output_folder, f"{name}_cuthead.mp4")
        (
            ffmpeg
            .input(input_path, ss=duration)
            .output(output_path, codec='copy')
            .run(overwrite_output=True, quiet=True)
        )
        print(f"Đã cắt đầu {duration} giây: {input_path} -> {output_path}")
        return output_path

    def merge_with_trimmed_second(self, link1, link2):
        # Lấy thời lượng video1
        probe1 = ffmpeg.probe(link1)
        duration1 = float(probe1['format']['duration'])
        # Lấy thời lượng video2
        probe2 = ffmpeg.probe(link2)
        duration2 = float(probe2['format']['duration'])
        if duration1 >= duration2:
            print("Video 1 dài hơn hoặc bằng video 2, không thể cắt video 2.")
            return
        # Cắt đầu video2 bằng cut_head
        trimmed2 = self.cut_head(link2, duration1)
        # Ghép video1 và trimmed2
        name1 = os.path.splitext(os.path.basename(link1))[0]
        name2 = os.path.splitext(os.path.basename(link2))[0]
        output_name = f"{name1}_{name2}_special.mp4"
        output_path = os.path.join(self.output_folder, output_name)
        # Tạo file list cho ffmpeg concat
        concat_list = os.path.join(self.output_folder, "concat_list.txt")
        with open(concat_list, "w", encoding="utf-8") as f:
            f.write(f"file '{os.path.abspath(link1)}'\n")
            f.write(f"file '{os.path.abspath(trimmed2)}'\n")
        (
            ffmpeg
            .input(concat_list, format='concat', safe=0)
            .output(output_path, c='copy')
            .run(overwrite_output=True, quiet=True)
        )
        # Xóa file tạm
        os.remove(trimmed2)
        os.remove(concat_list)
        self.created_files.append(output_name)
        print(f"Đã ghép đặc biệt: {link1} + {link2} (cắt đầu video 2) -> {output_path}")

    def merge_all_combinations(self, folder1, folder2):
        files1 = sorted([f for f in os.listdir(folder1) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))])
        files2 = sorted([f for f in os.listdir(folder2) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))])
        for file1 in files1:
            for file2 in files2:
                path1 = os.path.join(folder1, file1)
                path2 = os.path.join(folder2, file2)
                self.merge_videos(path1, path2)

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

# merge_videos("video1.mp4", "video2.mp4", "merged_video.mp4")
merger = VideoMerger("merged_videos")
merger.merge_all_combinations_trimmed("videos1", "videos2")