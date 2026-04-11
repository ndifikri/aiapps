import io

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# ─── Config ───────────────────────────────────────────────────────────────────
# Semua nilai dibaca dari Streamlit Secrets (.streamlit/secrets.toml secara
# lokal, atau App Settings > Secrets saat di-deploy di Streamlit Cloud).
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
CHAT_MODEL_NAME = st.secrets["CHAT_MODEL_NAME"]
IMAGE_MODEL_NAME = st.secrets["IMAGE_MODEL_NAME"]

# Inisialisasi Google Generative AI client dengan API key dari secrets
client = genai.Client(api_key=GOOGLE_API_KEY)

# Jumlah percakapan (pasang user + assistant) yang disertakan sebagai
# konteks saat memanggil API. Nilai 5 berarti 10 pesan terakhir dikirim.
MEMORY_WINDOW = 5

st.set_page_config(
    page_title="Lumina AI",
    page_icon="✨",
    layout="wide",
)

# ─── Auth Gate ────────────────────────────────────────────────────────────────
# Periksa status login via Streamlit built-in auth (OAuth 2.0).
# Jika belum login, tampilkan halaman landing dan hentikan eksekusi lebih lanjut
# dengan st.stop() agar halaman utama tidak ikut ter-render.
if not st.user.is_logged_in:
    # ── Hero Section ──────────────────────────────────────────────────────────
    col_hero, col_space = st.columns([2, 1])
    with col_hero:
        st.markdown("# ✨ Lumina AI")
        st.markdown("### *Illuminate your ideas — from words to visuals.*")
        st.markdown(
            "Lumina AI adalah platform AI kreatif yang menggabungkan kekuatan "
            "**chatbot multimodal** dan **image generation** dalam satu tempat. "
            "Didukung oleh Google Gemini, Lumina hadir sebagai partner kreatif "
            "yang membantu Anda mengekspresikan ide lewat percakapan maupun visual."
        )
        st.markdown("")
        if st.button("🔐  Login with Google Account", type="primary"):
            st.login("google")  # redirect ke Google OAuth
        st.caption("Lumina AI menggunakan Google OAuth 2.0 untuk autentikasi yang aman.")

    st.divider()

    # ── Feature Highlights ────────────────────────────────────────────────────
    st.markdown("### Apa yang bisa Lumina AI lakukan?")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 💬 Multimodal Chatbot")
        st.markdown(
            "Berinteraksi dengan AI menggunakan teks, gambar, atau file. "
            "Lumina mengingat konteks percakapan sehingga diskusi terasa natural dan mengalir."
        )
    with col2:
        st.markdown("#### 🎨 Image Generation")
        st.markdown(
            "Ubah ide menjadi gambar hanya dari sebuah kalimat. "
            "Gunakan fitur **Prompt Enhancer** agar deskripsi Anda dioptimalkan "
            "oleh AI sebelum gambar di-generate."
        )
    with col3:
        st.markdown("#### 🔒 Aman & Personal")
        st.markdown(
            "Login dengan akun Google Anda. Data sesi hanya tersimpan "
            "selama browser terbuka dan tidak dibagikan ke pihak manapun."
        )

    st.stop()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
# Sidebar hanya dirender setelah user berhasil login.
with st.sidebar:
    # Kartu profil: foto, nama, dan status verifikasi email user yang sedang login
    with st.container(border=True):
        col_pic, col_info = st.columns([1, 2])
        with col_pic:
            st.image(st.user["picture"], width=56)
        with col_info:
            st.markdown(f"**{st.user['name']}**")
            email_status = "✅" if st.user.email_verified else "❌"
            st.caption(f"{st.user['email']} {email_status}")

    # Tombol logout: menghapus sesi dan mengarahkan kembali ke halaman landing
    if st.button("Logout", type="primary", use_container_width=True):
        st.logout()

    st.divider()
    st.markdown("## ✨ Lumina AI")
    st.caption("*Illuminate your ideas.*")

    # Navigasi menu utama
    menu = st.radio(
        "Pilih Menu",
        ["💬 Chatbot", "🎨 Image Generation"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(f"Chat model: `{CHAT_MODEL_NAME}`")
    st.caption(f"Image model: `{IMAGE_MODEL_NAME}`")


# ─── Helper ───────────────────────────────────────────────────────────────────
def pil_to_part(img: Image.Image, mime_type: str = "image/png") -> types.Part:
    """Konversi PIL Image menjadi types.Part agar bisa dikirim ke Gemini API."""
    buf = io.BytesIO()
    fmt = "PNG" if mime_type == "image/png" else "JPEG"
    img.save(buf, format=fmt)
    return types.Part.from_bytes(data=buf.getvalue(), mime_type=mime_type)


# ─── MENU: CHATBOT ────────────────────────────────────────────────────────────
if menu == "💬 Chatbot":
    st.title("💬 Chatbot")
    st.markdown(
        "Tanyakan apa saja kepada Lumina — mulai dari pertanyaan umum, analisis dokumen, "
        "hingga diskusi kreatif. Anda juga bisa melampirkan **gambar atau file** "
        "untuk dibahas bersama."
    )
    st.divider()

    # Inisialisasi dua daftar di session_state (per-sesi browser):
    #   display_messages : riwayat untuk ditampilkan di UI (teks + gambar + nama file)
    #   api_messages     : riwayat dalam format Gemini API (types.Part), dipakai
    #                      untuk membangun konteks percakapan saat memanggil model
    if "display_messages" not in st.session_state:
        st.session_state.display_messages = []
    if "api_messages" not in st.session_state:
        st.session_state.api_messages = []

    # Tampilkan seluruh riwayat percakapan dari session_state
    for msg in st.session_state.display_messages:
        with st.chat_message(msg["role"]):
            for part in msg["parts"]:
                if part["type"] == "text":
                    st.markdown(part["data"])
                elif part["type"] == "image":
                    st.image(part["data"])
                elif part["type"] == "file":
                    st.caption(f"📎 {part['name']}")

    # Komponen upload file; state-nya dipertahankan antar-rerun oleh Streamlit
    # sampai user secara manual menghapus file dari uploader.
    with st.expander("📎 Lampirkan file / gambar (opsional)"):
        uploaded_files = st.file_uploader(
            "Upload",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg", "gif", "webp", "pdf", "txt", "csv"],
            label_visibility="collapsed",
        )

    # Tangkap input teks dari user melalui chat input di bagian bawah halaman
    if user_input := st.chat_input("Ketik pesan…"):
        # Bangun dua representasi pesan secara bersamaan:
        #   user_api_parts  : list types.Part untuk dikirim ke Gemini API
        #   display_parts   : list dict untuk ditampilkan di UI
        user_api_parts: list[types.Part] = [types.Part(text=user_input)]
        display_parts: list = [{"type": "text", "data": user_input}]

        for f in (uploaded_files or []):
            raw = f.read()
            mime = f.type or "application/octet-stream"
            if mime.startswith("image/"):
                # Gambar dikonversi ke PIL lalu ke types.Part agar bisa dibaca model
                img = Image.open(io.BytesIO(raw))
                user_api_parts.append(pil_to_part(img, mime))
                display_parts.append({"type": "image", "data": img})
            else:
                # File non-gambar (PDF, TXT, CSV) dikirim sebagai raw bytes
                user_api_parts.append(types.Part.from_bytes(data=raw, mime_type=mime))
                display_parts.append({"type": "file", "name": f.name})

        # Simpan dan tampilkan bubble pesan user sebelum menunggu respons
        st.session_state.display_messages.append({"role": "user", "parts": display_parts})
        with st.chat_message("user"):
            for part in display_parts:
                if part["type"] == "text":
                    st.markdown(part["data"])
                elif part["type"] == "image":
                    st.image(part["data"])
                elif part["type"] == "file":
                    st.caption(f"📎 {part['name']}")

        # Sliding window memory: ambil MEMORY_WINDOW percakapan terakhir
        # (= MEMORY_WINDOW * 2 pesan: tiap percakapan terdiri dari 1 user + 1 model)
        # lalu tambahkan pesan user saat ini di akhir sebagai giliran terbaru.
        history_window = st.session_state.api_messages[-(MEMORY_WINDOW * 2):]
        contents = [
            types.Content(role=msg["role"], parts=msg["parts"])
            for msg in history_window
        ]
        contents.append(types.Content(role="user", parts=user_api_parts))

        # Kirim ke Gemini API dan tampilkan respons
        with st.chat_message("assistant"):
            with st.spinner("Memproses…"):
                try:
                    response = client.models.generate_content(
                        model=CHAT_MODEL_NAME,
                        contents=contents,
                    )
                    reply = response.text
                except Exception as e:
                    reply = f"⚠️ Error: {e}"
                st.markdown(reply)

        # Simpan pesan user dan balasan model ke kedua daftar history
        st.session_state.api_messages.append({"role": "user", "parts": user_api_parts})
        st.session_state.api_messages.append(
            {"role": "model", "parts": [types.Part(text=reply)]}
        )
        st.session_state.display_messages.append(
            {"role": "assistant", "parts": [{"type": "text", "data": reply}]}
        )

    # Tombol hapus percakapan: reset kedua daftar history dan reload halaman
    if st.session_state.get("display_messages"):
        with st.sidebar:
            if st.button("🗑️ Hapus Percakapan", use_container_width=True):
                st.session_state.display_messages = []
                st.session_state.api_messages = []
                st.rerun()


# ─── MENU: IMAGE GENERATION ───────────────────────────────────────────────────
elif menu == "🎨 Image Generation":
    st.title("🎨 Image Generation")
    st.markdown(
        "Ubah ide Anda menjadi sebuah gambar hanya dengan mendeskripsikannya. "
        "Aktifkan **Prompt Enhancer** agar AI membantu memperkaya deskripsi Anda "
        "sebelum gambar di-generate."
    )
    st.divider()

    # ── Prompt Enhancer toggle ────────────────────────────────────────────────
    # Saat diaktifkan, prompt user dikirim terlebih dahulu ke CHAT_MODEL untuk
    # diubah menjadi redaksi prompt image generation yang lebih deskriptif dan
    # efektif, sebelum diteruskan ke IMAGE_MODEL.
    enhance_prompt = st.toggle(
        "✨ Prompt Enhancer",
        value=False,
        help=(
            "Aktifkan agar prompt Anda otomatis diperbaiki dan diperkaya oleh AI "
            "sebelum dikirim ke model image generation."
        ),
    )

    prompt = st.text_area(
        "Prompt",
        placeholder="Contoh: A futuristic city at night with neon lights reflecting on a rainy street…",
        height=130,
    )

    col_btn, _ = st.columns([1, 5])
    with col_btn:
        generate = st.button("✨ Generate", type="primary", use_container_width=True)

    if generate:
        if not prompt.strip():
            st.warning("Silakan isi prompt terlebih dahulu.")
        else:
            # ── Tahap 1 (opsional): perbaiki prompt via chat model ────────────
            final_prompt = prompt

            if enhance_prompt:
                with st.spinner("Memperbaiki prompt…"):
                    try:
                        enhance_instruction = (
                            "You are an expert AI image generation prompt engineer. "
                            "Rewrite the following user prompt into a highly detailed, "
                            "vivid, and effective image generation prompt. "
                            "Improve composition, lighting, style, mood, and visual details. "
                            "Return ONLY the improved prompt text, no explanation, "
                            "no prefix, no quotes.\n\n"
                            f"User prompt: {prompt}"
                        )
                        enhance_response = client.models.generate_content(
                            model=CHAT_MODEL_NAME,
                            contents=enhance_instruction,
                        )
                        final_prompt = enhance_response.text.strip()
                    except Exception as e:
                        st.warning(f"Prompt Enhancer gagal, menggunakan prompt asli. ({e})")
                        final_prompt = prompt

                # Tampilkan perbandingan prompt asli vs prompt yang telah diperbaiki
                with st.expander("🔍 Lihat perbandingan prompt", expanded=True):
                    col_orig, col_enhanced = st.columns(2)
                    with col_orig:
                        st.markdown("**Prompt asli**")
                        st.info(prompt)
                    with col_enhanced:
                        st.markdown("**Prompt setelah di-enhance**")
                        st.success(final_prompt)

            # ── Tahap 2: generate gambar dengan final_prompt ──────────────────
            with st.spinner("Generating image…"):
                try:
                    # Kirim final_prompt ke model image generation.
                    # response_modalities ["TEXT", "IMAGE"] memungkinkan model
                    # mengembalikan teks (caption/deskripsi) sekaligus gambar.
                    response = client.models.generate_content(
                        model=IMAGE_MODEL_NAME,
                        contents=final_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["TEXT", "IMAGE"]
                        ),
                    )

                    image_found = False
                    for part in response.candidates[0].content.parts:
                        if part.inline_data is not None:
                            # Decode bytes dari respons menjadi PIL Image lalu tampilkan
                            image_found = True
                            img = Image.open(io.BytesIO(part.inline_data.data))
                            st.image(img, width="stretch")

                            # Sediakan tombol download gambar hasil generate
                            buf = io.BytesIO()
                            img.save(buf, format="PNG")
                            st.download_button(
                                label="⬇️ Download PNG",
                                data=buf.getvalue(),
                                file_name="generated_image.png",
                                mime="image/png",
                            )
                        elif part.text:
                            # Tampilkan teks pendamping jika ada (misal: deskripsi gambar)
                            st.markdown(part.text)

                    if not image_found:
                        st.info("Model tidak menghasilkan gambar. Coba ubah prompt Anda.")

                except Exception as e:
                    st.error(f"Error: {e}")
