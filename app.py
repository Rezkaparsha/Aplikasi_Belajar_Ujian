import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import os
import time
import datetime

# Konfigurasi Halaman & Tema
st.set_page_config(page_title="AI Study Assistant - SNBT/TKA/UKK", layout="wide", initial_sidebar_state="collapsed")

# Inject Custom CSS
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
    .stApp { background-color: var(--primary-bg); color: var(--text-main); }
    .dashboard-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .card-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 8px; color: #ffffff; }
    .card-subtitle { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 20px; }
    .score-circle {
        display: flex; align-items: center; justify-content: center;
        width: 120px; height: 120px; border-radius: 50%;
        border: 8px solid var(--accent-blue); font-size: 2rem; font-weight: bold; color: white; margin: 0 auto;
    }
    .flashcard {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; min-height: 150px;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
    }
    .stButton>button { border-radius: 8px; font-weight: 600; border: none; }
</style>
''', unsafe_allow_html=True)

# Sistem Penyimpanan Data Lokal (Agar tidak hilang saat restart)
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

# Inisialisasi State & Load History Permanen
if "history" not in st.session_state:
    st.session_state.history = load_history()
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []

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
        st.success("Sistem terhubung otomatis ke Gemini AI.")
    else:
        new_key = st.text_input("Masukkan Gemini API Key:", type="password", value=st.session_state.get("manual_api_key", ""))
        if st.button("Simpan Kunci API"):
            st.session_state.manual_api_key = new_key
            st.success("API Key disimpan.")
    
    if st.button("🔒 Keluar / Lock App"):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- HALAMAN DASHBOARD -----------------
elif menu == "🏠 Dashboard Utama":
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="dashboard-card" style="text-align: center; height: 100%;">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Radar Kesiapanmu</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-subtitle">Rata-rata skor dari seluruh simulasi</div>', unsafe_allow_html=True)
        
        history_data = st.session_state.history
        if len(history_data) > 0:
            avg_score = sum([x['score'] for x in history_data]) / len(history_data)
            st.markdown(f'<div class="score-circle">{int(avg_score)}</div>', unsafe_allow_html=True)
            st.progress(int(avg_score)/100)
            st.caption("Menuju Target Aman (SNBT/UKK)")
        else:
            st.markdown(f'<div class="score-circle">0</div>', unsafe_allow_html=True)
            st.caption("Belum ada data. Mulai simulasi untuk menghitung!")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="dashboard-card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Riwayat & Arsip Simulasi (Tersimpan)</div>', unsafe_allow_html=True)
        
        if not history_data:
            st.info("Kamu belum menyelesaikan latihan apapun.")
        else:
            for idx, item in enumerate(reversed(history_data[-5:])):
                color = "green" if item['score'] >= 70 else "red"
                st.markdown(f'''
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding: 10px 0;">
                    <div>
                        <strong>{item['mapel']}</strong><br>
                        <span style="font-size: 0.8rem; color: var(--text-muted);">{item['date']} (Skor: {item['score']}/100)</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Flashcard
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Flashcard Belajarmu</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-subtitle">Ketik topik materi (Contoh: "Jaringan Komputer", "Matriks") lalu AI membuatkan intisarinya.</div>', unsafe_allow_html=True)
    
    fc_col1, fc_col2 = st.columns([3, 1])
    with fc_col1:
        topic = st.text_input("Materi / Topik", placeholder="Ketik topik...", label_visibility="collapsed")
    with fc_col2:
        if st.button("Buat Flashcard", type="primary", use_container_width=True) and topic and api_key:
            with st.spinner("Meracik inti materi..."):
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    prompt = f"Buatkan 3 kartu hafalan (flashcard) singkat tentang '{topic}'. Format JSON murni: [{{'subtopik': '...', 'isi': '...'}}]"
                    res = model.generate_content(prompt)
                    json_str = res.text.replace("```json", "").replace("```", "").strip()
                    st.session_state.flashcards = json.loads(json_str)
                except Exception as e:
                    st.error(f"Gagal: {e}")
    
    if st.session_state.flashcards:
        cols = st.columns(len(st.session_state.flashcards))
        for idx, card in enumerate(st.session_state.flashcards):
            with cols[idx]:
                st.markdown(f'''
                <div class="flashcard">
                    <div class="flashcard-title" style="color:#3b82f6; font-weight:bold;">{card.get('subtopik', 'Fakta')}</div>
                    <div class="flashcard-content" style="margin-top:10px;">{card.get('isi', '-')}</div>
                </div>
                ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- HALAMAN SIMULASI -----------------
elif menu == "📝 Mulai Simulasi":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Konfigurasi Simulasi</div>', unsafe_allow_html=True)
    
    sumber = st.radio("Sumber Soal:", ["📚 Jalur Standar (Bank Soal AI)", "📄 Upload Modul Sendiri (PDF)"], horizontal=True)
    materi_text, mapel_name = "", ""
    
    if sumber == "📚 Jalur Standar (Bank Soal AI)":
        mapel_name = st.selectbox("Pilih Jalur Target", [
            "Penalaran Matematika", "Literasi Bahasa Indonesia", 
            "Literasi Bahasa Inggris", "Konsentrasi Keahlian RPL", "Pengetahuan Kuantitatif"
        ])
        materi_text = f"Buatkan soal setingkat ujian nasional (SNBT/UKK) untuk mapel: {mapel_name}."
    else:
        uploaded_file = st.file_uploader("Upload Modul PDF", type="pdf")
        if uploaded_file:
            mapel_name = uploaded_file.name
            with st.spinner("Mengekstrak PDF..."):
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    materi_text += page.extract_text() + "\n"
                st.success("PDF siap digunakan!")
    
    cfg_col1, cfg_col2 = st.columns(2)
    with cfg_col1:
        jumlah_soal = st.select_slider("Jumlah Soal", options=[5, 10, 15, 20, 30, 45], value=10)
    with cfg_col2:
        waktu_menit = st.select_slider("Durasi (Menit)", options=[10, 20, 30, 60, 90, 120], value=20)
        
    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    
    if st.button("🚀 Mulai Simulasi Sekarang", type="primary", use_container_width=True):
        if not api_key: st.error("API Key belum diatur!")
        elif not materi_text: st.warning("Pilih materi atau upload PDF.")
        else:
            with st.spinner("Mengacak bank soal..."):
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    prompt = f'''
                    Buatkan {jumlah_soal} soal ujian berstandar HOTS berdasarkan acuan berikut.
                    Acuan: {materi_text[:10000]}
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
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                    st.success("Soal siap! Kerjakan di bawah.")
                except Exception as e:
                    st.error(f"Gagal memuat soal: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.get("quiz_data_v2"):
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown(f"### 📝 Lembar Jawaban: {st.session_state.quiz_mapel}")
        
        for i, q in enumerate(st.session_state.quiz_data_v2):
            st.markdown(f"**{i+1}. {q['pertanyaan']}**")
            user_choice = st.radio("Opsi:", q['opsi'], key=f"qz_{i}", index=None, disabled=st.session_state.quiz_submitted)
            st.session_state.quiz_answers[i] = user_choice
            
            if st.session_state.quiz_submitted:
                if user_choice == q['jawaban_benar']:
                    st.success("✅ Benar!")
                else:
                    st.error(f"❌ Salah. Kunci: {q['jawaban_benar']}")
                st.caption(f"**Pembahasan:** {q['penjelasan']}")
            st.markdown("<hr style='border-color: var(--border-color); border-style: dashed;'>", unsafe_allow_html=True)
            
        if not st.session_state.quiz_submitted:
            if st.button("Kumpulkan & Simpan Nilai", type="primary"):
                st.session_state.quiz_submitted = True
                score = sum(1 for i, q in enumerate(st.session_state.quiz_data_v2) if st.session_state.quiz_answers.get(i) == q['jawaban_benar'])
                nilai_akhir = int((score / len(st.session_state.quiz_data_v2)) * 100)
                
                now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
                new_record = {
                    "mapel": st.session_state.quiz_mapel,
                    "score": nilai_akhir,
                    "date": now,
                    "soal": st.session_state.quiz_data_v2
                }
                st.session_state.history.append(new_record)
                save_history(st.session_state.history) # Simpan permanen ke file
                st.rerun()
        else:
            if st.button("Selesai & Kembali ke Dashboard"):
                st.session_state.quiz_data_v2 = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- HALAMAN GENERATOR MATERI -----------------
elif menu == "📚 Generator Materi":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Generator Modul & Rangkuman AI</div>', unsafe_allow_html=True)
    
    jenis = st.radio("Pilih Mode:", ["🎥 Rangkum Video YouTube", "📄 Rangkum File PDF"], horizontal=True)
    
    if jenis == "🎥 Rangkum Video YouTube":
        yt_url = st.text_input("Link YouTube", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("Proses Video", type="primary") and yt_url and api_key:
            with st.spinner("Menganalisis video..."):
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    res = model.generate_content(f"Buatkan ringkasan materi penting dan rumus dari video ini: {yt_url}")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Gagal: {e}")
    else:
        pdf_file = st.file_uploader("Upload PDF", type="pdf")
        if st.button("Rangkum PDF", type="primary") and pdf_file and api_key:
            with st.spinner("Membaca PDF..."):
                try:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = "".join([page.extract_text() for page in pdf_reader.pages])
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    res = model.generate_content(f"Rangkum materi ini secara terstruktur:\n\n{text[:15000]}")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Gagal: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
