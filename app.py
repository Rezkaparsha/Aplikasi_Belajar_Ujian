import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import time

# Konfigurasi Halaman & Tema
st.set_page_config(page_title="AI Study Assistant - SNBT/TKA/UKK/US", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS untuk Tampilan Modern
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    .question-card {
        background-color: #1e222d;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2e3545;
        margin-bottom: 20px;
    }
    .badge {
        background-color: #2b3245;
        color: #00d4ff;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
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

# Inisialisasi Session State
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.title("📚 AI Study Assistant & Tryout Simulator")
st.markdown("Persiapan Ujian: **TKA, UKK, US, & SNBT**")

# Sidebar untuk Pengaturan
with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("Masukkan Google Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
        
    st.header("📄 Upload Materi PDF")
    uploaded_file = st.file_uploader("Upload file PDF materi", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Ekstrak Teks dari PDF"):
            with st.spinner("Membaca PDF..."):
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                st.session_state.pdf_text = text
                st.success("PDF berhasil diekstrak!")

    if st.button("🔒 Keluar / Lock App"):
        st.session_state.authenticated = False
        st.rerun()

# Main Area (Tabs)
tab1, tab2, tab3, tab4 = st.tabs(["📖 Penjelasan PDF", "🎥 Rangkum YouTube", "📝 Simulasi Ujian", "💬 Chatbot AI"])

# Tab 1: Penjelasan Materi
with tab1:
    st.header("Penjelasan & Ringkasan Materi PDF")
    if st.session_state.pdf_text and api_key:
        if st.button("Buat Ringkasan Materi"):
            with st.spinner("AI sedang merangkum materi..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"Buatkan penjelasan dan ringkasan yang komprehensif, terstruktur, dan mudah dipahami dari teks materi berikut untuk persiapan ujian sekolah/SNBT:\n\n{st.session_state.pdf_text[:15000]}"
                response = model.generate_content(prompt)
                st.write(response.text)
    elif not api_key:
        st.warning("Silakan masukkan API Key di sidebar.")
    else:
        st.info("Silakan upload dan ekstrak PDF terlebih dahulu.")

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
        st.warning("Silakan masukkan API Key di sidebar terlebih dahulu.")

# Tab 3: Simulasi Ujian
with tab3:
    st.header("Simulasi Ujian Interaktif")
    
    col1, col2 = st.columns(2)
    with col1:
        jumlah_soal = st.selectbox("Jumlah Soal", [5, 10, 20, 30, 45])
    with col2:
        waktu_menit = st.selectbox("Waktu Pengerjaan (Menit)", [10, 30, 60, 90, 120])
        
    if st.session_state.pdf_text and api_key:
        if st.button("Buat Soal Ujian Baru"):
            with st.spinner("AI sedang menyusun soal..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""
                Berdasarkan teks berikut, buatkan {jumlah_soal} soal ujian.
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
                    }},
                    {{
                        "tipe": "benar_salah",
                        "pertanyaan": "...",
                        "opsi": ["Benar", "Salah"],
                        "jawaban_benar": ["Benar"],
                        "penjelasan": "..."
                    }},
                    {{
                        "tipe": "lebih_dari_satu",
                        "pertanyaan": "...",
                        "opsi": ["Opsi 1", "Opsi 2", "Opsi 3", "Opsi 4"],
                        "jawaban_benar": ["Opsi 1", "Opsi 3"],
                        "penjelasan": "..."
                    }}
                ]
                
                Teks: {st.session_state.pdf_text[:10000]}
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
                    st.error(f"Gagal membuat soal. Coba klik tombol buat soal sekali lagi. Detail: {e}")

    if st.session_state.quiz_data:
        st.write(f"⏱️ **Batas Waktu:** {waktu_menit} Menit")
        st.markdown("---")
        
        # Loop Menampilkan Soal Satu per Satu
        for i, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**{i+1}. {q['pertanyaan']}** *(Tipe: {q['tipe'].replace('_', ' ').title()})*")
            
            # Form Input Jawaban
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
            
            # FITUR PENJELASAN LANGSUNG DI BAWAH JAWABAN (SETELAH SUBMIT)
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
            
        # Tombol Kumpulkan Jawaban
        if not st.session_state.submitted:
            if st.button("Kumpulkan Jawaban", type="primary"):
                elapsed_time = (time.time() - st.session_state.start_time) / 60
                if elapsed_time > waktu_menit:
                    st.error("Waktu pengerjaan sudah habis!")
                else:
                    st.session_state.submitted = True
                    st.rerun()
        else:
            # Hitung Nilai Akhir
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
    st.header("Chatbot AI Khusus Ujian")
    st.write("Tanyakan hal spesifik atau materi yang belum dipahami.")
    
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Tanyakan sesuatu tentang materi ini..."):
        if not api_key:
            st.error("Masukkan API Key di sidebar terlebih dahulu.")
        else:
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                context = f"Konteks materi PDF: {st.session_state.pdf_text[:10000]}\n\n" if st.session_state.pdf_text else ""
                full_prompt = context + prompt
                
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
