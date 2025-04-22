# 🛠️ Playwright Product Scraper Bot


A Python-based web automation script using **Playwright** that logs into a private product dashboard, navigates a series of nested UI tabs, and extracts structured product data into a JSON file.

---

## 🚀 Features

- 🔐 **Session Management**  
  Automatically saves and reuses login sessions to avoid repeated authentication.

- 🧭 **Hidden UI Navigation**  
  Programmatically clicks through:  
  `Launch Challenge` → `Tools` → `Open Data Tools` → `Open Inventory` → `Select Inventory Tab` → `Load Product Table`.

- 📦 **Dynamic Data Capture**  
  Scrapes all visible product cards from the dynamically loading product dashboard.

- 💾 **Data Export**  
  Stores all product information in a clean JSON format for further analysis.

---

## 📁 Files Included

- `playwright.py` – Main script to run the product scraper.
- `session.json` – Auto-generated Playwright session data (after first login).
- `products.json` – Exported product data.
- `requirements.txt` – Python dependencies for Playwright.

---

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash

git clone https://github.com/Prerna-lily/playwrightbot.git
cd playwrightbot
pip install -r requirements.txt
playwright install

python playwright.py

**Output structure:**

The products.json file will contain data like this:

json

[
  {
    "id": "0",
    "name": "Product Inventory",
    "category": "20",
    "description": "A premium, high-quality electronics product. The Essential Electronics Package is designed for maximum performance and user satisfaction.",
    "rating": 1.7,
    "price": 24.16,
    "stock": 739,
    "size": "32\u00d740\u00d729 cm",
    "manufacturer": "ValueCreators",
    "updated": "4/15/2025"
  }
  ...
]
