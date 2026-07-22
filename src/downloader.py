import os
import yt_dlp

def download_video(url, output_path="downloads"):
    """
    Hàm tải video từ YouTube sử dụng yt-dlp với cookie xác thực 
    và tùy chọn định dạng tự động tối ưu để tránh lỗi format không khả dụng.
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)

    ydl_opts = {
        # Tự động chọn video tốt nhất kết hợp với âm thanh tốt nhất rồi gộp lại
        'format': 'bestvideo+bestaudio/best',
        # Xuất file đầu ra chuẩn định dạng MP4
        'merge_output_format': 'mp4',
        # Thư mục lưu file tải về
        'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),
        # Đọc file cookies.txt ở thư mục gốc để vượt qua cơ chế chặn bot của YouTube
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        # Tránh ghi log quá rườm rà trên console
        'quiet': False,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Trích xuất thông tin video trước để lấy đường dẫn và tên file
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Nếu định dạng sau khi merge đổi thành mp4, cập nhật lại đuôi file cho chính xác
            base, _ = os.path.splitext(filename)
            final_filename = base + ".mp4"
            
            if os.path.exists(final_filename):
                return final_filename
            return filename
            
    except Exception as e:
        raise Exception(f"Lỗi tải video: {str(e)}")