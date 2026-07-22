# app.py
import streamlit as st
import os
import sys
from pathlib import Path

# Thêm thư mục hiện tại vào path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.pipeline import VideoTranslationPipeline

# Cấu hình trang
st.set_page_config(
    page_title="DuckDuckChill13 - Winter Aurora Deluxe Studio",
    page_icon="🦆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Giao diện CSS tùy chỉnh nâng cao (Đêm Mùa Đông, Sao Băng Lấp Lánh, Tuyết Dày, Thẻ Thống Kê 3D)
st.markdown("""
<style>
    /* Tổng thể nền Đêm Mùa Đông & Hiệu ứng Cực Quang */
    .stApp {
        background: radial-gradient(circle at 50% 0%, rgb(15, 23, 42) 0%, rgb(7, 13, 26) 50%, rgb(2, 6, 23) 100%);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
        overflow-x: hidden;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* --- KHUNG HIỆU ỨNG ĐỘNG (TUYẾT & SAO BĂNG LẤP LÁNH) --- */
    #winter-effects-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 99999;
        overflow: hidden;
    }

    /* Sao băng lấp lánh rực rỡ */
    .shooting-star {
        position: absolute;
        width: 160px;
        height: 3px;
        background: linear-gradient(90deg, rgba(255, 255, 255, 1), rgba(56, 189, 248, 0.8), rgba(129, 140, 248, 0));
        transform: rotate(-45deg);
        animation: shootAndGlow linear infinite;
        opacity: 0;
        filter: drop-shadow(0 0 10px rgba(56, 189, 248, 0.9));
    }

    .shooting-star:nth-child(1) { top: 5%; left: 85%; animation-delay: 0s; animation-duration: 3.2s; }
    .shooting-star:nth-child(2) { top: 12%; left: 98%; animation-delay: 1.5s; animation-duration: 4s; }
    .shooting-star:nth-child(3) { top: 1%; left: 45%; animation-delay: 2.8s; animation-duration: 3.5s; }
    .shooting-star:nth-child(4) { top: 20%; left: 70%; animation-delay: 4.5s; animation-duration: 3.8s; }

    @keyframes shootAndGlow {
        0% {
            transform: translateX(0) translateY(0) rotate(-45deg) scale(0.8);
            opacity: 1;
            filter: drop-shadow(0 0 12px rgba(255, 255, 255, 1));
        }
        70% {
            opacity: 1;
        }
        100% {
            transform: translateX(-700px) translateY(700px) rotate(-45deg) scale(1.2);
            opacity: 0;
            filter: drop-shadow(0 0 2px rgba(56, 189, 248, 0));
        }
    }

    /* Các hạt tuyết dày đặc, đa tầng chiều sâu */
    .snowflake {
        position: absolute;
        top: -15px;
        background: #ffffff;
        border-radius: 50%;
        filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.9));
        animation: snowfall linear infinite;
    }

    @keyframes snowfall {
        0% {
            transform: translateY(-15px) translateX(0);
            opacity: 1;
        }
        50% {
            transform: translateY(52vh) translateX(30px);
            opacity: 0.7;
        }
        100% {
            transform: translateY(106vh) translateX(-30px);
            opacity: 0.2;
        }
    }

    /* --- HERO SECTION 3D SANG TRỌNG --- */
    .hero-container {
        padding: 3.5rem 2rem;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 28px;
        text-align: center;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(16px);
        margin-bottom: 2rem;
        animation: fadeInDown 0.8s ease-out;
        position: relative;
        z-index: 2;
    }

    .hero-title {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #38bdf8 0%, #a5f3fc 40%, #818cf8 80%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        letter-spacing: -1px;
    }

    .hero-subtitle {
        font-size: 1.2rem;
        color: #94a3b8;
        max-width: 750px;
        margin: 0 auto;
        line-height: 1.7;
    }

    /* Thẻ Card Glassmorphism Chính */
    .glass-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2.8rem;
        box-shadow: 0 20px 45px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(18px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        z-index: 2;
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 25px 50px rgba(56, 189, 248, 0.25);
    }

    /* Thẻ Tính Năng Phụ (Feature Mini Cards) */
    .feature-grid {
        display: flex;
        gap: 1.5rem;
        margin-top: 2rem;
        margin-bottom: 2.5rem;
        z-index: 2;
        position: relative;
    }

    .feature-box {
        flex: 1;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }

    .feature-box:hover {
        border-color: rgba(56, 189, 248, 0.5);
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(56, 189, 248, 0.15);
        background: rgba(30, 41, 59, 0.8);
    }

    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    .feature-title {
        font-weight: 700;
        color: #38bdf8;
        font-size: 1rem;
        margin-bottom: 0.3rem;
    }

    .feature-desc {
        color: #94a3b8;
        font-size: 0.85rem;
    }

    /* Input & Selectbox */
    .stTextInput input, .stSelectbox select {
        background-color: rgba(15, 23, 42, 0.75) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 14px !important;
        padding: 0.8rem 1.1rem !important;
        transition: all 0.3s ease;
    }

    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.4) !important;
    }

    /* Nút bấm (Button) phong cách cao cấp */
    .stButton button {
        width: 100%;
        background: linear-gradient(135deg, #0284c7 0%, #3b82f6 50%, #6366f1 100%);
        color: white;
        font-weight: 700;
        font-size: 1.15rem;
        padding: 0.9rem 2rem;
        border-radius: 16px;
        border: none;
        box-shadow: 0 12px 30px rgba(59, 130, 246, 0.45);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .stButton button:hover {
        transform: translateY(-3px) scale(1.01);
        box-shadow: 0 18px 35px rgba(56, 189, 248, 0.65);
        background: linear-gradient(135deg, #0ea5e9 0%, #4f46e5 100%);
    }

    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
        100% { transform: translateY(0px); }
    }
    
    .floating-badge {
        display: inline-block;
        padding: 0.45rem 1.2rem;
        background: rgba(56, 189, 248, 0.15);
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 50px;
        color: #38bdf8;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 1.2rem;
        animation: float 3s ease-in-out infinite;
    }

    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.96);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        z-index: 10;
    }
</style>

<!-- KHUNG HIỆU ỨNG ĐỘNG (TUYẾT DÀY & SAO BĂNG LẤP LÁNH) -->
<div id="winter-effects-container">
    <div class="shooting-star"></div>
    <div class="shooting-star"></div>
    <div class="shooting-star"></div>
    <div class="shooting-star"></div>
</div>

<script>
    const container = document.getElementById('winter-effects-container');
    const snowflakeCount = 75;

    for (let i = 0; i < snowflakeCount; i++) {
        const snowflake = document.createElement('div');
        snowflake.classList.add('snowflake');
        
        const size = Math.random() * 6 + 2;
        snowflake.style.width = `${size}px`;
        snowflake.style.height = `${size}px`;
        
        snowflake.style.left = `${Math.random() * 100}vw`;
        
        const duration = Math.random() * 6 + 4;
        snowflake.style.animationDuration = `${duration}s`;
        
        const delay = Math.random() * 9;
        snowflake.style.animationDelay = `${delay}s`;
        
        snowflake.style.opacity = Math.random() * 0.8 + 0.2;
        
        container.appendChild(snowflake);
    }
</script>
""", unsafe_allow_html=True)

# --- Sidebar Thông tin ---
with st.sidebar:
    st.markdown("### 🦆 DuckDuckChill13 Studio")
    st.markdown("---")
    st.markdown("**Trạng thái:** 🟢 Tuyết & Sao băng Lấp lánh")
    st.markdown("**Engine AI:** Whisper + Edge-TTS")
    st.markdown("---")
    st.info("💡 **Mẹo:** Thưởng thức không gian chill tuyệt đỉnh dưới bầu trời mùa đông cùng DuckDuckChill13.")
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("© 2026 DuckDuckChill13. All rights reserved.")

# --- Phần Hero Section Chính ---
st.markdown("""
    <div class="hero-container">
        <div class="floating-badge">🦆 DuckDuckChill13 • AI Video Studio</div>
        <div class="hero-title">Video Translation & Dubbing</div>
        <div class="hero-subtitle">
            Hệ thống dịch thuật và lồng tiếng video tự động đẳng cấp. 
            Tận hưởng không gian mùa đông lãng mạn dưới bầu trời sao băng lấp lánh cùng DuckDuckChill13.
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Các thẻ tính năng phụ ---
st.markdown("""
    <div class="feature-grid">
        <div class="feature-box">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">Tốc Độ Siêu Tốc</div>
            <div class="feature-desc">Xử lý media đa luồng tối ưu hóa hiệu năng tối đa.</div>
        </div>
        <div class="feature-box">
            <div class="feature-icon">🎙️</div>
            <div class="feature-title">Lồng Tiếng AI</div>
            <div class="feature-desc">Giọng đọc Microsoft Edge-TTS mượt mà, tự nhiên.</div>
        </div>
        <div class="feature-box">
            <div class="feature-icon">🎯</div>
            <div class="feature-title">Độ Chính Xác Cao</div>
            <div class="feature-desc">Nhận diện ngữ nghĩa bằng Whisper AI thế hệ mới.</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Layout Form Chính ---
col_left, col_center, col_right = st.columns([1, 10, 1])

with col_center:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    with st.form("translation_form"):
        st.markdown("### ⚙️ Thiết Lập Thông Số Xử Lý Video")
        st.write("")
        
        url = st.text_input(
            "🔗 Đường dẫn Video (YouTube, TikTok, Facebook hoặc file local):", 
            placeholder="Ví dụ: https://www.youtube.com/watch?v=..."
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            source_lang = st.selectbox("🌐 Ngôn ngữ gốc", ["auto", "en", "ja", "ko", "zh", "fr", "es"], index=0)
        with c2:
            target_lang = st.selectbox("🎯 Ngôn ngữ đích", ["vi", "en", "ja", "ko", "zh", "fr"], index=0)
        with c3:
            whisper_model = st.selectbox("🤖 Model Whisper", ["base", "small", "medium"], index=0)
            
        st.markdown("<br>", unsafe_allow_html=True)
        mode = st.radio(
            "🎛️ Lựa chọn chế độ vận hành:", 
            ["🎬 Dịch & Lồng tiếng đầy đủ (Full Dubbing)", "📝 Chỉ tạo phụ đề (Subtitle only)", "🎙️ Chỉ lồng tiếng (Dub only)"],
            horizontal=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 KHỞI TẠO TIẾN TRÌNH XỬ LÝ AI")

    st.markdown('</div>', unsafe_allow_html=True)

    # Xử lý sự kiện khi bấm nút
    if submitted:
        if not url.strip():
            st.warning("⚠️ Vui lòng nhập đường dẫn video hợp lệ trước khi bắt đầu!")
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.status("🌟 DuckDuckChill13 đang kích hoạt Pipeline AI xử lý video...", expanded=True) as status:
                st.write("🔍 Đang phân tích và tải xuống dữ liệu media...")
                
                subtitle_only = ("Chỉ tạo phụ đề" in mode)
                dub_only = ("Chỉ lồng tiếng" in mode)
                
                pipeline = VideoTranslationPipeline(
                    source_lang=source_lang,
                    target_lang=target_lang,
                    whisper_model=whisper_model,
                    output_dir="output",
                    temp_dir="temp",
                    download_dir="downloads"
                )
                
                st.write("🎙️ Đang nhận diện giọng nói & tiến hành dịch thuật thông minh...")
                result = pipeline.run(url=url.strip(), subtitle_only=subtitle_only, dub_only=dub_only)
                
                if result["success"]:
                    status.update(label="✨ DuckDuckChill13 đã hoàn thành xuất sắc toàn bộ quy trình!", state="complete", expanded=False)
                    st.balloons()
                    
                    st.success("🎉 Video của bạn đã sẵn sàng để thưởng thức!")
                    
                    output_path = result["output_path"]
                    if os.path.exists(output_path):
                        down_col1, down_col2 = st.columns(2)
                        with down_col1:
                            with open(output_path, "rb") as f:
                                st.download_button(
                                    label="📥 Tải xuống Video hoàn chỉnh (MP4)",
                                    data=f,
                                    file_name=os.path.basename(output_path),
                                    mime="video/mp4"
                                )
                        with down_col2:
                            st.info(f"📂 Lưu tại: `{output_path}`")
                            
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("### 👁️ Xem trước kết quả trực tuyến:")
                        st.video(output_path)
                else:
                    status.update(label="❌ Tiến trình xử lý gặp sự cố!", state="error", expanded=True)
                    st.error(f"Chi tiết lỗi: {result.get('error', 'Không xác định')}")