# Dashboard Analisis Keluhan Konsumen

Dashboard interaktif untuk menganalisis data keluhan konsumen menggunakan Streamlit dan Plotly.

## 📋 Fitur

- **10+ Insight Mendalam**: Analisis korelasi multi-dimensi
- **Filter Interaktif**: Filter berdasarkan tahun dan produk
- **Visualisasi Dinamis**: Grafik interaktif dengan Plotly
- **Pivot Tables**: 8 pivot table untuk analisis mendalam
- **Rekomendasi Power BI**: Panduan lengkap untuk implementasi di Power BI
- **Export Data**: Download data dalam format CSV

## 🚀 Cara Menjalankan

1. **Clone repository ini**
   ```bash
   git clone <repository-url>
   cd dashboard_bi
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Siapkan data**
   - Letakkan file CSV Anda dengan nama `consumer_complaints.csv` di folder root
   - File harus memiliki kolom: `date_received`, `product`, `issue`, `state`, `company`, `timely_response`, `consumer_disputed_is`, dll.

4. **Jalankan aplikasi**
   ```bash
   streamlit run main.py
   ```

5. **Buka browser**
   - Aplikasi akan terbuka otomatis di `http://localhost:8501`

## 📊 Struktur Data

File CSV yang dibutuhkan harus memiliki kolom berikut:
- `date_received`: Tanggal keluhan diterima
- `date_sent_to_company`: Tanggal dikirim ke perusahaan
- `product`: Jenis produk
- `issue`: Jenis masalah
- `state`: Lokasi (negara bagian)
- `company`: Nama perusahaan
- `timely_response`: Apakah respons tepat waktu (Yes/No)
- `consumer_disputed_is`: Apakah konsumen bersengketa (Yes/No)
- `submitted_via`: Channel pengajuan keluhan
- `company_response_to_consumer`: Jenis respons perusahaan
- `complaint_id`: ID unik keluhan

## 📦 Dependencies

- streamlit
- pandas
- plotly
- numpy

Lihat `requirements.txt` untuk versi lengkap.

## 🎨 Kustomisasi

### Mengubah Tema
Edit file `.streamlit/config.toml` untuk mengubah warna dan tema:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

## 📁 Struktur Folder

```
dashboard_bi/
├── main.py                 # Aplikasi utama
├── consumer_complaints.csv # Data (tidak di-commit)
├── .streamlit/
│   └── config.toml        # Konfigurasi tema
├── .gitignore             # File yang diabaikan Git
├── requirements.txt       # Dependencies Python
└── README.md             # Dokumentasi ini
```

## 💡 Tips

- Gunakan filter di sidebar untuk fokus pada data tertentu
- Semua pivot table dapat di-export ke CSV
- Dashboard ini dirancang untuk mudah diintegrasikan dengan Power BI

## 📝 Lisensi

[MIT License](LICENSE) - bebas digunakan untuk keperluan pribadi maupun komersial.

## 🤝 Kontribusi

Kontribusi selalu diterima! Silakan buat Pull Request atau laporkan issue.
