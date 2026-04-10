# AI Apps

Aplikasi AI berbasis Streamlit yang mengintegrasikan Google Gemini untuk dua fitur utama: chatbot multimodal dan image generation. Dilengkapi autentikasi Google OAuth agar hanya pengguna yang login yang dapat mengakses aplikasi.

## Fitur

- **Login dengan Google Account** — autentikasi via OAuth 2.0, profil user ditampilkan di sidebar
- **Chatbot** — percakapan dengan Gemini; mendukung input teks, gambar, dan file (PDF, TXT, CSV). Menyertakan 5 percakapan terakhir sebagai konteks (sliding window memory)
- **Image Generation** — generate gambar dari prompt teks menggunakan Gemini image model, lengkap dengan tombol download PNG

## Prasyarat

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) sebagai package manager
- Google Cloud project dengan **Gemini API** aktif
- Google OAuth 2.0 credentials (Client ID & Secret)

## Instalasi & Menjalankan Secara Lokal

**1. Clone repo dan install dependencies**
```bash
git clone https://github.com/ndifikri/aiapps.git
cd aiapps
uv sync
```

**2. Buat file `.streamlit/secrets.toml`**
```toml
GOOGLE_API_KEY  = "YOUR_GEMINI_API_KEY"
CHAT_MODEL_NAME = "gemini-2.0-flash"
IMAGE_MODEL_NAME = "gemini-2.0-flash-preview-image-generation"

[auth]
redirect_uri   = "http://localhost:8501/oauth2callback"
cookie_secret  = "random-string-minimal-32-karakter"

[auth.google]
client_id              = "YOUR_GOOGLE_CLIENT_ID"
client_secret          = "YOUR_GOOGLE_CLIENT_SECRET"
server_metadata_url    = "https://accounts.google.com/.well-known/openid-configuration"
```

> File ini **tidak** di-commit ke git (sudah ada di `.gitignore`).

**3. Jalankan aplikasi**
```bash
uv run streamlit run main.py
```

## Deploy ke Streamlit Cloud

1. Push repo ke GitHub
2. Buka [share.streamlit.io](https://share.streamlit.io) → **New app** → pilih repo ini, main file: `main.py`
3. Buka **App Settings → Secrets**, paste seluruh isi `secrets.toml` dengan `redirect_uri` diganti ke:
   ```
   https://<nama-app>.streamlit.app/oauth2callback
   ```
4. Klik **Deploy**

## Struktur Project

```
aiapps/
├── main.py                     # Entrypoint aplikasi Streamlit
├── pyproject.toml              # Konfigurasi project & dependencies (uv)
├── uv.lock                     # Lock file dependencies
├── .streamlit/
│   └── secrets.toml            # Secrets lokal (tidak di-commit)
└── .gitignore
```

## Dependencies Utama

| Package | Kegunaan |
|---|---|
| `streamlit` | Framework UI |
| `google-genai` | Google Gemini API client |
| `Pillow` | Pemrosesan gambar |
