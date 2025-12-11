#!/usr/bin/env python3
"""
Scraper untuk mengambil daftar URL anime series dari otakudesu.fit (Versi 2)
Dengan filtering yang lebih baik untuk menghindari pagination links
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin
import re

class AnimeSeriesScraper:
    def __init__(self):
        self.base_url = "https://otakudesu.fit"
        self.series_url = f"{self.base_url}/series/"
        # Headers untuk menghindari blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def fetch_page(self, url, timeout=10):
        """
        Fetch halaman dengan timeout dan error handling
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def is_pagination_link(self, url):
        """
        Check apakah URL adalah pagination link
        """
        # Pagination links biasanya berformat /series/page/N/ atau /series/page/N/
        if re.search(r'/series/page/\d+/', url):
            return True
        # Juga hindari link ke halaman series utama sendiri
        if url == self.series_url or url == f"{self.base_url}/series":
            return True
        return False
    
    def clean_title(self, title):
        """
        Bersihkan title dari karakter yang tidak perlu
        """
        # Hapus whitespace berlebih
        title = ' '.join(title.split())
        return title

    def extract_year(self, detail_url):
        """
        Ambil tahun rilis dari halaman detail jika ada elemen dengan class 'addyear'
        """
        html_content = self.fetch_page(detail_url)
        if not html_content:
            return ''

        soup = BeautifulSoup(html_content, 'html.parser')
        year_tag = soup.find(class_='addyear')
        if not year_tag:
            return ''

        year_text = year_tag.get_text(strip=True)
        match = re.search(r'(\d{4})', year_text)
        return match.group(1) if match else year_text
    
    def scrape_series_list(self):
        """
        Scrape daftar series dari halaman utama
        Menggunakan BeautifulSoup untuk parsing HTML
        """
        print(f"Fetching series list from {self.series_url}...")
        html_content = self.fetch_page(self.series_url)
        
        if not html_content:
            print("Failed to fetch series list page")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        series_list = []
        
        # Cari semua link yang mengandung /series/ dalam href
        all_links = soup.find_all('a', href=re.compile(r'/series/'))
        
        seen_urls = set()  # Untuk menghindari duplikat
        
        for link in all_links:
            href = link.get('href', '')
            
            # Filter: harus berisi /series/ dan tidak boleh URL utama atau pagination
            if href and '/series/' in href:
                full_url = urljoin(self.base_url, href)
                
                # Skip pagination links dan halaman utama
                if self.is_pagination_link(full_url):
                    continue
                
                # Hindari duplikat
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    
                    # Ambil title dari link text
                    title = link.get_text(strip=True)
                    title = self.clean_title(title)

                        # Ambil gambar jika tersedia
                    image_tag = link.find('img')
                    image_src = image_tag.get('data-src') if image_tag else ''
                    if not image_src and image_tag:
                        image_src = image_tag.get('src', '')
                    image_url = urljoin(self.base_url, image_src) if image_src else ''

                    # Ambil tahun rilis dari halaman detail
                    year = self.extract_year(full_url)
                    
                    # Filter: title tidak boleh kosong atau hanya angka/simbol
                    if title and not re.match(r'^[\d«»\s]*$', title) and title.lower() not in ['home', 'search', 'previous']:
                        series_list.append({
                            'title': title,
                            'url': full_url,
                            'image_url': image_url,
                            'year': year
                        })
        
        return series_list
    
    def scrape_with_pagination(self, max_pages=None):
        """
        Scrape series dengan pagination
        Jika ada pagination, lanjutkan ke halaman berikutnya
        """
        all_series = []
        page_num = 1
        
        while True:
            if max_pages and page_num > max_pages:
                break
            
            # Construct URL dengan pagination
            if page_num == 1:
                url = self.series_url
            else:
                url = f"{self.series_url}page/{page_num}/"
            
            print(f"\nScraping page {page_num}: {url}")
            
            html_content = self.fetch_page(url)
            if not html_content:
                print(f"Failed to fetch page {page_num}, stopping.")
                break
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Scrape series dari halaman ini
            all_links = soup.find_all('a', href=re.compile(r'/series/'))
            page_series = []
            seen_urls = set()
            
            for link in all_links:
                href = link.get('href', '')
                
                if href and '/series/' in href:
                    full_url = urljoin(self.base_url, href)
                    
                    # Skip pagination links
                    if self.is_pagination_link(full_url):
                        continue
                    
                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        title = link.get_text(strip=True)
                        title = self.clean_title(title)

                        # Ambil gambar jika tersedia
                        image_tag = link.find('img')
                        image_src = image_tag.get('data-src') if image_tag else ''
                        if not image_src and image_tag:
                            image_src = image_tag.get('src', '')
                        image_url = urljoin(self.base_url, image_src) if image_src else ''

                        # Ambil tahun rilis dari halaman detail
                        year = self.extract_year(full_url)
                        
                        # Filter: title tidak boleh kosong atau hanya angka/simbol
                        if title and not re.match(r'^[\d«»\s]*$', title) and title.lower() not in ['home', 'search', 'previous']:
                            page_series.append({
                                'title': title,
                                'url': full_url,
                                'image_url': image_url,
                                'year': year
                            })
            
            if not page_series:
                print(f"No series found on page {page_num}, stopping.")
                break
            
            all_series.extend(page_series)
            print(f"Found {len(page_series)} series on page {page_num}")
            
            # Check apakah ada link "Next" untuk pagination
            next_link = soup.find('a', string=re.compile(r'Next', re.I))
            if not next_link:
                print("No next page found, stopping.")
                break
            
            page_num += 1
            time.sleep(1)  # Delay untuk menghindari rate limiting
        
        return all_series
    
    def save_to_json(self, data, filename):
        """
        Simpan hasil scraping ke file JSON
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nData saved to {filename}")
    
    def save_to_csv(self, data, filename):
        """
        Simpan hasil scraping ke file CSV
        """
        import csv
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'url', 'image_url', 'year'])
            writer.writeheader()
            writer.writerows(data)
        print(f"Data saved to {filename}")

def main():
    scraper = AnimeSeriesScraper()
    
    # Scrape dengan pagination (maksimal 3 halaman untuk testing)
    print("=" * 60)
    print("ANIME SERIES SCRAPER - OTAKUDESU.FIT (v2)")
    print("=" * 60)
    
    series_list = scraper.scrape_with_pagination(max_pages=52)
    
    # Hapus duplikat berdasarkan URL
    unique_series = []
    seen_urls = set()
    for item in series_list:
        if item['url'] not in seen_urls:
            seen_urls.add(item['url'])
            unique_series.append(item)
    
    print(f"\n{'=' * 60}")
    print(f"Total unique series found: {len(unique_series)}")
    print(f"{'=' * 60}\n")
    
    # Tampilkan 15 series pertama
    print("First 15 series:")
    for i, series in enumerate(unique_series[:15], 1):
        print(f"{i}. {series['title']}")
        print(f"   URL: {series['url']}\n")
    
    # Simpan ke file
    scraper.save_to_json(unique_series, './a_grab_anime_list/anime_series_clean.json')
    scraper.save_to_csv(unique_series, './a_grab_anime_list/anime_series_clean.csv')

if __name__ == "__main__":
    main()
