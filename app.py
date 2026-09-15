import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import time
import pandas as pd

# Konfigurasi Halaman & Tema
st.set_page_config(page_title="AI Study Assistant - SNBT/TKA/UKK", layout="wide", initial_sidebar_state="collapsed")

# Inject Custom CSS Ala Kita (Modern, Dark Mode, Minimalist)
st.markdown('''
<style>
    :root {
        --primary-bg: #0b0f19;
        --card-bg: #151a28;
        --accent-blue: #3b82f6;
        --text-main: #f1f5f9;
        --text-muted: #94a3b8;
        --border-color: #2e3c54;
    }
    
    .stApp {
        background-color: var(--primary-bg);
        color: var(--text-main);
    }
    
    /* Card Styling */
    .dashboard-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    .dashboard-card:hover {
        transform: translateY(-2px);
    }
    
    /* Typography */
    .card-title {
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: #ffffff;
    }
    .card-subtitle {
        font-size: 0.9rem;
        color: var(--text-muted);
        margin-bottom: 20px;
    }
    
    /* Metrics/Scores */
    .score-circle {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 8px solid var(--accent-blue);
        font-size: 2rem;
        font-weight: bold;
        color: white;
        margin: 0 auto;
    }
    
    /* Flashcard */
    .flashcard {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-align: center;
    }
    .flashcard-title {
        color: var(--accent-blue);
        font-size: 0.85rem;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 12px;
    }
    .flashcard-content {
        font-size: 1.1rem;
        font-weight: 500;
    }
    
    /* Custom button overrides */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: scale(1.02);
    }
</style>
''', unsafe_allow_html=True)

# System Kode Akses Security
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="dashboard-card" style="max-width: 500px; margin: 100px auto; text-align: center;">', unsafe_allow_html=True)
    st.title("🔒 Portal Ujian Terpadu")
    st.write("Masukkan kode akses rahasia untuk masuk.")
    passcode = st.text_input("Kode Akses", type="password", placeholder="******", label_visibility="collapsed")
    if st.button("Akses Sistem", type="primary", use_container_width=True):
        if passcode == "060407":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Akses Ditolak!")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Inisialisasi Session State
if "history" not in st.session_state:
    st.session_state.history = [] # Format: {"mapel": "RPL", "score": 85, "date": "..."}
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []

# Navigasi ala Dashboard
st.markdown("<h2>🎓 MYSARPRASS Learning Terminal</h2>", unsafe_allow_html=True)

menu = st.sidebar.radio("Navigasi", ["🏠 Dashboard Utama", "📝 Mulai Simulasi", "📚 Generator Materi", "⚙️ Pengaturan API"])

# Cek API Key
api_key = ""
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.session_state.get("manual_api_key", "")

if api_key:
    genai.configure(api_key=api_key)

# ----------------- HALAMAN PENGATURAN -----------------
if menu == "⚙️ Pengaturan API":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Koneksi Sistem AI</div>', unsafe_allow_html=True)
    if "GEMINI_API_KEY" in st.secrets:
        st.success("Sistem telah terhubung otomatis ke Gemini AI melalui sistem rahasia.")
    else:
        new_key = st.text_input("Masukkan Gemini API Key:", type="password", value=st.session_state.get("manual_api_key", ""))
        if st.button("Simpan Kunci API"):
            st.session_state.manual_api_key = new_key
            st.success("API Key disimpan sementara di sesi ini.")
    
    if st.button("🔒 Keluar / Lock App"):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- HALAMAN DASHBOARD -----------------
elif menu == "🏠 Dashboard Utama":
    
    # Bagian Atas: Radar Kesiapan & Riwayat Ringkas
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="dashboard-card" style="text-align: center; height: 100%;">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Radar Kesiapanmu</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-subtitle">Rata-rata skor dari seluruh simulasi</div>', unsafe_allow_html=True)
        
        if len(st.session_state.history) > 0:
            avg_score = sum([x['score'] for x in st.session_state.history]) / len(st.session_state.history)
            st.markdown(f'<div class="score-circle">{int(avg_score)}</div>', unsafe_allow_html=True)
            st.progress(int(avg_score)/100)
            st.caption("Menuju Target Aman (SNBT/UKK)")
        else:
            st.markdown(f'<div class="score-circle">0</div>', unsafe_allow_html=True)
            st.caption("Belum ada data. Mulai simulasi untuk menghitung!")
            
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="dashboard-card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Aktivitas Terbaru</div>', unsafe_allow_html=True)
        
        if not st.session_state.history:
            st.info("Kamu belum menyelesaikan latihan apapun hari ini.")
        else:
            for item in reversed(st.session_state.history[-4:]): # Ambil 4 terakhir
                color = "green" if item['score'] >= 70 else "red"
                st.markdown(f'''
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding: 12px 0;">
                    <div>
                        <strong>{item['mapel']}</strong><br>
                        <span style="font-size: 0.8rem; color: var(--text-muted);">{item['date']}</span>
                    </div>
                    <div style="font-weight: bold; font-size: 1.2rem; color: {color};">
                        {item['score']} / 100
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Bagian Bawah: Flashcard Cepat
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Flashcard Belajarmu</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-subtitle">Ketik topik materi (Contoh: "Jaringan Komputer", "Matriks", "Fotosintesis") lalu AI akan membuatkan intisarinya.</div>', unsafe_allow_html=True)
    
    fc_col1, fc_col2 = st.columns([3, 1])
    with fc_col1:
        topic = st.text_input("Materi / Topik", placeholder="Ketik topik di sini...", label_visibility="collapsed")
    with fc_col2:
        if st.button("Buat Flashcard", type="primary", use_container_width=True) and topic and api_key:
            with st.spinner("Meracik inti materi..."):
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    prompt = f"Buatkan 3 kartu hafalan (flashcard) singkat tentang '{topic}'. Format JSON murni: [{{'subtopik': '...', 'isi': '...'}}]"
                    res = model.generate_content(prompt)
                    json_str = res.text.replace("```json", "").replace("```", "").strip()
                    cards = json.loads(json_str)
                    st.session_state.flashcards = cards
                except:
                    st.error("Gagal membuat flashcard. Coba lagi.")
    
    if st.session_state.flashcards:
        cols = st.columns(len(st.session_state.flashcards))
        for idx, card in enumerate(st.session_state.flashcards):
            with cols[idx]:
                st.markdown(f'''
                <div class="flashcard">
                    <div class="flashcard-title">{card.get('subtopik', 'Fakta')}</div>
                    <div class="flashcard-content">{card.get('isi', '-')}</div>
                </div>
                ''', unsafe_allow_html=True)
                
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- HALAMAN SIMULASI -----------------
elif menu == "📝 Mulai Simulasi":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Konfigurasi Simulasi (Siap dalam 10 Detik)</div>', unsafe_allow_html=True)
    
    # Pilihan Preset atau Upload
    sumber = st.radio("Sumber Soal:", ["📚 Jalur Standar (Bank Soal AI)", "📄 Upload Modul Sendiri (PDF)"], horizontal=True)
    
    materi_text = ""
    mapel_name = ""
    
    if sumber == "📚 Jalur Standar (Bank Soal AI)":
        mapel_name = st.selectbox("Pilih Jalur Target", [
            "Penalaran Matematika", 
            "Literasi Bahasa Indonesia", 
            "Literasi Bahasa Inggris", 
            "Konsentrasi Keahlian RPL (Rekayasa Perangkat Lunak)",
            "Pengetahuan Kuantitatif"
        ])
        materi_text = f"Buatkan soal setingkat ujian nasional (SNBT/UKK) untuk mata pelajaran: {mapel_name}. Pastikan soal berbobot dan menantang."
    else:
        uploaded_file = st.file_uploader("Upload Modul PDF", type="pdf")
        if uploaded_file:
            mapel_name = uploaded_file.name
            with st.spinner("Mengekstrak PDF..."):
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    materi_text += page.extract_text() + "\n"
                st.success("PDF siap digunakan!")
    
    # Pengaturan jumlah dan waktu
    cfg_col1, cfg_col2 = st.columns(2)
    with cfg_col1:
        jumlah_soal = st.select_slider("Jumlah Soal", options=[5, 10, 15, 20, 30, 45], value=10)
    with cfg_col2:
        waktu_menit = st.select_slider("Durasi (Menit)", options=[10, 20, 30, 60, 90, 120], value=20)
        
    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    
    if st.button("🚀 Mulai Simulasi Sekarang", type="primary", use_container_width=True):
        if not api_key:
            st.error("API Key belum diatur!")
        elif not materi_text:
            st.warning("Pilih materi atau upload PDF terlebih dahulu.")
        else:
            with st.spinner("Mengacak bank soal..."):
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    prompt = f'''
                    Berdasarkan acuan berikut, buatkan {jumlah_soal} soal ujian berstandar HOTS (Higher Order Thinking Skills).
                    Acuan/Materi: {materi_text[:10000]}
                    
                    Format JSON murni (tanpa markdown):
                    [
                        {{
                            "pertanyaan": "...",
                            "opsi": ["A. ...", "B. ...", "C. ...", "D. ...", "E. ..."],
                            "jawaban_benar": "A. ...",
                            "penjelasan": "..."
                        }}
                    ]
                    '''
                    res = model.generate_content(prompt)
                    json_str = res.text.replace("```json", "").replace("```", "").strip()
                    st.session_state.quiz_data_v2 = json.loads(json_str)
                    st.session_state.quiz_mapel = mapel_name
                    st.session_state.start_time_v2 = time.time()
                    st.session_state.quiz_waktu = waktu_menit
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                    st.success("Siap! Gulir ke bawah untuk mengerjakan.")
                except Exception as e:
                    st.error(f"Gagal memuat soal. Server sibuk. Silakan coba lagi. Detail: {e}")
                    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Area Pengerjaan Soal
    if st.session_state.get("quiz_data_v2"):
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown(f"### 📝 Lembar Jawaban: {st.session_state.quiz_mapel}")
        
        waktu_sisa = st.session_state.quiz_waktu - ((time.time() - st.session_state.start_time_v2) / 60)
        st.info(f"⏳ Target Waktu: {st.session_state.quiz_waktu} Menit (Kerjakan dengan teliti)")
        
        for i, q in enumerate(st.session_state.quiz_data_v2):
            st.markdown(f"**{i+1}. {q['pertanyaan']}**")
            
            user_choice = st.radio("Opsi:", q['opsi'], key=f"qz_{i}", index=None, disabled=st.session_state.quiz_submitted)
            st.session_state.quiz_answers[i] = user_choice
            
            if st.session_state.quiz_submitted:
                if user_choice == q['jawaban_benar']:
                    st.success("✅ Benar!")
                    st.caption(f"**Pembahasan:** {q['penjelasan']}")
                else:
                    st.error(f"❌ Salah. Kunci: {q['jawaban_benar']}")
                    st.caption(f"**Pembahasan:** {q['penjelasan']}")
            
            st.markdown("<hr style='border-color: var(--border-color); border-style: dashed;'>", unsafe_allow_html=True)
            
        if not st.session_state.quiz_submitted:
            if st.button("Kumpulkan & Cek Nilai", type="primary"):
                st.session_state.quiz_submitted = True
                
                # Hitung Nilai
                score = 0
                for i, q in enumerate(st.session_state.quiz_data_v2):
                    if st.session_state.quiz_answers.get(i) == q['jawaban_benar']:
                        score += 1
                        
                nilai_akhir = int((score / len(st.session_state.quiz_data_v2)) * 100)
                
                # Simpan Riwayat
                import datetime
                now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
                st.session_state.history.append({
                    "mapel": st.session_state.quiz_mapel,
                    "score": nilai_akhir,
                    "date": now
                })
                
                st.rerun()
        else:
            score = sum(1 for i, q in enumerate(st.session_state.quiz_data_v2) if st.session_state.quiz_answers.get(i) == q['jawaban_benar'])
            nilai_akhir = int((score / len(st.session_state.quiz_data_v2)) * 100)
            
            st.markdown(f'<div class="score-circle" style="margin-bottom: 20px;">{nilai_akhir}</div>', unsafe_allow_html=True)
            if nilai_akhir >= 70:
                st.balloons()
            
            if st.button("Selesai & Kembali ke Dashboard"):
                st.session_state.quiz_data_v2 = None
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- HALAMAN GENERATOR MATERI -----------------
elif menu == "📚 Generator Materi":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Generator Modul & Rangkuman AI</div>', unsafe_allow_html=True)
    st.write("Ubah Video YouTube atau File PDF menjadi catatan belajar interaktif.")
    
    jenis = st.radio("Pilih Mode:", ["🎥 Rangkum Video YouTube", "📄 Rangkum File PDF"], horizontal=True)
    
    if jenis == "🎥 Rangkum Video YouTube":
        yt_url = st.text_input("Link YouTube", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("Proses Video", type="primary"):
            if not api_key: st.error("API Key belum diatur!")
            elif yt_url:
                with st.spinner("AI menganalisis video..."):
                    try:
                        model = genai.GenerativeModel('gemini-3.6-flash')
                        res = model.generate_content(f"Buatkan ringkasan struktur, materi penting, dan rumus/konsep dari video ini: {yt_url}")
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(res.text)
                    except:
                        st.error("Gagal menganalisis video.")
    else:
        pdf_file = st.file_uploader("Upload PDF", type="pdf")
        if st.button("Rangkum PDF", type="primary"):
            if not api_key: st.error("API Key belum diatur!")
            elif pdf_file:
                with st.spinner("AI membaca dan merangkum PDF..."):
                    try:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        text = ""
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        res = model.generate_content(f"Rangkum materi ini secara terstruktur agar mudah dipelajari untuk ujian:\n\n{text[:15000]}")
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(res.text)
                    except:
                        st.error("Gagal merangkum dokumen.")
                        
    st.markdown('</div>', unsafe_allow_html=True)
