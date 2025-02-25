import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}
try:
    driver = webdriver.Chrome()
except:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    print("Running in headless mode.")
    
_scroll = False
    
# Function to safely make a request
def safe_request(url):
    try:
        # Use requests to check the status code first
        response = requests.get(url , headers=headers)
        if 200 <= response.status_code < 300:
            driver.get(url)
            time.sleep(5)  # Wait for the page to load
            if _scroll:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(50)  # Wait for new content to load
                _scroll = False
            print(f"{url} => Page retrieved successfully!")
            return driver.page_source
        elif response.status_code == 404:
            print(f"{url} => Error: 404 Not Found")
            return None
        elif response.status_code == 503:
            print(f"{url} => Error: 503 Service Unavailable")
            return None
        elif response.status_code >= 400:
            print(f"{url} => Client Error: {response.status_code}")
            return None
        elif response.status_code >= 500:
            print(f"{url} => Server Error: {response.status_code}")
            return None
       
    except Exception as e:
        print(f"{url} => An error occurred: {e}")
        return None

base_url = 'https://igod.gov.in/sectors'
# Send a GET request to fetch the HTML content
res = safe_request(base_url)
if res:
    soup = BeautifulSoup(res, 'html.parser')
    # Extract links
    sector_links = {a.text.strip().replace(" ","_").replace("_&" , ""): a['href'] for a in soup.select('.sector-container .sector-box')}
sector_links_slice = dict(list(sector_links.items())[0:6])

count = 1
for name , link in sector_links_slice.items():
    print(f'count => {count} out of {len(sector_links_slice)}')
    
    # Scrape the main page
    main_page_source = safe_request(link)
    if main_page_source:
        soup = BeautifulSoup(main_page_source, 'html.parser')
        if soup:
            _scroll = True

        # Find all search result rows
        search_rows = soup.find_all('div', class_=['search-result-row', 'search-result-row '])
        print(len(search_rows))
        # Initialize a list to store the data
        data = []
        image_data = []
        sub_count = 1
        # Loop through each search result
        for row in search_rows:
            print(f'sub_count => {sub_count} out of {len(search_rows)}')
            sub_count += 1
            link = row.find('a', class_='search-title')
            
            if link and link['href']:
                link_url = link['href']
                title_text = link.get_text(strip=True)  # Get the title text
                
                # # Visit each link
                link_page_source = safe_request(link_url)
                if link_page_source:
                    page_soup = BeautifulSoup(link_page_source, 'html.parser')

                    # Check for images within the linked page
                    images = page_soup.find_all('img')
                    total_images = len(images)

                    # Count images missing alt attributes
                    total_images_missing_alt = sum(1 for img in images if not img.has_attr('alt') or img.get('alt') == "" or img.get('alt') == "..." or img.get('alt') is None)

                    # Append the data to the list
                    data.append({
                        'Title': title_text,
                        'Link': link_url,
                        'Total Images': total_images,
                        'Total Images Missing Alt': total_images_missing_alt
                    })
                    image_data.append({
                            'title': title_text,  # Include title for the first image
                            'link': link_url,
                            })
                    # Loop through the images to collect additional data for the second CSV
                    for index, img in enumerate(images):
                        img_url = img.get('src') if img.has_attr('src') else img.get('data-src') 
                        alt_text = 'Missing ALT Text' if not img.has_attr('alt') or img.get('alt') == "" or img.get('alt') == "..." or img.get('alt') is None else img.get('alt', '')

                        image_data.append({
                            'title': '',
                            'link': '',
                            'index': index + 1,  # 1-based index
                            'image_url': img_url,
                            'alt_text': alt_text })
            

        # Create a DataFrame for the first CSV and save it
        df = pd.DataFrame(data)
        df.to_csv(f'{name}_image_stats.csv', index=False)
        print(f"{name} => Data has been written to image_stats.csv.")

        # Create a DataFrame for the second CSV (image info) and save it
        df_images = pd.DataFrame(image_data)
        df_images.to_csv(f'{name}_image_details.csv', index=False)
        print(f"{name} => Image details have been written to image_details.csv.")
    else:
        print("Failed to retrieve the main page.")
    count += 1
    
# Clean up
driver.quit()