from flask import Flask, request, jsonify
from GiangVideo import combine_audio_overlay_all_pairs

app = Flask(__name__)

@app.route('/run_merge', methods=['POST'])
def run_merge():
    data = request.json
    try:
        combine_audio_overlay_all_pairs(
            data['video_folder'],
            data['audio_folder'],
            data['output_folder'],
            data['remove_original_audio']
        )
        return jsonify({"message": "Đã bắt đầu xử lý! Xem kết quả trong thư mục xuất."})
    except Exception as e:
        return jsonify({"message": f"Lỗi: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)