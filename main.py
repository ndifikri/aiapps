import io

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
CHAT_MODEL_NAME = st.secrets["CHAT_MODEL_NAME"]
IMAGE_MODEL_NAME = st.secrets["IMAGE_MODEL_NAME"]

client = genai.Client(api_key=GOOGLE_API_KEY)

st.set_page_config(
    page_title="AI Apps",
    page_icon="🤖",
    layout="wide",
)

# ─── Auth Gate ────────────────────────────────────────────────────────────────
if not st.user.is_logged_in:
    st.title("Welcome to AI Apps 🤖")
    st.markdown("Silakan login untuk menggunakan aplikasi.")
    if st.button("Login with Google Account", type="primary"):
        st.login("google")
    st.stop()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    with st.container(border=True):
        col_pic, col_info = st.columns([1, 2])
        with col_pic:
            st.image(st.user["picture"], width=56)
        with col_info:
            st.markdown(f"**{st.user['name']}**")
            email_status = "✅" if st.user.email_verified else "❌"
            st.caption(f"{st.user['email']} {email_status}")
    if st.button("Logout", type="primary", use_container_width=True):
        st.logout()

    st.divider()
    st.title("🤖 AI Apps")
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
    buf = io.BytesIO()
    fmt = "PNG" if mime_type == "image/png" else "JPEG"
    img.save(buf, format=fmt)
    return types.Part.from_bytes(data=buf.getvalue(), mime_type=mime_type)


MEMORY_WINDOW = 5  # jumlah percakapan (user+assistant) yang diingat

# ─── CHATBOT ──────────────────────────────────────────────────────────────────
if menu == "💬 Chatbot":
    st.title("💬 Chatbot")

    if "display_messages" not in st.session_state:
        st.session_state.display_messages = []  # untuk tampilan
    if "api_messages" not in st.session_state:
        st.session_state.api_messages = []      # untuk konteks API (role: user/model)

    # Render history
    for msg in st.session_state.display_messages:
        with st.chat_message(msg["role"]):
            for part in msg["parts"]:
                if part["type"] == "text":
                    st.markdown(part["data"])
                elif part["type"] == "image":
                    st.image(part["data"])
                elif part["type"] == "file":
                    st.caption(f"📎 {part['name']}")

    # File uploader (persists until user removes it)
    with st.expander("📎 Lampirkan file / gambar (opsional)"):
        uploaded_files = st.file_uploader(
            "Upload",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg", "gif", "webp", "pdf", "txt", "csv"],
            label_visibility="collapsed",
        )

    # Chat input
    if user_input := st.chat_input("Ketik pesan…"):
        # Build API parts untuk pesan saat ini
        user_api_parts: list[types.Part] = [types.Part(text=user_input)]
        display_parts: list = [{"type": "text", "data": user_input}]

        for f in (uploaded_files or []):
            raw = f.read()
            mime = f.type or "application/octet-stream"
            if mime.startswith("image/"):
                img = Image.open(io.BytesIO(raw))
                user_api_parts.append(pil_to_part(img, mime))
                display_parts.append({"type": "image", "data": img})
            else:
                user_api_parts.append(types.Part.from_bytes(data=raw, mime_type=mime))
                display_parts.append({"type": "file", "name": f.name})

        # Render user bubble
        st.session_state.display_messages.append(
            {"role": "user", "parts": display_parts}
        )
        with st.chat_message("user"):
            for part in display_parts:
                if part["type"] == "text":
                    st.markdown(part["data"])
                elif part["type"] == "image":
                    st.image(part["data"])
                elif part["type"] == "file":
                    st.caption(f"📎 {part['name']}")

        # Bangun konteks: ambil MEMORY_WINDOW percakapan terakhir (= 2*N pesan)
        history_window = st.session_state.api_messages[-(MEMORY_WINDOW * 2):]
        contents = [
            types.Content(role=msg["role"], parts=msg["parts"])
            for msg in history_window
        ]
        contents.append(types.Content(role="user", parts=user_api_parts))

        # Get response
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

        # Simpan ke history
        st.session_state.api_messages.append({"role": "user", "parts": user_api_parts})
        st.session_state.api_messages.append(
            {"role": "model", "parts": [types.Part(text=reply)]}
        )
        st.session_state.display_messages.append(
            {"role": "assistant", "parts": [{"type": "text", "data": reply}]}
        )

    # Clear chat
    if st.session_state.get("display_messages"):
        with st.sidebar:
            if st.button("🗑️ Hapus Percakapan", use_container_width=True):
                st.session_state.display_messages = []
                st.session_state.api_messages = []
                st.rerun()


# ─── IMAGE GENERATION ─────────────────────────────────────────────────────────
elif menu == "🎨 Image Generation":
    st.title("🎨 Image Generation")

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
            with st.spinner("Generating image…"):
                try:
                    response = client.models.generate_content(
                        model=IMAGE_MODEL_NAME,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["TEXT", "IMAGE"]
                        ),
                    )

                    image_found = False
                    for part in response.candidates[0].content.parts:
                        if part.inline_data is not None:
                            image_found = True
                            img = Image.open(io.BytesIO(part.inline_data.data))
                            st.image(img, width="stretch")

                            buf = io.BytesIO()
                            img.save(buf, format="PNG")
                            st.download_button(
                                label="⬇️ Download PNG",
                                data=buf.getvalue(),
                                file_name="generated_image.png",
                                mime="image/png",
                            )
                        elif part.text:
                            st.markdown(part.text)

                    if not image_found:
                        st.info("Model tidak menghasilkan gambar. Coba ubah prompt Anda.")

                except Exception as e:
                    st.error(f"Error: {e}")
