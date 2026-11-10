# Wahyu Pamungkas - Modern Developer Portfolio

Website portofolio interaktif dan responsif untuk web developer dengan tampilan futuristik, efek pembuka *cinematic shutter*, sistem digital HUD melingkar, dan animasi kinetik di setiap halaman.

---

## 📁 Struktur Folder Proyek Bersih

```text
prtprog/
├── app.py                         # Aplikasi utama Streamlit (Frontend & Backend UI)
├── requirements.txt               # Dependensi paket Python yang dibutuhkan
├── README.md                      # Dokumentasi proyek portofolio
├── .gitignore                     # Konfigurasi file yang diabaikan oleh Git
├── .streamlit/
│   └── config.toml                # Tema gelap & konfigurasi server Streamlit
│
└── assets/                        # Berkas dan aset aktif portofolio
    ├── profile_clean.png          # Foto profil utama (transparan bebas artefak)
    ├── CV_WAHYU PAMUNGKAS.pdf     # Berkas CV resmi untuk fitur Download CV
    └── sspr1.jpeg                 # Screenshot pratinjau asli proyek Financial Distress ML
```

---

## 🚀 Cara Menjalankan Portofolio

1. **Pastikan Python (>= 3.9) telah terpasang.**
2. **Install dependensi yang diperlukan**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Jalankan aplikasi dengan Streamlit**:
   ```bash
   streamlit run app.py
   ```
4. Buka browser pada alamat `http://localhost:8501`.

---

## ✨ Fitur Utama

- **Cinematic Shutter Entrance**: Layar pembuka interaktif dengan pecahan partikel berkilau (*particle explosion*) dan tombol masuk (*Click to Enter*).
- **Circular Digital HUD System**: Bentuk sistem digital melingkar futuristik di belakang foto profil dengan radar scanner berputar, node sirkuit data, dan cincin telemetri.
- **Responsif di Semua Perangkat**: Tata letak otomatis menyesuaikan ukuran desktop, tablet, maupun smartphone tanpa menutupi subjek foto profil.
- **Dark & Light Mode**: Tombol saklar tema terang dan gelap dengan transisi warna yang halus.
- **Section Lengkap**:
  - `Home`: Hero showcase, kartu kode interaktif, dan tech stack icons.
  - `About`: Ringkasan pengalaman kerja dan metrik statistik 3D.
  - `Skills`: Kartu keahlian dengan animasi progres bar dan laser streak.
  - `Projects`: Mockup visual interaktif dari proyek pilihan.
  - `Blog`: Kartu artikel dan wawasan industri.
  - `Contact`: Testimonial klien, sosial media, dan formulir kontak langsung.

---

© 2024 Wahyu Pamungkas (Yuui.Dev). All rights reserved.
