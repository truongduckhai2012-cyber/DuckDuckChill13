FROM python:3.10-slim

# Cài đặt ffmpeg và các công cụ hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Sao chép file requirements và cài đặt các thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Mở cổng động bằng biến môi trường PORT của Render (mặc định fallback về 8501)
ENV PORT=8501

# Lệnh khởi động sử dụng biến $PORT linh hoạt
CMD streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true