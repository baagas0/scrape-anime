#!/usr/bin/env python3
"""
Scraper untuk mengambil URL iframe dari halaman episode anime
Membaca file anime_series_detailed.json dan scraping URL iframe dari setiap episode
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin
import re
import sys

class IframeUrlScraper:
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
    
    def scrape_iframe_url(self, episode_url):
        """
        Scrape URL iframe dari halaman episode
        Mencari di dalam div#pembed terlebih dahulu, jika tidak ada gunakan iframe lain sebagai fallback
        """
        html_content = self.fetch_page(episode_url)
        
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Coba cari div dengan id "pembed" terlebih dahulu
        pembed = soup.find('div', id='pembed')
        if pembed:
            iframe = pembed.find('iframe')
            if iframe and iframe.get('src'):
                return iframe.get('src')
        
        # Fallback: cari iframe pertama di halaman
        iframe = soup.find('iframe')
        if iframe and iframe.get('src'):
            return iframe.get('src')
        
        return None
    
    def load_detailed_series(self, json_file):
        """
        Load data series detail dari JSON file
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"File {json_file} not found")
            return []
    
    def scrape_all_episodes(self, json_file, output_file, max_episodes=None):
        """
        Scrape URL iframe dari semua episode
        """
        series_list = self.load_detailed_series(json_file)
        
        if not series_list:
            print("No series found in JSON file")
            return
        
        print(f"Found {len(series_list)} series to process")
        
        total_episodes = 0
        processed_episodes = 0
        
        # Count total episodes
        for series in series_list:
            total_episodes += len(series.get('episodes', []))
        
        print(f"Total episodes to scrape: {total_episodes}")
        
        enhanced_series = []
        
        for series_idx, series in enumerate(series_list, 1):
            print(f"\n[Series {series_idx}/{len(series_list)}] {series['title']}")
            
            series_copy = series.copy()
            episodes = series.get('episodes', [])
            
            enhanced_episodes = []
            
            for ep_idx, episode in enumerate(episodes, 1):
                if max_episodes and processed_episodes >= max_episodes:
                    print(f"Reached max episodes limit ({max_episodes})")
                    break
                
                episode_url = episode.get('url')
                if not episode_url:
                    continue
                
                print(f"  [{ep_idx}/{len(episodes)}] Scraping {episode.get('episode')}...", end=' ')
                
                iframe_url = self.scrape_iframe_url(episode_url)
                
                episode_copy = episode.copy()
                if iframe_url:
                    episode_copy['iframe_url'] = iframe_url
                    print(f"✓ Found")
                else:
                    episode_copy['iframe_url'] = None
                    print(f"✗ Not found")
                
                enhanced_episodes.append(episode_copy)
                processed_episodes += 1
                
                # Delay untuk menghindari rate limiting
                time.sleep(0.5)
            
            series_copy['episodes'] = enhanced_episodes
            enhanced_series.append(series_copy)
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_series, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'=' * 60}")
        print(f"Successfully scraped {processed_episodes} episodes")
        print(f"Data saved to {output_file}")
        print(f"{'=' * 60}")
        
        return enhanced_series

def main():
    # Check if input file is provided
    input_file = './b_grab_anime_info/anime_series_detailed.json'
    output_file = './c_grab_iframe/anime_series_with_iframe.json'
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    scraper = IframeUrlScraper()
    
    print("=" * 60)
    print("IFRAME URL SCRAPER - OTAKUDESU.FIT")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print("=" * 60)
    
    # Scrape all episodes (limit to 10 for testing)
    scraper.scrape_all_episodes(input_file, output_file, max_episodes=999999999999999)

if __name__ == "__main__":
    main()
