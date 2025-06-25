# Cần cài đặt moviepy: pip install moviepy
from moviepy import VideoFileClip, concatenate_videoclips
import os

def merge_two_videos(video_path1, video_path2, output_path="merged_output.mp4"):
    """
    Ghép hai tệp video bằng MoviePy v2.2.1 và lưu kết quả.

    Args:
        video_path1 (str): Đường dẫn đến tệp video thứ nhất.
        video_path2 (str): Đường dẫn đến tệp video thứ hai.
        output_path (str): Đường dẫn để lưu tệp video đã ghép.
    """
    # Kiểm tra xem các tệp video đầu vào có tồn tại không
    if not os.path.exists(video_path1):
        print(f"Lỗi: Không tìm thấy tệp '{video_path1}'")
        return
    if not os.path.exists(video_path2):
        print(f"Lỗi: Không tìm thấy tệp '{video_path2}'")
        return

    clip1 = None
    clip2 = None
    final_clip = None

    try:
        # Bước 1: Tải hai tệp video vào các đối tượng VideoFileClip
        print(f"Đang tải video 1: {video_path1}")
        clip1 = VideoFileClip(video_path1)
        
        print(f"Đang tải video 2: {video_path2}")
        clip2 = VideoFileClip(video_path2)

        # Bước 2: Ghép hai clip lại với nhau
        # Hàm concatenate_videoclips nhận một danh sách các đối tượng Clip
        # Sử dụng method="compose" để tránh lỗi hiển thị khi hai video có độ phân giải khác nhau
        print("Đang tiến hành ghép nối hai video...")
        final_clip = concatenate_videoclips([clip1, clip2], method="compose")

        # Bước 3: Ghi kết quả ra tệp video mới
        # Chỉ định codec video và audio để đảm bảo tính tương thích cao
        print(f"Đang ghi tệp kết quả vào '{output_path}'...")
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        print("\nGhép video thành công!")
        print(f"Tệp đã được lưu tại: {os.path.abspath(output_path)}")

    except Exception as e:
        print(f"\nĐã xảy ra lỗi trong quá trình xử lý: {e}")

    finally:
        # Bước 4: Đóng tất cả các clip để giải phóng tài nguyên hệ thống
        # Đây là bước cực kỳ quan trọng để tránh rò rỉ bộ nhớ
        print("Đang giải phóng tài nguyên...")
        if clip1:
            clip1.close()
        if clip2:
            clip2.close()
        if final_clip:
            final_clip.close()

# --- VÍ DỤ SỬ DỤNG ---
if __name__ == '__main__':
    # Vui lòng thay thế bằng đường dẫn thực tế đến các tệp video của bạn
    # Để chạy ví dụ này, hãy tạo 2 tệp video tên là 'input_video_1.mp4' và 'input_video_2.mp4'
    # và đặt chúng trong cùng thư mục với tệp script này.
    
    path_video_1 = "video1.mp4"
    path_video_2 = "video2.mp4"
    output_filename = "final_video.mp4"

    # Gọi hàm để thực hiện việc ghép nối
    merge_two_videos(path_video_1, path_video_2, output_filename)