import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import time

st.set_page_config(page_title="AI Study Assistant - SNBT/TKA/UKK/US", layout="wide")

# Inisialisasi Session State
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "start_time" not in st.session_state:
    st.session_state.start_time = None

st.title("📚 AI Study Assistant & Tryout Simulator")
st.markdown("Persiapan Ujian: **TKA, UKK, US, & SNBT**")

# Sidebar untuk Pengaturan
with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("Masukkan Google Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
        
    st.header("📄 Upload Materi")
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

# Main Area (Tabs)
tab1, tab2, tab3 = st.tabs(["📖 Penjelasan Materi", "📝 Simulasi Ujian", "💬 Chatbot Guru AI"])

# Tab 1: Penjelasan Materi
with tab1:
    st.header("Penjelasan & Ringkasan Materi")
    if st.session_state.pdf_text and api_key:
        if st.button("Buat Ringkasan Materi"):
            with st.spinner("AI sedang merangkum materi..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"Buatkan penjelasan dan ringkasan yang komprehensif, terstruktur, dan mudah dipahami dari teks materi berikut untuk persiapan ujian sekolah/SNBT:\n\n{st.session_state.pdf_text[:15000]}" # Limit teks agar tidak melebihi token
                response = model.generate_content(prompt)
                st.write(response.text)
    elif not api_key:
        st.warning("Silakan masukkan API Key di sidebar.")
    else:
        st.info("Silakan upload dan ekstrak PDF terlebih dahulu.")

# Tab 2: Simulasi Ujian
with tab2:
    st.header("Simulasi Ujian")
    
    col1, col2 = st.columns(2)
    with col1:
        jumlah_soal = st.selectbox("Jumlah Soal", [5, 10, 20, 30])
    with col2:
        waktu_menit = st.selectbox("Waktu Pengerjaan (Menit)", [10, 30, 60, 90, 120])
        
    if st.session_state.pdf_text and api_key:
        if st.button("Buat Soal Ujian"):
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
                    # Parsing JSON murni
                    json_str = response.text.replace("```json", "").replace("```", "").strip()
                    st.session_state.quiz_data = json.loads(json_str)
                    st.session_state.start_time = time.time()
                    st.success("Soal berhasil dibuat! Silakan kerjakan di bawah.")
                except Exception as e:
                    st.error(f"Gagal membuat soal. Terjadi kesalahan format dari AI. Coba lagi. Detail: {e}")

    if st.session_state.quiz_data:
        st.write(f"⏱️ **Batas Waktu:** {waktu_menit} Menit")
        
        with st.form("quiz_form"):
            user_answers = {}
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**{i+1}. {q['pertanyaan']}** *(Tipe: {q['tipe'].replace('_', ' ').title()})*")
                
                if q['tipe'] == "lebih_dari_satu":
                    user_answers[i] = []
                    for opt in q['opsi']:
                        if st.checkbox(opt, key=f"q_{i}_{opt}"):
                            user_answers[i].append(opt)
                else:
                    user_answers[i] = st.radio("Pilih jawaban:", q['opsi'], key=f"q_{i}", index=None)
                st.markdown("---")
            
            submitted = st.form_submit_button("Kumpulkan Jawaban")
            
            if submitted:
                # Cek Waktu
                elapsed_time = (time.time() - st.session_state.start_time) / 60
                if elapsed_time > waktu_menit:
                    st.error("Waktu habis! Jawaban tidak tersimpan.")
                else:
                    st.success(f"Selesai dalam {elapsed_time:.2f} menit!")
                    score = 0
                    
                    for i, q in enumerate(st.session_state.quiz_data):
                        st.subheader(f"Soal {i+1}")
                        correct_answers = q['jawaban_benar']
                        
                        if q['tipe'] == "lebih_dari_satu":
                            # Memeriksa jika list jawaban user sama persis dengan kunci
                            if sorted(user_answers[i]) == sorted(correct_answers):
                                st.success("Jawaban Anda Benar!")
                                score += 1
                            else:
                                st.error(f"Jawaban Anda Salah. Anda menjawab: {user_answers[i]}")
                                st.info(f"Jawaban Benar: {correct_answers}")
                                st.warning(f"Penjelasan: {q['penjelasan']}")
                        else:
                            # Memeriksa Pilihan Ganda atau Benar/Salah
                            ans = [user_answers[i]] if user_answers[i] else []
                            if ans == correct_answers:
                                st.success(f"Jawaban Anda Benar! ({ans[0]})")
                                score += 1
                            else:
                                st.error(f"Jawaban Anda Salah. Anda menjawab: {ans[0] if ans else 'Tidak menjawab'}")
                                st.info(f"Jawaban Benar: {correct_answers[0]}")
                                st.warning(f"Penjelasan: {q['penjelasan']}")
                                
                    st.metric(label="Nilai Akhir Anda", value=f"{(score/len(st.session_state.quiz_data))*100:.0f} / 100")

# Tab 3: Chatbot AI
with tab3:
    st.header("Chatbot AI Khusus Ujian")
    st.write("Tanyakan hal spesifik atau materi yang masih kurang dipahami dari PDF ini.")
    
    # Menampilkan riwayat chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input pengguna
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