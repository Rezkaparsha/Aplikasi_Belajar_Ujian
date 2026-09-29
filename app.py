import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import os
import time
import datetime

# Konfigurasi Halaman & Tema ala Pelajaran.ai
st.set_page_config(page_title="Pelajaran AI - Learning Assistant", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS ala Pelajaran.ai (Modern Dark Theme & Elegant Cards)
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
        width: 110px; height: 110px; border-radius: 50%;
        border: 6px solid var(--accent-blue); font-size: 1.8rem; font-weight: bold; color: white; margin: 0 auto;
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

# System Kode Akses Security (PIN: 060407)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="dashboard-card" style="max-width: 450px; margin: 80px auto; text-align: center;">', unsafe_allow_html=True)
    st.title("🔒 Pelajaran.ai Terminal")
    st.write("Masukkan kode akses rahasia untuk melanjutkan:")
    passcode = st.text_input("Kode Akses", type="password", placeholder="******", label_visibility="collapsed")
    if st.button("Masuk ke Aplikasi", type="primary", use_container_width=True):
        if passcode == "060407":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Kode Akses Salah!")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Inisialisasi State
if "history" not in st.session_state:
    st.session_state.history = load_history()
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "review_item" not in st.session_state:
    st.session_state.review_item = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Cek API Key dari Secrets atau Sidebar
api_key = st.secrets.get("GEMINI_API_KEY", st.session_state.get("manual_api_key", ""))
if api_key:
    genai.configure(api_key=api_key)

# Header Utama
st.markdown("<h2>🚀 Pelajaran.ai - Smart Learning Terminal</h2>", unsafe_allow_html=True)

# Sidebar Navigasi & Pengaturan
with st.sidebar:
    st.header("⚙️ Navigasi & Akun")
    menu = st.radio("Menu Utama", ["🏠 Dashboard Utama", "💬 Chatbot AI Pelajaran", "📝 Simulasi Ujian", "📚 Generator Materi", "🔑 Pengaturan API"])
    
    st.markdown("---")
    if not api_key:
        st.warning("⚠️ API Key belum terhubung.")
    else:
        st.success("✅ AI Engine Siap")
        
    if st.button("🔒 Keluar / Lock"):
        st.session_state.authenticated = False
        st.rerun()

# ----------------- HALAMAN PENGATURAN API -----------------
if menu == "🔑 Pengaturan API":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Koneksi Google Gemini API</div>', unsafe_allow_html=True)
    if "GEMINI_API_KEY" in st.secrets:
        st.success("API Key sudah tersimpan di Streamlit Secrets.")
    else:
        new_key = st.text_input("Masukkan Gemini API Key:", type="password", value=st.session_state.get("manual_api_key", ""))
        if st.button("Simpan Key"):
            st.session_state.manual_api_key = new_key
            st.success("API Key berhasil disimpan di sesi ini.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- HALAMAN DASHBOARD UTAMA -----------------
elif menu == "🏠 Dashboard Utama":
    if st.session_state.review_item is not None:
        item = st.session_state.review_item
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        if st.button("⬅️ Kembali ke Dashboard"):
            st.session_state.review_item = None
            st.rerun()
            
        st.markdown(f"### 📖 Arsip Review: {item['mapel']}")
        st.caption(f"Tanggal: {item['date']} | Skor Akhir: {item['score']}/100")
        st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
        
        for idx, q in enumerate(item.get('soal', [])):
            st.markdown(f"**{idx+1}. {q.get('pertanyaan')}**")
            st.markdown(f"💡 **Jawaban Benar:** `{q.get('jawaban_benar')}`")
            st.markdown(f"📝 **Pembahasan:** {q.get('penjelasan')}")
            st.markdown("<hr style='border-color: var(--border-color); border-style: dashed;'>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<div class="dashboard-card" style="text-align: center; height: 100%;">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Radar Kesiapan</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-subtitle">Rata-rata Skor Latihan</div>', unsafe_allow_html=True)
            
            history_data = st.session_state.history
            if len(history_data) > 0:
                avg_score = sum([x['score'] for x in history_data]) / len(history_data)
                st.markdown(f'<div class="score-circle">{int(avg_score)}</div>', unsafe_allow_html=True)
                st.progress(int(avg_score)/100)
                st.caption("Performa Perjalanan Belajarmu")
            else:
                st.markdown(f'<div class="score-circle">0</div>', unsafe_allow_html=True)
                st.caption("Selesaikan simulasi pertama untuk menghitung skor.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="dashboard-card" style="height: 100%;">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Riwayat Tryout (Tersimpan)</div>', unsafe_allow_html=True)
            
            history_data = st.session_state.history
            if not history_data:
                st.info("Belum ada riwayat simulasi yang tersimpan.")
            else:
                for idx, item in enumerate(reversed(history_data)):
                    col_h1, col_h2 = st.columns([3, 1])
                    with col_h1:
                        st.markdown(f"**{item['mapel']}**<br><span style='font-size: 0.8rem; color: var(--text-muted);'>{item['date']} (Skor: {item['score']}/100)</span>", unsafe_allow_html=True)
                    with col_h2:
                        if st.button("🔍 Detail", key=f"rev_{idx}"):
                            st.session_state.review_item = item
                            st.rerun()
                    st.markdown("<hr style='border-color: var(--border-color); margin: 6px 0;'>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Flashcard Generator
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">AI Flashcard Generator</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-subtitle">Ketik topik materi (Contoh: "Algoritma Pemrograman", "Sistem Ekskresi") untuk membuat kartu hafalan cepat.</div>', unsafe_allow_html=True)
        
        fc_col1, fc_col2 = st.columns([3, 1])
        with fc_col1:
            topic = st.text_input("Topik Materi", placeholder="Ketik topik di sini...", label_visibility="collapsed")
        with fc_col2:
            if st.button("Buat Flashcards", type="primary", use_container_width=True) and topic and api_key:
                with st.spinner("Meracik poin hafalan..."):
                    try:
                        model = genai.GenerativeModel('gemini-3.6-flash')
                        prompt = f"Buatkan 3 kartu hafalan (flashcard) singkat tentang '{topic}'. Format JSON murni tanpa markdown: [{{'subtopik': '...', 'isi': '...'}}]"
                        res = model.generate_content(prompt)
                        json_str = res.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.flashcards = json.loads(json_str, strict=False)
                    except Exception as e:
                        st.error(f"Gagal membuat flashcard (Coba lagi dalam beberapa detik): {e}")
        
        if st.session_state.flashcards:
            cols = st.columns(len(st.session_state.flashcards))
            for idx, card in enumerate(st.session_state.flashcards):
                with cols[idx]:
                    st.markdown(f'''
                    <div class="flashcard">
                        <div style="color:#2f81f7; font-weight:bold; font-size:0.9rem;">{card.get('subtopik', 'Inti Materi')}</div>
                        <div style="margin-top:8px; font-size:1rem;">{card.get('isi', '-')}</div>
                    </div>
                    ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- HALAMAN CHATBOT AI PELAJARAN -----------------
elif menu == "💬 Chatbot AI Pelajaran":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🤖 Asisten Belajar Pelajaran.ai</div>', unsafe_allow_html=True)
    st.write("Tanyakan soal sulit, rumus, penjelasan teori, atau saran strategi belajar.")
    
    # Tampilkan riwayat chat
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input Chat
    if prompt := st.chat_input("Tanyakan sesuatu (misal: 'Jelaskan cara kerja percabangan if-else di Python')..."):
        if not api_key:
            st.error("Silakan atur API Key terlebih dahulu.")
        else:
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Pelajaran.ai sedang berpikir..."):
                    try:
                        model = genai.GenerativeModel('gemini-3.6-flash')
                        res = model.generate_content(prompt)
                        st.markdown(res.text)
                        st.session_state.chat_messages.append({"role": "assistant", "content": res.text})
                    except Exception as e:
                        st.error(f"Gagal memproses pesan: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- HALAMAN SIMULASI UJIAN -----------------
elif menu == "📝 Simulasi Ujian":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Pengaturan Simulasi Ujian</div>', unsafe_allow_html=True)
    
    sumber = st.radio("Sumber Materi:", ["📚 Jalur Standar (Bank Soal AI)", "📄 Upload Modul PDF Sendiri"], horizontal=True)
    materi_text, mapel_name = "", ""
    
    if sumber == "📚 Jalur Standar (Bank Soal AI)":
        mapel_name = st.selectbox("Pilih Mata Pelajaran Target", [
            "Penalaran Matematika", "Literasi Bahasa Indonesia", 
            "Literasi Bahasa Inggris", "Konsentrasi Keahlian RPL", "Pengetahuan Kuantitatif"
        ])
        materi_text = f"Buatkan soal ujian berstandar HOTS untuk mata pelajaran: {mapel_name}."
    else:
        uploaded_file = st.file_uploader("Upload File PDF Materi", type="pdf")
        if uploaded_file:
            mapel_name = uploaded_file.name
            with st.spinner("Mengekstrak isi dokumen PDF..."):
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    materi_text += page.extract_text() + "\n"
                st.success("File PDF siap diproses AI!")
    
    cfg_col1, cfg_col2 = st.columns(2)
    with cfg_col1:
        jumlah_soal = st.select_slider("Jumlah Soal", options=[5, 10, 15, 20, 30, 45], value=10)
    with cfg_col2:
        waktu_menit = st.select_slider("Durasi Waktu (Menit)", options=[10, 20, 30, 60, 90, 120], value=20)
        
    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    
    if st.button("🚀 Mulai Simulasi Ujian", type="primary", use_container_width=True):
        if not api_key:
            st.error("API Key belum terpasang!")
        elif not materi_text:
            st.warning("Silakan pilih mata pelajaran atau upload PDF terlebih dahulu.")
        else:
            with st.spinner("Menyusun paket soal..."):
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    prompt = f'''
                    Buatkan {jumlah_soal} soal ujian berstandar HOTS berdasarkan acuan materi berikut.
                    Variasikan tipe soal: ada pilihan ganda biasa (1 jawaban benar) dan pilihan ganda kompleks (jawaban benar lebih dari 1).
                    Acuan: {materi_text[:10000]}
                    
                    Kembalikan HANYA format JSON murni:
                    [
                        {{
                            "pertanyaan": "...",
                            "tipe": "tunggal", 
                            "opsi": ["A. ...", "B. ...", "C. ...", "D. ...", "E. ..."],
                            "jawaban_benar": "A. ...",
                            "penjelasan": "..."
                        }},
                        {{
                            "pertanyaan": "...",
                            "tipe": "kompleks", 
                            "opsi": ["Opsi 1", "Opsi 2", "Opsi 3", "Opsi 4"],
                            "jawaban_benar": ["Opsi 1", "Opsi 3"],
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
                    st.success("Soal berhasil dibuat! Kerjakan lembar jawaban di bawah ini.")
                except Exception as e:
                    st.error(f"Gagal memuat soal: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Area Lembar Jawaban
    if st.session_state.get("quiz_data_v2"):
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown(f"### 📝 Lembar Jawaban Simulasi: {st.session_state.quiz_mapel}")
        
        for i, q in enumerate(st.session_state.quiz_data_v2):
            st.markdown(f"**{i+1}. {q.get('pertanyaan')}**")
            
            is_complex = q.get('tipe') == 'kompleks' or isinstance(q.get('jawaban_benar'), list)
            
            if is_complex:
                st.caption("ℹ️ *Soal Pilihan Ganda Kompleks (Bisa pilih lebih dari 1 jawaban).*")
                selected_multi = []
                for opt in q['opsi']:
                    chk = st.checkbox(opt, key=f"qz_comp_{i}_{opt}", disabled=st.session_state.quiz_submitted)
                    if chk:
                        selected_multi.append(opt)
                st.session_state.quiz_answers[i] = selected_multi
            else:
                user_choice = st.radio("Pilih jawaban:", q['opsi'], key=f"qz_{i}", index=None, disabled=st.session_state.quiz_submitted)
                st.session_state.quiz_answers[i] = user_choice
            
            if st.session_state.quiz_submitted:
                ans_user = st.session_state.quiz_answers.get(i)
                ans_true = q['jawaban_benar']
                
                if is_complex:
                    is_ok = sorted(ans_user if isinstance(ans_user, list) else []) == sorted(ans_true if isinstance(ans_true, list) else [ans_true])
                else:
                    is_ok = (ans_user == ans_true)
                    
                if is_ok:
                    st.success("✅ Jawaban Benar!")
                else:
                    st.error(f"❌ Jawaban Salah. Kunci: {ans_true}")
                st.caption(f"**Pembahasan:** {q['penjelasan']}")
                
            st.markdown("<hr style='border-color: var(--border-color); border-style: dashed;'>", unsafe_allow_html=True)
            
        if not st.session_state.quiz_submitted:
            if st.button("Kumpulkan & Simpan Hasil", type="primary"):
                st.session_state.quiz_submitted = True
                
                score = 0
                total_q = len(st.session_state.quiz_data_v2)
                for i, q in enumerate(st.session_state.quiz_data_v2):
                    ans_user = st.session_state.quiz_answers.get(i)
                    ans_true = q['jawaban_benar']
                    is_complex = q.get('tipe') == 'kompleks' or isinstance(ans_true, list)
                    
                    if is_complex:
                        if sorted(ans_user if isinstance(ans_user, list) else []) == sorted(ans_true if isinstance(ans_true, list) else [ans_true]):
                            score += 1
                    else:
                        if ans_user == ans_true:
                            score += 1
                            
                nilai_akhir = int((score / total_q) * 100)
                now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
                
                new_record = {
                    "mapel": st.session_state.quiz_mapel,
                    "score": nilai_akhir,
                    "date": now,
                    "soal": st.session_state.quiz_data_v2
                }
                st.session_state.history.append(new_record)
                save_history(st.session_state.history)
                st.rerun()
        else:
            if st.button("Selesai & Kembali"):
                st.session_state.quiz_data_v2 = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- HALAMAN GENERATOR MATERI -----------------
elif menu == "📚 Generator Materi":
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">AI Modul & Rangkuman Generator</div>', unsafe_allow_html=True)
    
    jenis = st.radio("Pilih Sumber Rangkuman:", ["🎥 Video YouTube", "📄 File PDF"], horizontal=True)
    
    if jenis == "🎥 Video YouTube":
        yt_url = st.text_input("Link Video YouTube", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("Rangkum Video", type="primary") and yt_url and api_key:
            with st.spinner("AI sedang merangkum isi video..."):
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    res = model.generate_content(f"Buatkan ringkasan poin-poin materi penting dan konsep kunci dari video ini: {yt_url}")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Gagal merangkum video: {e}")
    else:
        pdf_file = st.file_uploader("Upload Dokumen PDF", type="pdf")
        if st.button("Rangkum PDF", type="primary") and pdf_file and api_key:
            with st.spinner("AI sedang membaca PDF..."):
                try:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = "".join([page.extract_text() for page in pdf_reader.pages])
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    res = model.generate_content(f"Rangkum materi ini secara ringkas, terstruktur, dan mudah dipahami:\n\n{text[:15000]}")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Gagal merangkum PDF: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
