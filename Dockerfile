FROM python:3.10-slim

RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Ép pip hiển thị log chi tiết và bắt buộc cài đặt trực tiếp
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8501
EXPOSE 8501

# Gọi trực tiếp module Python thay vì lệnh tắt
CMD python3 -m streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true