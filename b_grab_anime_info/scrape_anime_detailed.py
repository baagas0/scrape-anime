#!/usr/bin/env python3
"""
Scraper untuk mengambil informasi detail anime series dan URL episode dari otakudesu.fit
Membaca file anime_series_clean.json dan melakukan scraping detail untuk setiap series
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin
import re
import sys

class AnimeDetailedScraper:
    def __init__(self):
        self.base_url = "https://otakudesu.fit"
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
    
    def extract_text_from_li(self, soup, label):
        """
        Extract text dari list item berdasarkan label
        Contoh: <li><b>Genre:</b> <span>Action</span></li>
        """
        for li in soup.find_all('li'):
            b_tag = li.find('b')
            if b_tag and label in b_tag.get_text():
                # Get semua text setelah <b> tag
                content = li.get_text()
                # Remove label dan colon
                result = content.replace(f"{label}:", "").strip()
                return result
        return None
    
    def scrape_series_detail(self, series_url):
        """
        Scrape detail informasi dari halaman series
        """
        print(f"Scraping detail from: {series_url}")
        html_content = self.fetch_page(series_url)
        
        if not html_content:
            print(f"Failed to fetch {series_url}")
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find entry-content div
        entry_content = soup.find('div', class_='entry-content')
        if not entry_content:
            print(f"Entry-content not found for {series_url}")
            return None
        
        # Extract description (first paragraph)
        description = ""
        p_tag = entry_content.find('p')
        if p_tag:
            description = p_tag.get_text(strip=True)
        
        # Extract metadata from ul.data
        data_ul = entry_content.find('ul', class_='data')
        detail = {
            'description': description,
            'genre': [],
            'stars': [],
            'director': '',
            'country': '',
            'network': ''
        }
        
        if data_ul:
            for li in data_ul.find_all('li'):
                b_tag = li.find('b')
                if not b_tag:
                    continue
                
                label = b_tag.get_text(strip=True).lower()
                
                if 'genre' in label:
                    # Extract all genre links
                    genres = []
                    for a in li.find_all('a'):
                        genres.append(a.get_text(strip=True))
                    detail['genre'] = genres
                
                elif 'stars' in label or 'cast' in label:
                    # Extract all actor links
                    stars = []
                    for a in li.find_all('a'):
                        stars.append(a.get_text(strip=True))
                    detail['stars'] = stars
                
                elif 'director' in label:
                    # Extract director
                    a_tag = li.find('a')
                    if a_tag:
                        detail['director'] = a_tag.get_text(strip=True)
                    else:
                        # If no link, get text after <b>
                        text = li.get_text()
                        detail['director'] = text.replace('Director:', '').strip()
                
                elif 'country' in label:
                    # Extract country
                    a_tag = li.find('a')
                    if a_tag:
                        detail['country'] = a_tag.get_text(strip=True)
                    else:
                        text = li.get_text()
                        detail['country'] = text.replace('Country:', '').strip()
                
                elif 'network' in label:
                    # Extract network
                    a_tag = li.find('a')
                    if a_tag:
                        detail['network'] = a_tag.get_text(strip=True)
                    else:
                        text = li.get_text()
                        detail['network'] = text.replace('Network:', '').strip()
        
        return detail
    
    def scrape_episodes(self, series_url):
        """
        Scrape daftar episode dari halaman series
        """
        html_content = self.fetch_page(series_url)
        
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        episodes = []
        
        # Find all links with /watch/ in href (episode links)
        episode_links = soup.find_all('a', href=re.compile(r'/watch/'))
        
        if not episode_links:
            print(f"No episode links found for {series_url}")
            return []
        
        # Find all episode links
        for link in episode_links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            
            # Check if this is an episode link (starts with "EP")
            if text.startswith('EP '):
                # Clean the title (remove date info)
                title = re.sub(r'\s+', ' ', text).strip()
                # Extract just the episode number
                ep_match = re.search(r'EP\s+(\d+)', title)
                if ep_match:
                    ep_num = ep_match.group(1)
                    episodes.append({
                        'episode': f"EP {ep_num}",
                        'title': title,
                        'url': urljoin(self.base_url, href)
                    })
        
        return episodes
    
    def load_series_list(self, json_file):
        """
        Load daftar series dari JSON file
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"File {json_file} not found")
            return []
    
    def scrape_all_series(self, json_file, output_file, max_series=None):
        """
        Scrape semua series dari JSON file
        """
        series_list = self.load_series_list(json_file)
        
        if not series_list:
            print("No series found in JSON file")
            return
        
        print(f"Found {len(series_list)} series to scrape")
        
        enhanced_series = []
        
        for idx, series in enumerate(series_list, 1):
            if max_series and idx > max_series:
                break
            
            print(f"\n[{idx}/{len(series_list)}] Processing: {series['title']}")
            
            # Scrape detail
            detail = self.scrape_series_detail(series['url'])
            if not detail:
                print(f"Failed to scrape detail for {series['title']}")
                continue
            
            # Scrape episodes
            episodes = self.scrape_episodes(series['url'])
            print(f"Found {len(episodes)} episodes")
            
            # Combine data
            enhanced_item = {
                'title': series['title'],
                'url': series['url'],
                'image_url': series.get('image_url', ''),
                'year': series.get('year', ''),
                'description': detail['description'],
                'genre': detail['genre'],
                'stars': detail['stars'],
                'director': detail['director'],
                'country': detail['country'],
                'network': detail['network'],
                'episodes': episodes,
                'total_episodes': len(episodes)
            }
            
            enhanced_series.append(enhanced_item)
            
            # Delay untuk menghindari rate limiting
            time.sleep(1)
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_series, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'=' * 60}")
        print(f"Successfully scraped {len(enhanced_series)} series")
        print(f"Data saved to {output_file}")
        print(f"{'=' * 60}")
        
        return enhanced_series

def main():
    # Check if input file is provided
    input_file = './a_grab_anime_list/anime_series_clean.json'
    output_file = './b_grab_anime_info/anime_series_detailed.json'
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    scraper = AnimeDetailedScraper()
    
    print("=" * 60)
    print("ANIME DETAILED SCRAPER - OTAKUDESU.FIT")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print("=" * 60)
    
    # Scrape all series (limit to 5 for testing)
    scraper.scrape_all_series(input_file, output_file, max_series=999999999)

if __name__ == "__main__":
    main()
