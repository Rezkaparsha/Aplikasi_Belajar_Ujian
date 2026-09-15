import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import time

# Konfigurasi Halaman & Tema
st.set_page_config(page_title="AI Study Assistant - SNBT/TKA/UKK/US", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    .question-card { background-color: #1e222d; padding: 20px; border-radius: 12px; border: 1px solid #2e3545; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# System Kode Akses Security
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Akses Terbatas Aplikasi Belajar")
    st.write("Masukkan kode akses rahasia untuk melanjutkan:")
    
    col_acc1, col_acc2 = st.columns([2, 1])
    with col_acc1:
        passcode = st.text_input("Kode Akses", type="password", placeholder="Masukkan 6 digit angka")
    
    if st.button("Masuk ke Aplikasi"):
        if passcode == "060407":
            st.session_state.authenticated = True
            st.success("Kode akses benar! Membuka aplikasi...")
            st.rerun()
        else:
            st.error("Kode akses salah. Kamu tidak memiliki izin akses!")
    st.stop()

# Inisialisasi Session State Baru
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pdf_dict" not in st.session_state:
    st.session_state.pdf_dict = {}  # Menyimpan banyak file sekaligus
if "active_file" not in st.session_state:
    st.session_state.active_file = None  # File yang sedang dipilih
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.title("📚 AI Study Assistant & Tryout Simulator")
st.markdown("Persiapan Ujian: **TKA, UKK, US, & SNBT**")

# Cek API Key dari Streamlit Secrets atau Sidebar
api_key = ""
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

# Sidebar untuk Pengaturan
with st.sidebar:
    st.header("⚙️ Pengaturan")
    
    if api_key:
        st.success("✅ API Key Otomatis Terhubung!")
        genai.configure(api_key=api_key)
    else:
        api_key_input = st.text_input("Masukkan Google Gemini API Key", type="password")
        if api_key_input:
            api_key = api_key_input
            genai.configure(api_key=api_key)
        
    st.header("📄 Upload Materi PDF")
    st.info("Kamu bisa upload banyak file beda mapel sekaligus.")
    uploaded_files = st.file_uploader("Upload file PDF materi", type="pdf", accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Ekstrak Semua PDF"):
            with st.spinner(f"Membaca {len(uploaded_files)} file..."):
                temp_dict = {}
                for file in uploaded_files:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    temp_dict[file.name] = text
                
                st.session_state.pdf_dict = temp_dict
                
                # Otomatis pilih file pertama yang diupload sebagai aktif
                if len(temp_dict) > 0:
                    st.session_state.active_file = list(temp_dict.keys())[0]
                st.success("Semua file berhasil diekstrak!")

    # Fitur Memilih Mapel yang Fokus Dipelajari
    if st.session_state.pdf_dict:
        st.markdown("---")
        st.header("🎯 Pilih Mata Pelajaran")
        
        selected_file = st.selectbox(
            "Materi yang sedang aktif:", 
            list(st.session_state.pdf_dict.keys()), 
            index=list(st.session_state.pdf_dict.keys()).index(st.session_state.active_file) if st.session_state.active_file in st.session_state.pdf_dict else 0
        )
        
        # Jika ganti mapel, reset soal dan chat agar tidak tertukar
        if selected_file != st.session_state.active_file:
            st.session_state.active_file = selected_file
            st.session_state.quiz_data = None
            st.session_state.submitted = False
            st.session_state.user_answers = {}
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("---")
    if st.button("🔒 Keluar / Lock App"):
        st.session_state.authenticated = False
        st.rerun()

# Ambil teks khusus dari file yang sedang dipilih
current_text = ""
if st.session_state.active_file and st.session_state.active_file in st.session_state.pdf_dict:
    current_text = st.session_state.pdf_dict[st.session_state.active_file]

# Main Area (Tabs)
tab1, tab2, tab3, tab4 = st.tabs(["📖 Penjelasan PDF", "🎥 Rangkum YouTube", "📝 Simulasi Ujian", "💬 Chatbot AI"])

# Tab 1: Penjelasan Materi
with tab1:
    st.header(f"Ringkasan Materi: {st.session_state.active_file if st.session_state.active_file else 'Belum ada file'}")
    if current_text and api_key:
        if st.button("Buat Ringkasan Materi Ini"):
            with st.spinner("AI sedang merangkum materi..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"Buatkan penjelasan dan ringkasan komprehensif khusus untuk materi dari file {st.session_state.active_file} berikut:\n\n{current_text[:15000]}"
                response = model.generate_content(prompt)
                st.write(response.text)
    elif not api_key:
        st.warning("Silakan pastikan API Key sudah dimasukkan/tersimpan.")
    else:
        st.info("Silakan upload, ekstrak PDF, dan pilih file di sidebar terlebih dahulu.")

# Tab 2: Rangkum YouTube
with tab2:
    st.header("🎥 Rangkum Video Pembelajaran YouTube")
    st.write("Tempelkan link video YouTube materi pelajaran untuk dirangkum poin pentingnya.")
    
    youtube_url = st.text_input("Link Video YouTube", placeholder="https://www.youtube.com/watch?v=...")
    
    if youtube_url and api_key:
        if st.button("Proses & Rangkum Video"):
            with st.spinner("AI sedang menganalisis konten video YouTube..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Tolong buatkan ringkasan materi pelajaran, poin kunci, serta rumus/contoh soal penting dari video YouTube ini: {youtube_url}"
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Gagal merangkum video. Pastikan link YouTube valid. Detail: {e}")
    elif not api_key:
        st.warning("Silakan pastikan API Key sudah dimasukkan/tersimpan.")

# Tab 3: Simulasi Ujian
with tab3:
    st.header(f"Simulasi Ujian: {st.session_state.active_file if st.session_state.active_file else 'Belum ada file'}")
    
    col1, col2 = st.columns(2)
    with col1:
        jumlah_soal = st.selectbox("Jumlah Soal", [5, 10, 20, 30, 45])
    with col2:
        waktu_menit = st.selectbox("Waktu Pengerjaan (Menit)", [10, 30, 60, 90, 120])
        
    if current_text and api_key:
        if st.button(f"Buat Soal {st.session_state.active_file}"):
            with st.spinner(f"AI sedang menyusun soal dari {st.session_state.active_file}..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""
                Berdasarkan teks materi dari file {st.session_state.active_file} berikut, buatkan {jumlah_soal} soal ujian.
                Variasikan tipe soal menjadi:
                1. Pilihan Ganda (A, B, C, D, E)
                2. Benar/Salah
                3. Pilihan Ganda Kompleks (Jawaban benar lebih dari 1)
                
                Kembalikan dalam format JSON murni tanpa markdown (tanpa ```json) dengan struktur seperti ini:
                [
                    {{
                        "tipe": "pilihan_ganda",
                        "pertanyaan": "...",
                        "opsi": ["A...", "B...", "C...", "D...", "E..."],
                        "jawaban_benar": ["A..."],
                        "penjelasan": "..."
                    }}
                ]
                
                Teks: {current_text[:15000]}
                """
                try:
                    response = model.generate_content(prompt)
                    json_str = response.text.replace("```json", "").replace("```", "").strip()
                    st.session_state.quiz_data = json.loads(json_str)
                    st.session_state.start_time = time.time()
                    st.session_state.submitted = False
                    st.session_state.user_answers = {}
                    st.success("Soal berhasil dibuat! Silakan kerjakan di bawah.")
                except Exception as e:
                    st.error("Gagal membuat soal. Format dari AI tidak sesuai, silakan klik tombol buat soal sekali lagi.")

    if st.session_state.quiz_data:
        st.write(f"⏱️ **Batas Waktu:** {waktu_menit} Menit")
        st.markdown("---")
        
        for i, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**{i+1}. {q['pertanyaan']}** *(Tipe: {q['tipe'].replace('_', ' ').title()})*")
            
            if q['tipe'] == "lebih_dari_satu":
                selected_opts = []
                for opt in q['opsi']:
                    checked = st.checkbox(opt, key=f"q_{i}_{opt}", disabled=st.session_state.submitted)
                    if checked:
                        selected_opts.append(opt)
                st.session_state.user_answers[i] = selected_opts
            else:
                user_choice = st.radio("Pilih jawaban:", q['opsi'], key=f"q_{i}", index=None, disabled=st.session_state.submitted)
                st.session_state.user_answers[i] = user_choice
            
            if st.session_state.submitted:
                user_ans = st.session_state.user_answers.get(i)
                correct_ans = q['jawaban_benar']
                
                if q['tipe'] == "lebih_dari_satu":
                    is_correct = sorted(user_ans if user_ans else []) == sorted(correct_ans)
                else:
                    is_correct = [user_ans] == correct_ans if user_ans else False
                
                if is_correct:
                    st.success(f"✅ **Jawaban Kamu Benar!**\n\n**Penjelasan:** {q['penjelasan']}")
                else:
                    jawaban_user_str = ", ".join(user_ans) if isinstance(user_ans, list) else (user_ans if user_ans else "Tidak dijawab")
                    st.error(f"❌ **Jawaban Kamu Salah.** (Jawaban kamu: {jawaban_user_str})\n\n"
                             f"💡 **Jawaban Benar:** {', '.join(correct_ans)}\n\n"
                             f"📝 **Penjelasan:** {q['penjelasan']}")
            
            st.markdown("---")
            
        if not st.session_state.submitted:
            if st.button("Kumpulkan Jawaban", type="primary"):
                elapsed_time = (time.time() - st.session_state.start_time) / 60
                if elapsed_time > waktu_menit:
                    st.error("Waktu pengerjaan sudah habis!")
                else:
                    st.session_state.submitted = True
                    st.rerun()
        else:
            score = 0
            for i, q in enumerate(st.session_state.quiz_data):
                user_ans = st.session_state.user_answers.get(i)
                correct_ans = q['jawaban_benar']
                if q['tipe'] == "lebih_dari_satu":
                    if sorted(user_ans if user_ans else []) == sorted(correct_ans):
                        score += 1
                else:
                    if [user_ans] == correct_ans:
                        score += 1
            
            total_soal = len(st.session_state.quiz_data)
            nilai_akhir = int((score / total_soal) * 100)
            
            st.balloons()
            st.metric(label="Nilai Akhir Kamu", value=f"{nilai_akhir} / 100", delta=f"{score} dari {total_soal} Soal Benar")
            
            if st.button("Reset / Buat Simulasi Baru"):
                st.session_state.submitted = False
                st.session_state.quiz_data = None
                st.rerun()

# Tab 4: Chatbot AI
with tab4:
    st.header(f"Chatbot AI: {st.session_state.active_file if st.session_state.active_file else 'Belum ada file'}")
    st.write("Tanyakan hal spesifik terkait materi yang sedang aktif dipilih.")
    
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Tanyakan sesuatu tentang materi ini..."):
        if not api_key:
            st.error("Silakan pastikan API Key sudah dimasukkan/tersimpan.")
        else:
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                context = f"Konteks materi PDF dari file {st.session_state.active_file}: {current_text[:10000]}\n\n" if current_text else ""
                full_prompt = context + prompt
                
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
