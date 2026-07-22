FROM python:3.10-slim

# Cài đặt ffmpeg và git
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Sao chép toàn bộ mã nguồn và file requirements vào container
COPY . .

# Cài đặt trực tiếp các thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Mở cổng động theo biến PORT của Render
ENV PORT=8501

# Chạy ứng dụng bằng module python chính thống
CMD python -m streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true