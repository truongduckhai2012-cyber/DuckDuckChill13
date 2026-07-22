FROM python:3.10-slim

# Cài đặt ffmpeg và git
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Nâng cấp pip và cài đặt trực tiếp các thư viện từ requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ source code vào container
COPY . .

# Khai báo biến môi trường PORT của Render
ENV PORT=8501

# Lệnh chạy ứng dụng Streamlit
CMD streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true