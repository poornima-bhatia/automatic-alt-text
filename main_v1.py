import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}
def safe_request_1(url):
    retries = 3
    for attempt in range(retries):
        try:
            # Use requests to check the status code first
            response = requests.get(url , headers = headers , verify=False , timeout=20)
            response.raise_for_status()
            # driver.get(url)
            time.sleep(20)  # Wait for the page to load
            print(f"{url}")
            return response.text
        except requests.exceptions.Timeout:
            print(f"{url} => Request timed out. Attempt {attempt + 1} of {retries}.")
            time.sleep(2)  # Wait before retrying
        except Exception as e:
            print(f"{url} => An error occurred: {e}")
            return None
    print(f"{url} => Failed after {retries} attempts.")
    return None

def images(sheet_name):
    df = pd.read_excel('sectors_data_x.xlsx', sheet_name=sheet_name)
    total_images_src = []
    total_images_alt_missing_text = []
    image_data = []
    for index, row in df.iterrows():
        title = row['title']
        link = row['link']
        image_data.append({
                'title': title,
                'link': link,
            })
        response = safe_request_1(link)
        if response:
            soup = BeautifulSoup(response, 'html.parser')
            images = soup.find_all('img')
            total_images_src.append(len(images))
            total_images_alt_missing_text.append(sum(1 for img in images if not img.has_attr('alt') or img['alt'] in ["", "..."]))
            for img in images:
                img_url = img.get('src') or img.get('data-src') or img.get('srcset') or img.get('data-srcset')
                alt_text = 'Missing ALT Text' if not img.has_attr('alt') or img.get('alt') == "" or img.get('alt') == "..." or img.get('alt') is None else img.get('alt', 'Missing ALT Text')

                # Print image details
                if img_url:
                    image_data.append({
                        'title': '',
                        'link': '',
                        'image_src': img_url,
                        'image_alt_text': alt_text
                    })
        else:
            total_images_src.append(0)
            total_images_alt_missing_text.append(0)

    if image_data:
        image_df = pd.DataFrame(image_data)

    df['total_images_src'] = total_images_src
    df['total_images_alt_missing_text'] = total_images_alt_missing_text
    try:
        with pd.ExcelWriter('sectors_data_x.xlsx', engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            if image_data:
                image_df = pd.DataFrame(image_data)
                image_df.to_excel(writer, sheet_name=f"{sheet_name}_img_details", index=False)
    except PermissionError:
        print("Permission error: Ensure the Excel file is not open in another program.")
    except Exception as e:
        print(f"Error writing to Excel file: {e}")

excel_file = pd.ExcelFile('sectors_data_x.xlsx')
sheet_names = excel_file.sheet_names
print(sheet_names)
for sheet_name in sheet_names:
    images(sheet_name)