import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import os
import time
import datetime

# Konfigurasi Halaman & Tema ala Dashboard Modern
st.set_page_config(
    page_title="SNBTMaster - Smart Learning Terminal", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan ala Dashboard / Pelajaran.ai
st.markdown('''
<style>
    :root {
        --primary-bg: #0d1117;
        --card-bg: #161b22;
        --accent-blue: #2f81f7;
        --accent-green: #238636;
        --text-main: #c9d1d9;
        --text-muted: #8b949e;
        --border-color: #30363d;
    }
    .stApp { background-color: var(--primary-bg); color: var(--text-main); }
    .dashboard-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }
    .card-title { font-size: 1.2rem; font-weight: 700; color: #ffffff; margin-bottom: 6px; }
    .card-subtitle { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 16px; }
    .score-circle {
        display: flex; align-items: center; justify-content: center;
        width: 120px; height: 120px; border-radius: 50%;
        border: 6px solid var(--accent-blue); font-size: 2rem; font-weight: bold; color: white; margin: 0 auto;
    }
    .flashcard {
        background: #21262d;
        border: 1px solid var(--border-color); border-radius: 10px; padding: 16px; min-height: 130px;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
    }
    .stButton>button { border-radius: 8px; font-weight: 600; }
</style>
''', unsafe_allow_html=True)

# Sistem Penyimpanan Data Lokal Permanen
HISTORY_FILE = "history_data.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history_data):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=4)
    except:
        pass

# Security Pin
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="dashboard-card" style="max-width: 450px; margin: 80px auto; text-align: center;">', unsafe_allow_html=True)
    st.title("🔒 SNBTMaster Terminal")
    st.write("Masukkan PIN Akses untuk melanjutkan:")
    passcode = st.text_input("PIN Akses", type="password", placeholder="******", label_visibility="collapsed")
    if st.button("Masuk ke Aplikasi", type="primary", use_container_width=True):
        if passcode == "060407":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("PIN Akses Salah!")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Inisialisasi Session States
if "history" not in st.session_state:
    st.session_state.history = load_history()
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "review_item" not in st.session_state:
    st.session_state.review_item = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Cek API Key
api_key = st.secrets.get("GEMINI_API_KEY", st.session_state.get("manual_api_key", ""))
if api_key:
    genai.configure(api_key=api_key)

st.markdown("<h2>🧠 SNBTMaster - AI Learning Terminal</h2>", unsafe_allow_html=True)

# Sidebar Navigasi
with st.sidebar:
    st.header("⚙️ Navigasi")
    menu = st.radio("Menu Utama", ["🏠 Dashboard", "📝 Simulasi Baru (CBT)", "💬 AI Tutor Chatbot", "📚 Flashcards", "🔑 Pengaturan API"])
    st.markdown("---")
    if not api_key:
        st.warning("⚠️ API Key Belum Terhubung")
    else:
        st.success("✅ AI Engine Ready")
    if st.button("🔒 Keluar"):
        st.session_state.authenticated = False
        st.rerun()

# ----------------- 1. PENGATURAN API -----------------
if menu == "🔑 Pengaturan API":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Pengaturan API Key</div>', unsafe_allow_html=True)
    if "GEMINI_API_KEY" in st.secrets:
        st.success("API Key terhubung otomatis dari Secrets.")
    else:
        new_key = st.text_input("Masukkan Gemini API Key:", type="password", value=st.session_state.get("manual_api_key", ""))
        if st.button("Simpan Key"):
            st.session_state.manual_api_key = new_key
            st.success("API Key tersimpan!")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- 2. DASHBOARD UTAMA -----------------
elif menu == "🏠 Dashboard":
    if st.session_state.review_item is not None:
        item = st.session_state.review_item
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        if st.button("⬅️ Kembali ke Dashboard"):
            st.session_state.review_item = None
            st.rerun()
            
        st.markdown(f"### 📖 Pembahasan Ujian: {item['mapel']}")
        st.caption(f"Tanggal: {item['date']} | Skor IRT: {item['score']}/1000")
        st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
        
        for idx, q in enumerate(item.get('soal', [])):
            st.markdown(f"**Soal {idx+1}: {q.get('pertanyaan')}**")
            st.markdown(f"💡 **Jawaban Benar:** `{q.get('jawaban_benar')}`")
            st.markdown(f"📝 **Pembahasan:** {q.get('penjelasan')}")
            st.markdown("<hr style='border-color: var(--border-color); border-style: dashed;'>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<div class="dashboard-card" style="text-align: center; height: 100%;">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Rata-rata Skor IRT</div>', unsafe_allow_html=True)
            
            history_data = st.session_state.history
            if len(history_data) > 0:
                avg_score = sum([x['score'] for x in history_data]) / len(history_data)
                st.markdown(f'<div class="score-circle">{int(avg_score)}</div>', unsafe_allow_html=True)
                st.progress(min(1.0, avg_score/1000))
                st.caption("Target Skor Aman SNBT/PTN")
            else:
                st.markdown(f'<div class="score-circle">0</div>', unsafe_allow_html=True)
                st.caption("Mulai simulasi untuk melihat skor IRT.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="dashboard-card" style="height: 100%;">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Riwayat Simulasi Ujian</div>', unsafe_allow_html=True)
            
            history_data = st.session_state.history
            if not history_data:
                st.info("Belum ada data pengerjaan ujian.")
            else:
                for idx, item in enumerate(reversed(history_data)):
                    col_h1, col_h2 = st.columns([3, 1])
                    with col_h1:
                        st.markdown(f"**{item['mapel']}**<br><span style='font-size: 0.8rem; color: var(--text-muted);'>{item['date']} (Skor IRT: {item['score']})</span>", unsafe_allow_html=True)
                    with col_h2:
                        if st.button("🔍 Review", key=f"rev_{idx}"):
                            st.session_state.review_item = item
                            st.rerun()
                    st.markdown("<hr style='border-color: var(--border-color); margin: 6px 0;'>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ----------------- 3. SIMULASI UJIAN (CBT) -----------------
elif menu == "📝 Simulasi Baru (CBT)":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Konfigurasi Simulasi Ujian Custom</div>', unsafe_allow_html=True)
    
    sumber = st.radio("Sumber Bank Soal:", ["📚 Bank Soal Standar SNBT", "📄 Upload PDF Modul/Soal"], horizontal=True)
    materi_text, mapel_name = "", ""
    
    if sumber == "📚 Bank Soal Standar SNBT":
        mapel_name = st.selectbox("Pilih Subtes", [
            "Penalaran Matematika", "Literasi Bahasa Indonesia", 
            "Literasi Bahasa Inggris", "Pemrograman Dasar / RPL", "Pengetahuan Kuantitatif"
        ])
        materi_text = f"Buatkan paket soal ujian HOTS untuk subtes: {mapel_name}."
    else:
        uploaded_file = st.file_uploader("Upload File PDF Bank Soal", type="pdf")
        if uploaded_file:
            mapel_name = uploaded_file.name
            with st.spinner("Mengekstrak teks PDF..."):
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    materi_text += page.extract_text() + "\n"
                st.success("PDF Berhasil Dibuat!")
    
    cfg_col1, cfg_col2 = st.columns(2)
    with cfg_col1:
        jumlah_soal = st.select_slider("Jumlah Soal", options=[5, 10, 15, 20, 30, 45], value=10)
    with cfg_col2:
        waktu_menit = st.select_slider("Durasi Ujian (Menit)", options=[10, 20, 30, 60, 90, 120], value=20)
        
    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    
    if st.button("🚀 Buat & Mulai Ujian", type="primary", use_container_width=True):
        if not api_key:
            st.error("API Key belum terhubung!")
        elif not materi_text:
            st.warning("Pilih mata pelajaran atau upload PDF terlebih dahulu.")
        else:
            with st.spinner("AI sedang meracik paket soal..."):
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    prompt = f'''
                    Buatkan {jumlah_soal} soal ujian berstandar HOTS berdasarkan materi berikut.
                    Materi: {materi_text[:10000]}
                    
                    Format JSON murni tanpa markdown:
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
                    
                    st.session_state.quiz_data_v2 = json.loads(json_str, strict=False)
                    st.session_state.quiz_mapel = mapel_name
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                    st.success("Soal Siap! Kerjakan di bawah ini.")
                except Exception as e:
                    st.error(f"Gagal memuat soal: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Engine Lembar Jawaban CBT
    if st.session_state.get("quiz_data_v2"):
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown(f"### 📝 CBT Engine: {st.session_state.quiz_mapel}")
        
        for i, q in enumerate(st.session_state.quiz_data_v2):
            st.markdown(f"**Soal {i+1}. {q.get('pertanyaan')}**")
            
            user_choice = st.radio("Pilihan Jawaban:", q['opsi'], key=f"qz_{i}", index=None, disabled=st.session_state.quiz_submitted)
            st.session_state.quiz_answers[i] = user_choice
            
            if st.session_state.quiz_submitted:
                ans_user = st.session_state.quiz_answers.get(i)
                ans_true = q['jawaban_benar']
                
                if ans_user == ans_true:
                    st.success("✅ Benar!")
                else:
                    st.error(f"❌ Salah. Kunci: {ans_true}")
                st.caption(f"**Pembahasan:** {q['penjelasan']}")
            st.markdown("<hr style='border-color: var(--border-color); border-style: dashed;'>", unsafe_allow_html=True)
            
        if not st.session_state.quiz_submitted:
            if st.button("Kumpulkan & Cek Hasil", type="primary"):
                st.session_state.quiz_submitted = True
                
                score = sum(1 for i, q in enumerate(st.session_state.quiz_data_v2) if st.session_state.quiz_answers.get(i) == q['jawaban_benar'])
                total_q = len(st.session_state.quiz_data_v2)
                
                # Kalkulasi Skor ala IRT (Skala 1000)
                irt_score = int((score / total_q) * 1000)
                now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
                
                new_record = {
                    "mapel": st.session_state.quiz_mapel,
                    "score": irt_score,
                    "date": now,
                    "soal": st.session_state.quiz_data_v2
                }
                st.session_state.history.append(new_record)
                save_history(st.session_state.history)
                st.rerun()
        else:
            if st.button("Selesai & Kembali ke Dashboard"):
                st.session_state.quiz_data_v2 = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- 4. AI TUTOR CHATBOT -----------------
elif menu == "💬 AI Tutor Chatbot":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🤖 AI Tutor Pembelajaran</div>', unsafe_allow_html=True)
    
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Tanyakan soal sulit atau teori pelajaran..."):
        if not api_key:
            st.error("Masukkan API Key terlebih dahulu!")
        else:
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("AI Tutor sedang menjawab..."):
                    try:
                        model = genai.GenerativeModel('gemini-3.6-flash')
                        res = model.generate_content(prompt)
                        st.markdown(res.text)
                        st.session_state.chat_messages.append({"role": "assistant", "content": res.text})
                    except Exception as e:
                        st.error(f"Gagal memproses pesan: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- 5. FLASHCARDS -----------------
elif menu == "📚 Flashcards":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">AI Flashcard Generator</div>', unsafe_allow_html=True)
    
    fc_col1, fc_col2 = st.columns([3, 1])
    with fc_col1:
        topic = st.text_input("Topik Materi Hafalan", placeholder="Contoh: Rumus Turunan, Logika Matematika...")
    with fc_col2:
        if st.button("Buat Kartu", type="primary") and topic and api_key:
            with st.spinner("Membuat kartu hafalan..."):
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    prompt = f"Buatkan 3 kartu hafalan ringkas tentang '{topic}'. Format JSON murni: [{{'subtopik': '...', 'isi': '...'}}]"
                    res = model.generate_content(prompt)
                    json_str = res.text.replace("```json", "").replace("```", "").strip()
                    st.session_state.flashcards = json.loads(json_str, strict=False)
                except Exception as e:
                    st.error(f"Gagal: {e}")
                    
    if st.session_state.flashcards:
        cols = st.columns(len(st.session_state.flashcards))
        for idx, card in enumerate(st.session_state.flashcards):
            with cols[idx]:
                st.markdown(f'''
                <div class="flashcard">
                    <div style="color:#2f81f7; font-weight:bold;">{card.get('subtopik', 'Inti')}</div>
                    <div style="margin-top:8px;">{card.get('isi', '-')}</div>
                </div>
                ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
