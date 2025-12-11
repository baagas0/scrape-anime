# Strategi dan Panduan Best Practice Scraping Otakudesu.fit

Dokumen ini menjelaskan strategi terbaik (*best practice*) untuk melakukan *web scraping* pada situs Otakudesu.fit, khususnya untuk menghindari *overlay* iklan, serta menjelaskan logika dari skrip Python yang telah berhasil mengumpulkan daftar URL seri anime.

## 1. Strategi Best Practice untuk Menghindari Iklan

Masalah utama pada situs ini adalah *full-screen overlay* iklan yang muncul ketika pengguna berinteraksi dengan elemen di halaman. Iklan ini biasanya dipicu oleh *event listener* JavaScript yang terpasang pada elemen-elemen yang dapat diklik.

**Strategi Terbaik:**

Untuk menghindari masalah ini, kita harus menghindari eksekusi JavaScript sama sekali.

1.  **Gunakan `requests` dan `BeautifulSoup`:** Alih-alih menggunakan *headless browser* (seperti Selenium atau Playwright) yang akan memuat dan menjalankan JavaScript (termasuk iklan), kita menggunakan pustaka `requests` untuk mengambil konten HTML mentah dari server, dan `BeautifulSoup` untuk menganalisis struktur HTML tersebut.
2.  **Bypass Iklan:** Karena iklan *overlay* dan *pop-up* hanya muncul melalui eksekusi JavaScript, dengan hanya mengambil HTML mentah, kita secara efektif **melewati seluruh mekanisme iklan** tersebut. Server hanya mengirimkan HTML statis yang berisi daftar seri anime, dan itulah yang kita ambil.
3.  **Simulasi Browser:** Dalam skrip, kita menyertakan *header* `User-Agent` yang valid (`Mozilla/5.0...`) untuk membuat permintaan kita terlihat seperti permintaan dari *browser* biasa, yang membantu mencegah *blocking* sederhana dari server.

Strategi ini adalah *best practice* karena:
*   **Cepat dan Ringan:** Tidak perlu memuat aset (gambar, CSS, JS) yang tidak perlu, sehingga proses *scraping* jauh lebih cepat.
*   **Stabil:** Tidak bergantung pada perubahan JavaScript atau CSS iklan. Selama struktur HTML dasar daftar seri tidak berubah, skrip akan tetap berfungsi.

## 2. Penjelasan Logika Skrip Python (`scrape_anime_series_v2.py`)

Skrip yang telah dieksekusi menggunakan pustaka `requests` dan `BeautifulSoup` untuk mengambil daftar seri anime.

| Komponen | Fungsi |
| :--- | :--- |
| **`requests.Session()`** | Digunakan untuk mempertahankan *header* `User-Agent` di setiap permintaan, membuat sesi *scraping* lebih efisien. |
| **`fetch_page(url)`** | Mengambil konten HTML dari URL yang diberikan. Dilengkapi dengan *error handling* untuk kegagalan koneksi atau status HTTP non-200. |
| **`is_pagination_link(url)`** | Fungsi filter penting untuk membedakan URL seri anime dari URL navigasi halaman (`/series/page/N/`). |
| **`scrape_with_pagination(max_pages)`** | Logika utama yang mengiterasi melalui halaman-halaman seri. Secara otomatis mendeteksi dan melanjutkan ke halaman berikutnya hingga tidak ada lagi link "Next" atau mencapai batas `max_pages`. |
| **`BeautifulSoup` Selector | Menggunakan `soup.find_all('a', href=re.compile(r'/series/'))` untuk mencari semua tag `<a>` (link) yang mengandung `/series/` di atribut `href`-nya. Ini adalah cara yang kuat untuk menargetkan link seri tanpa bergantung pada nama kelas CSS yang mungkin berubah. |
| **Pembersihan Data** | Menggunakan `link.get_text(strip=True)` untuk mengambil judul, dan fungsi `clean_title` untuk menghilangkan spasi berlebih dan karakter non-alfanumerik yang tidak relevan. |

## 3. Hasil Scraping

Skrip telah berhasil mengumpulkan **30 URL seri anime unik** dari 3 halaman pertama situs.

Daftar lengkap telah disimpan dalam dua format file:
1.  **JSON:** `/home/ubuntu/anime_series_clean.json`
2.  **CSV:** `/home/ubuntu/anime_series_clean.csv`

Berikut adalah 5 contoh data yang berhasil dikumpulkan:

| Title | URL |
| :--- | :--- |
| Shuumatsu no Walküre III2021EP15TV | `https://otakudesu.fit/series/shuumatsu-no-walkure-iii/` |
| Nukitashi the Animation Specials2025EP2TV | `https://otakudesu.fit/series/nukitashi-the-animation-specials/` |
| CompletedTatsuki Fujimoto 17-262025EP8TV | `https://otakudesu.fit/series/tatsuki-fujimoto-17-26/` |
| Disney Twisted-Wonderland: The Animation2025EP8TV | `https://otakudesu.fit/series/disney-twisted-wonderland-the-animation/` |
| Long Zu II: Daowangzhe Zhi Tong-EP10TV | `https://otakudesu.fit/series/long-zu-ii-daowangzhe-zhi-tong/` |

## 4. Langkah Selanjutnya: Scraping URL Episode

Anda menyebutkan bahwa langkah selanjutnya adalah *scraping* URL per episode dari halaman seri.

**Panduan untuk Modifikasi Skrip:**

1.  **Iterasi URL Seri:** Anda dapat memuat file `/home/ubuntu/anime_series_clean.json` dan mengiterasi melalui setiap URL seri yang ada di dalamnya.
2.  **Analisis Halaman Seri:** Untuk setiap URL seri (misalnya, `https://otakudesu.fit/series/shuumatsu-no-walkure-iii/`), Anda perlu memanggil `fetch_page()` lagi.
3.  **Temukan Link Episode:** Setelah mendapatkan konten HTML halaman seri, gunakan `BeautifulSoup` untuk mencari link episode. Berdasarkan struktur umum situs seperti ini, link episode kemungkinan besar akan berada di dalam tag `<a>` dengan pola `href` yang mengandung `/episode/` atau `/ep/`.

**Contoh Selector untuk Episode:**

```python
# Di dalam fungsi baru untuk scrape episode
soup_series = BeautifulSoup(html_content, 'html.parser')
episode_links = soup_series.find_all('a', href=re.compile(r'/(episode|ep)/'))

for link in episode_links:
    episode_url = urljoin(self.base_url, link.get('href'))
    episode_title = link.get_text(strip=True)
    # Simpan episode_title dan episode_url
```

Anda dapat menambahkan fungsi baru ke dalam kelas `AnimeSeriesScraper` untuk melakukan langkah ini, atau membuat skrip terpisah yang membaca hasil *scraping* seri dan melanjutkan ke *scraping* episode.
