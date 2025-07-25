import os
import shutil
import uuid
import socket  # Thêm thư viện socket để lấy địa chỉ IP
from flask import Flask, request, send_file, jsonify, render_template
from werkzeug.utils import secure_filename

# Quan trọng: Import hàm xử lý từ file của bạn
try:
    from GiangVideo import combine_audio_overlay_all_pairs
except ImportError:
    print(
        "LỖI: Không tìm thấy tệp 'GiangVideo.py' hoặc hàm 'combine_audio_overlay_all_pairs'."
    )
    print("Hãy đảm bảo tệp 'GiangVideo.py' ở cùng thư mục với 'run_merge.py'.")
    exit()

# Khởi tạo ứng dụng Flask
app = Flask(__name__, template_folder=".")

# Cấu hình thư mục tạm để lưu file upload và output
# Sử dụng thư mục 'temp' trong thư mục hiện tại
BASE_TEMP_DIR = os.path.join(os.getcwd(), "temp_processing_files")
os.makedirs(BASE_TEMP_DIR, exist_ok=True)


@app.route("/")
def index():
    """
    Hàm này phục vụ file index.html cho giao diện người dùng.
    """
    try:
        return render_template("index.html")
    except Exception as e:
        return (
            f"Lỗi: Không tìm thấy file index.html. Hãy chắc chắn nó ở cùng thư mục. Chi tiết: {e}",
            404,
        )


@app.route("/process", methods=["POST"])
def process_videos():
    """
    Hàm này xử lý việc upload file, gọi hàm ghép video, nén và trả về kết quả.
    """
    # Tạo một thư mục phiên duy nhất để xử lý các yêu cầu đồng thời
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(BASE_TEMP_DIR, session_id)

    video_dir = os.path.join(session_dir, "videos")
    audio_dir = os.path.join(session_dir, "audios")
    output_dir = os.path.join(session_dir, "output")

    zip_path = None  # Khởi tạo biến zip_path
    try:
        # Tạo các thư mục cần thiết
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # Lấy danh sách file từ request
        video_files = request.files.getlist("videos")
        audio_files = request.files.getlist("audios")

        if not video_files or not audio_files:
            return jsonify({"error": "Vui lòng cung cấp cả tệp video và audio."}), 400

        # Lưu các tệp video đã tải lên
        for file in video_files:
            # SỬA LỖI: Kiểm tra xem file và file.filename có tồn tại không
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(video_dir, filename))

        # Lưu các tệp audio đã tải lên
        for file in audio_files:
            # SỬA LỖI: Kiểm tra xem file và file.filename có tồn tại không
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(audio_dir, filename))

        # Lấy tùy chọn xóa audio gốc (giá trị là 'true' hoặc 'false' từ JS)
        remove_original_audio = request.form.get("remove_original_audio") == "true"

        print(f"▶️ Bắt đầu xử lý cho phiên {session_id}...")
        print(f"   - Thư mục video: {video_dir}")
        print(f"   - Thư mục audio: {audio_dir}")
        print(f"   - Thư mục output: {output_dir}")
        print(f"   - Xóa audio gốc: {remove_original_audio}")

        # Gọi hàm xử lý chính từ file GiangVideo.py
        combine_audio_overlay_all_pairs(
            video_folder=video_dir,
            audio_folder=audio_dir,
            output_folder=output_dir,
            remove_original_audio=remove_original_audio,
        )

        print(f"✅ Xử lý hoàn tất cho phiên {session_id}.")

        # Kiểm tra xem có file nào được tạo ra không
        if not os.listdir(output_dir):
            print(f"⚠️ Không có file nào được tạo ra trong thư mục output.")
            return (
                jsonify(
                    {
                        "error": "Xử lý hoàn tất nhưng không có video nào được tạo ra. Vui lòng kiểm tra log của server."
                    }
                ),
                500,
            )

        # Nén thư mục output thành file zip
        zip_filename = f"processed_{session_id}"
        zip_path_without_ext = os.path.join(BASE_TEMP_DIR, zip_filename)
        zip_path = shutil.make_archive(zip_path_without_ext, "zip", output_dir)

        print(f"📦 Đã nén kết quả vào: {zip_path}")

        # Trả file zip về cho người dùng
        return send_file(
            zip_path, as_attachment=True, download_name="processed_videos.zip"
        )

    except Exception as e:
        print(f"❌ Đã xảy ra lỗi trong quá trình xử lý: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        # Dọn dẹp: Xóa thư mục của phiên làm việc sau khi đã hoàn tất
        try:
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
                print(f"🧹 Đã dọn dẹp thư mục tạm: {session_dir}")
        except Exception as cleanup_error:
            print(
                f"⚠️ Lỗi trong quá trình dọn dẹp thư mục {session_dir}: {cleanup_error}"
            )
            print(
                "   (Điều này có thể xảy ra trên Windows nếu file đang bị khóa. Thư mục sẽ được xóa sau.)"
            )

        # Xóa file zip nếu có
        try:
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
                print(f"🧹 Đã dọn dẹp tệp zip: {zip_path}")
        except Exception as cleanup_error:
            print(f"⚠️ Lỗi trong quá trình dọn dẹp tệp zip {zip_path}: {cleanup_error}")


if __name__ == "__main__":

    def get_local_ip():
        """Hàm này tìm địa chỉ IP cục bộ của máy."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Không cần phải kết nối được, chỉ cần thử để lấy IP
            s.connect(("10.255.255.255", 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = "127.0.0.1"  # Trả về IP mặc định nếu không tìm thấy
        finally:
            s.close()
        return IP

    local_ip = get_local_ip()
    port = 5000

    print("===================================================")
    print("          SERVER GHÉP VIDEO ĐANG CHẠY")
    print("===================================================")
    print(
        "1. Đặt các tệp 'run_merge.py', 'index.html', 'GiangVideo.py' vào cùng một thư mục."
    )
    print("2. Mở trình duyệt và truy cập:")
    print(f"   - Trên máy này: http://127.0.0.1:{port} hoặc http://localhost:{port}")
    print(f"   - Trên máy khác cùng mạng Wi-Fi: http://{local_ip}:{port}")
    print("3. Nhấn Ctrl+C trong cửa sổ terminal này để dừng server.")
    print("---------------------------------------------------")
    # Chạy server, host='0.0.0.0' để có thể truy cập từ các máy khác trong mạng
    app.run(host="0.0.0.0", port=5000, debug=True)