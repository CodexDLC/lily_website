import json
import os

BASE_DIR = r'c:\install\projects\clients\lily_website\src\lily_backend\system\fixtures\catalog\service'
FILES = [
    'services_brows_lashes.json',
    'services_cosmetology.json',
    'services_depilation.json',
    'services_hair.json',
    'services_massage.json',
    'services_nails.json',
    'services_pedicure.json'
]

# Correct prices for cosmetology (based on screenshot)
COSMETOLOGY_PRICES = {
    "Комбинированная чистка лица": 50.0,
    "Карбокситерапия": 40.0,
    "Криотерапия": 35.0,
}

def clean_file(filename):
    path = os.path.join(BASE_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for entry in data:
        if 'fields' in entry:
            # Remove masters
            if 'masters' in entry['fields']:
                del entry['fields']['masters']
            
            # Fix Cosmetology prices
            if filename == 'services_cosmetology.json':
                name = entry['fields'].get('name_ru')
                if name in COSMETOLOGY_PRICES:
                    entry['fields']['price'] = COSMETOLOGY_PRICES[name]

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Cleaned {filename}")

if __name__ == "__main__":
    for f in FILES:
        clean_file(f)
