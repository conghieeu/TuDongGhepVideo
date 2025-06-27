from moviepy.editor import (
    VideoFileClip,
    concatenate_videoclips,
    AudioFileClip,
    CompositeAudioClip,
)
import os
import moviepy.video.fx.all as vfx

# Tải video từ YouTube
# def download_youtube_video(url, output_path='downloads'):
#     yt = YouTube(url)
#     stream = yt.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').desc().first()
#     if not os.path.exists(output_path):
#         os.makedirs(output_path)
#     file_path = stream.download(output_path=output_path)
#     return file_path


def cut_video(input_path, start_time, end_time):
    video = VideoFileClip(input_path)
    return video.subclip(start_time, end_time)


def merge_videos(clips, resolution=(720, 1280), fps=30):
    standardized_clips = [standardize_clip(c, resolution, fps) for c in clips]
    final_clip = concatenate_videoclips(standardized_clips, method="compose")
    return final_clip


def standardize_clip(clip, target_resolution=(720, 1280), target_fps=30):
    return clip.resize(target_resolution).set_fps(target_fps)


def save_clip(clip, output_path="output.mp4"):
    clip.write_videofile(output_path, threads=4, codec="libx264", audio_codec="aac")
    clip.close()


def get_video_info(clip):
    info = {
        "resolution": clip.size,
        "fps": clip.fps,
        "duration": clip.duration,
        "has_audio": clip.audio is not None,
    }
    return info


def insert_audio_clip(video, audio_path, insert_time):
    video_duration = video.duration

    try:
        audio = AudioFileClip(audio_path)
    except:
        audio_video = VideoFileClip(audio_path)
        if not audio_video.audio:
            raise ValueError("File video chèn không có âm thanh.")
        audio = audio_video.audio

    total_needed_duration = audio.duration + insert_time

    if total_needed_duration > video_duration:
        video = repeat_video_tail(video, total_needed_duration, 3)
    elif total_needed_duration < video_duration:
        video = video.subclip(0, total_needed_duration)

    new_audio = combine_audio_clips(video, audio)
    return video.set_audio(new_audio)


def repeat_video_tail(video_clip, duration, loop_duration):
    """
    Extends a video clip to a specified duration by repeating its tail segment.
    Parameters:
        video_clip (VideoFileClip): Đoạn video gốc cần xử lý.
        duration (float): Độ dài (tính bằng giây) mong muốn của video đầu ra.
        loop_duration (float): Độ dài (tính bằng giây) của đoạn cuối video sẽ được lặp lại.
    Returns:
        VideoFileClip: Đoạn video mới có độ dài đúng bằng `duration`, với phần cuối được lặp lại nếu cần thiết.
    """
    current_duration = video_clip.duration
    if current_duration >= duration:
        return video_clip.subclip(0, duration)
    tail_duration = min(loop_duration, current_duration)
    tail = video_clip.subclip(current_duration - tail_duration, current_duration)
    remaining_duration = duration - current_duration
    repeat_count = int(remaining_duration / tail_duration) + 1
    tail_loop = [tail] * repeat_count
    looped_tail = concatenate_videoclips(tail_loop)
    final_clip = concatenate_videoclips([video_clip, looped_tail])
    return final_clip.subclip(0, duration)


def combine_audio_clips(video, audio):
    base_audio = video.audio if video.audio else None
    new_audio = CompositeAudioClip([base_audio, audio] if base_audio else [audio])

    return new_audio


def merge_videos_with_audio_and_outro(
    video_folder, audio_folder, outro_folder, output_folder
):
    os.makedirs(output_folder, exist_ok=True)

    video_files = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]
    audio_files = [f for f in os.listdir(audio_folder) if f.endswith((".mp3", ".mp4"))]
    outro_files = [f for f in os.listdir(outro_folder) if f.endswith(".mp4")]

    print("📂 Danh sách video:", video_files)
    print("🎵 Danh sách audio:", audio_files)
    print("📺 Danh sách outro:", outro_files)

    for video_file in video_files:
        video_path = os.path.join(video_folder, video_file)

        # Lấy thông tin định dạng gốc từ video đầu tiên
        ref_clip = VideoFileClip(video_path)
        resolution = ref_clip.size
        fps = ref_clip.fps
        ref_clip.close()

        for audio_file in audio_files:
            audio_path = os.path.join(audio_folder, audio_file)

            for outro_file in outro_files:
                outro_path = os.path.join(outro_folder, outro_file)

                try:
                    print("Chuẩn hóa video chính và outro")
                    main_clip = standardize_clip(
                        VideoFileClip(video_path), resolution, fps
                    )
                    outro_clip = standardize_clip(
                        VideoFileClip(outro_path), resolution, fps
                    )
                    main_clip = main_clip.without_audio()
                    outro_clip = outro_clip.set_audio(outro_clip.audio.volumex(0.3))

                    print("Ghép video chính + outro")
                    merged_video = merge_videos(
                        [main_clip, outro_clip], resolution, fps
                    )

                    print("Sau khi có merged full video, mới thay thế audio")
                    video_with_audio = insert_audio_clip(
                        merged_video, audio_path, insert_time=0
                    )

                    print("Tên file xuất ra")
                    name = f"{os.path.splitext(video_file)[0]}_{os.path.splitext(audio_file)[0]}_{os.path.splitext(outro_file)[0]}"
                    output_path = os.path.join(output_folder, f"{name}.mp4")

                    save_clip(video_with_audio, output_path)
                    print(f"✅ Đã xuất: {output_path}")
                except Exception as e:
                    print(f"❌ Lỗi với {video_file} + {audio_file} + {outro_file}: {e}")


def insert_audio_clip_mix(
    video,
    audio_path,
    audio_insert_time,
    video_tail_duration,
    video_audio_gain=1.0,
    audio_insert_volume=1.0,
):
    """
    Chèn một đoạn audio vào video tại thời điểm chỉ định, trộn với âm thanh gốc của video và điều chỉnh âm lượng từng nguồn.
    Nếu tổng thời lượng video sau khi chèn audio và phần đuôi ngắn hơn yêu cầu, phần đuôi video sẽ được lặp lại để đủ thời lượng.
    Nếu dài hơn, video sẽ bị cắt ngắn lại.
    Args:
        video (VideoFileClip): Đối tượng video gốc (moviepy).
        audio_path (str): Đường dẫn tới file audio hoặc video chứa audio cần chèn.
        audio_insert_time (float): Thời điểm (tính bằng giây) bắt đầu chèn audio vào video.
        video_tail_duration (float): Thời lượng phần đuôi video sau khi audio kết thúc (tính bằng giây).
        video_audio_gain (float, optional): Hệ số điều chỉnh âm lượng audio gốc của video. Mặc định là 1.0.
        audio_insert_volume (float, optional): Hệ số điều chỉnh âm lượng audio chèn vào. Mặc định là 1.0.
    Returns:
        VideoFileClip: Đối tượng video mới đã được chèn và trộn audio.
    Raises:
        ValueError: Nếu file video/audio chèn vào không có âm thanh.
    Ghi chú:
        - Hỗ trợ cả file audio (.mp3, .wav, ...) và video có audio.
        - Âm thanh mới sẽ được trộn (mix) với âm thanh gốc của video.
        - Có thể điều chỉnh âm lượng từng nguồn âm thanh riêng biệt.
    """
    video_duration = video.duration

    # Đọc audio (hỗ trợ cả .mp3 và video có audio)
    try:
        audio = AudioFileClip(audio_path)
    except:
        audio_video = VideoFileClip(audio_path)
        if not audio_video.audio:
            raise ValueError("File video chèn không có âm thanh.")
        audio = audio_video.audio

    total_needed_duration = audio_insert_time + audio.duration + video_tail_duration

    # Nếu video quá ngắn → lặp phần đuôi video
    if total_needed_duration > video_duration:
        video = repeat_video_tail(video, total_needed_duration, 3)
    elif total_needed_duration < video_duration:
        video = video.subclip(0, total_needed_duration)

    # Trộn âm thanh: audio cũ + audio mới, có chỉnh âm lượng
    base_audio = video.audio.volumex(video_audio_gain) if video.audio else None
    new_audio = audio.volumex(audio_insert_volume).set_start(audio_insert_time)
    mixed_audio = CompositeAudioClip(
        [base_audio, new_audio] if base_audio else [new_audio]
    )

    return video.set_audio(mixed_audio)


def combine_audio_overlay_all_pairs(video_folder, audio_folder, output_folder):
    """
    Kết hợp từng file audio với từng file video trong hai thư mục, xuất ra tất cả các cặp video-audio có thể.
    Args:
        video_folder (str): Đường dẫn tới thư mục chứa các file video (.mp4).
        audio_folder (str): Đường dẫn tới thư mục chứa các file audio (.mp3, .mp4).
        output_folder (str): Đường dẫn tới thư mục xuất các file video đã ghép audio.
    Chức năng:
        - Duyệt qua tất cả các file video và audio, ghép từng audio vào từng video.
        - Chuẩn hóa độ phân giải và fps của video theo video gốc.
        - Đảm bảo video đủ dài để ghép audio.
        - Xuất file video mới với tên dạng <tên_video>_<tên_audio>.mp4 vào output_folder.
        - In ra thông báo tiến trình và lỗi (nếu có).
    Ví dụ:
        combine_audio_overlay_all_pairs("videos", "audios", "output")
    """
    os.makedirs(output_folder, exist_ok=True)

    video_files = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]
    audio_files = [f for f in os.listdir(audio_folder) if f.endswith((".mp3", ".mp4"))]

    print("📂 Danh sách video:", video_files)
    print("🎵 Danh sách audio:", audio_files)

    for video_file in video_files:
        video_path = os.path.join(video_folder, video_file)

        ref_clip = VideoFileClip(video_path)
        resolution = ref_clip.size
        fps = ref_clip.fps
        ref_clip.close()

        for audio_file in audio_files:
            audio_path = os.path.join(audio_folder, audio_file)

            try:
                print(f"▶️ Xử lý video: {video_file} + audio: {audio_file}")

                # Chuẩn hóa video
                video_clip = standardize_clip(
                    VideoFileClip(video_path), resolution, fps
                )

                # Đảm bảo có đủ độ dài để ghép audio
                video_with_audio = insert_audio_clip_mix(
                    video_clip, audio_path, 0, 3, 0.4
                )

                # Đặt tên theo dạng video_audio
                video_name, _ = os.path.splitext(video_file)
                audio_name, _ = os.path.splitext(audio_file)
                name = f"{audio_name}_{video_name}"
                output_path = os.path.join(output_folder, f"{name}.mp4")

                save_clip(video_with_audio, output_path)
                print(f"✅ Đã xuất: {output_path}")

            except Exception as e:
                print(f"❌ Lỗi với {video_file} + {audio_file}: {e}")


if __name__ == "__main__":
    print("▶️ Script bắt đầu...")

    video_folder = r"C:\Users\PC\Desktop\Processing"
    audio_folder = r"C:\Users\PC\Desktop\Processing\New folder"
    output_folder = r"C:\Users\PC\Desktop\Processing\Output"
    combine_audio_overlay_all_pairs(video_folder, audio_folder, output_folder)
