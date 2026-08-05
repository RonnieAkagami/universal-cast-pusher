# Universal CAST Data Pusher

An automated, non-destructive Excel-to-MongoDB data import pipeline built with **Streamlit**, **PyMongo**, and **OpenPyXL**.

---

## Features

- ⚡ **Universal Import**: Drag & drop any CAST audit Excel spreadsheet (`.xlsx`).
- 📌 **Org-Specific Scoping**: Target any specified `orgId`.
- 🛡️ **Strict Non-Destructive Update**: Appends new CAST attributes under `attributes.<key>` using `$set`. Pre-existing specifications, titles, and non-matching documents remain 100% untouched.
- 🔍 **Pre-Check Dashboard**: Real-time MongoDB matching analysis and data quality warnings before pushing.
- 🧹 **Automated Quality Cleaning**: Automatically formats multi-line failure report bullet points and converts decimal rates (`0.05` -> `5%`).
- 📄 **Live DB Inspector**: Preview updated documents and full JSON `attributes` directly in the UI.

---

## Directory Structure

```
universal-cast-pusher/
├── .streamlit/
│   └── config.toml          # Custom UI theme settings
├── utils/
│   ├── __init__.py
│   ├── excel_parser.py      # Excel file parsing & pre-check routines
│   └── mongo_client.py      # MongoDB connections, $set updates & auto-cleaning
├── .env.example              # Environment variables template
├── .gitignore                # Git exclusions
├── Dockerfile                # Docker container build configuration
├── README.md                 # Project documentation
├── app.py                    # Streamlit main presentation layer
├── config.py                 # Centralized configuration loader
├── requirements.txt          # Python dependencies
└── start_app.sh              # Local server launcher
```

---

## Local Setup

1. **Clone & Navigate**:
   ```bash
   cd universal-cast-pusher
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment (Optional)**:
   Create a `.env` file or environment variables:
   ```bash
   cp .env.example .env
   ```

4. **Launch Application**:
   ```bash
   ./start_app.sh
   ```
   Or run:
   ```bash
   python3 -m streamlit run app.py
   ```
   Open **http://localhost:8501** in your web browser.

---

## Push to GitHub

To publish this standalone repository to GitHub:

```bash
cd universal-cast-pusher

# Initialize Git repository
git init
git add .
git commit -m "Initial commit of Universal CAST Data Pusher Streamlit app"

# Create a main branch and link your GitHub remote repository
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/universal-cast-pusher.git

# Push to GitHub
git push -u origin main
```

---

## Deploy to Streamlit Cloud (Free & Easy)

1. Push your repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/).
3. Click **New App** and select your repository (`universal-cast-pusher`).
4. Set **Main file path** to `app.py`.
5. Under **Advanced settings**, add your secrets (e.g. `MONGO_URI`):
   ```toml
   MONGO_URI = "mongodb://username:password@hostname:port/omsProd?authSource=admin"
   ```
6. Click **Deploy!**

---

## Deploy using Docker

Build and run using Docker:

```bash
# Build image
docker build -t universal-cast-pusher .

# Run container on port 8501
docker run -d -p 8501:8501 --name cast-pusher universal-cast-pusher
```
