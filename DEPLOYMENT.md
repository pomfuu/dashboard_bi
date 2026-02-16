# 🚀 Panduan Deploy ke Streamlit Cloud

## ⚠️ Masalah: File CSV Terlalu Besar

File `consumer_complaints.csv` (168 MB) terlalu besar untuk di-push ke GitHub (limit 100 MB).

## ✅ Solusi: Upload CSV ke Cloud Storage

### **Metode 1: Google Drive (Direkomendasikan)**

1. **Upload file CSV ke Google Drive:**
   - Buka [Google Drive](https://drive.google.com)
   - Upload file `consumer_complaints.csv`
   - Klik kanan file → "Get link" → "Anyone with the link"
   - Copy link yang didapat (misal: `https://drive.google.com/file/d/ABC123XYZ/view`)

2. **Copy File ID dari URL:**
   ```
   Format awal:
   https://drive.google.com/file/d/ABC123XYZ/view?usp=sharing

   File ID: ABC123XYZ (bagian setelah /d/ dan sebelum /view)
   ```

3. **Setting Streamlit Cloud Secrets:**
   - Buka [Streamlit Cloud](https://share.streamlit.io)
   - Pilih app Anda
   - Klik ⚙️ Settings → Secrets
   - Tambahkan (bisa pakai URL asli atau yang sudah diformat):
   ```toml
   # Opsi 1: URL asli (akan dikonversi otomatis)
   DATA_URL = "https://drive.google.com/file/d/ABC123XYZ/view?usp=sharing"

   # Opsi 2: Direct download URL
   DATA_URL = "https://drive.usercontent.google.com/download?id=ABC123XYZ&export=download&confirm=t"
   ```

   **Catatan:** Aplikasi akan otomatis mendeteksi dan mengkonversi URL Google Drive ke format yang benar.

4. **Deploy ulang aplikasi**

---

### **Metode 2: Dropbox**

1. **Upload file ke Dropbox:**
   - Upload `consumer_complaints.csv` ke Dropbox
   - Klik "Share" → "Create link"
   - Copy link (misal: `https://www.dropbox.com/s/abc123/file.csv?dl=0`)

2. **Ubah parameter dl:**
   ```
   Ubah dari: ?dl=0
   Menjadi:   ?dl=1

   Contoh:
   https://www.dropbox.com/s/abc123/consumer_complaints.csv?dl=1
   ```

3. **Setting Streamlit Cloud Secrets:**
   ```toml
   DATA_URL = "https://www.dropbox.com/s/abc123/consumer_complaints.csv?dl=1"
   ```

---

### **Metode 3: GitHub LFS (Large File Storage)**

Jika ingin tetap di GitHub:

1. **Install Git LFS:**
   ```bash
   git lfs install
   ```

2. **Track file CSV:**
   ```bash
   git lfs track "*.csv"
   git add .gitattributes
   ```

3. **Commit dan push:**
   ```bash
   git add consumer_complaints.csv
   git commit -m "Add CSV via Git LFS"
   git push
   ```

**Catatan:** GitHub LFS gratis hanya untuk 1GB storage dan 1GB bandwidth/bulan.

---

### **Metode 4: Dataset Publik (Alternatif)**

Jika data adalah public dataset, gunakan link original:

```python
# Di main.py, ganti data_url dengan:
data_url = "https://data.consumerfinance.gov/api/views/s6ew-h6mp/rows.csv?accessType=DOWNLOAD"
```

---

## 🔧 Testing Lokal

Sebelum deploy, test dulu di lokal:

```bash
# Set environment variable untuk simulasi
export DATA_URL="https://your-cloud-storage-url.com/file.csv"
streamlit run main.py
```

---

## 📋 Checklist Deploy

- [ ] CSV sudah di-upload ke cloud storage (Google Drive/Dropbox)
- [ ] Link sudah diubah ke format direct download
- [ ] Secrets sudah di-set di Streamlit Cloud
- [ ] Code sudah di-push ke GitHub (tanpa CSV)
- [ ] Test lokal berhasil dengan URL
- [ ] Deploy di Streamlit Cloud

---

## 🆘 Troubleshooting

**Error: "No such file or directory"**
- Pastikan DATA_URL sudah di-set di Streamlit Cloud Secrets
- Cek apakah link direct download benar (coba download manual dulu)

**Error: "403 Forbidden" atau "404"**
- Pastikan file sharing settings di Google Drive/Dropbox adalah "Anyone with the link"
- Format URL sudah benar untuk direct download

**Data loading sangat lambat:**
- Pertama kali load akan lambat (168 MB didownload dari cloud)
- Setelah cached, akan cepat
- Pertimbangkan compress file CSV atau filter data yang diperlukan saja

---

## 💡 Tips Optimasi

### Kurangi Ukuran Dataset (Opsional)

Jika data terlalu besar, filter hanya data yang diperlukan:

```python
# Contoh: ambil hanya 3 tahun terakhir
df = df[df['date_received'] >= '2023-01-01']

# Atau sample random 50%
df = df.sample(frac=0.5, random_state=42)
```

### Compress CSV

```bash
# Compress dengan gzip (bisa mengurangi ukuran 70-80%)
gzip consumer_complaints.csv
# Hasil: consumer_complaints.csv.gz

# Pandas bisa baca langsung:
df = pd.read_csv('consumer_complaints.csv.gz')
```

---

Selamat mencoba! 🎉
