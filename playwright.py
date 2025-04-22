import json
import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SESSION_FILE = "session.json"
OUTPUT_FILE = "products.json"
BASE_URL = "https://hiring.idenhq.com/"
USERNAME = "prernakulk12@gmail.com"
PASSWORD = "qHXbka3C"

# Constants for extraction
MAX_RETRY_ATTEMPTS = 5
EXPECTED_PRODUCT_COUNT = 10000
SCROLL_PAUSE_TIME = 1000  # milliseconds
EXTRACTION_BATCH_SIZE = 200  # Check for new products after this many scrolls

def load_or_authenticate(playwright):
    browser = playwright.chromium.launch(headless=False)
    
    if os.path.exists(SESSION_FILE) and os.path.getsize(SESSION_FILE) > 0:
        try:
            context = browser.new_context(storage_state=SESSION_FILE)
            page = context.new_page()
            page.goto(BASE_URL)
            
            # Check if we're already logged in by looking for a dashboard element
            try:
                if page.query_selector("text=Dashboard", timeout=5000):
                    print("✅ Using existing session")
                    return context, page
            except:
                print("⚠️ Session expired. Re-authenticating...")
                # Continue to authentication
        except Exception:
            print("⚠️ Session file corrupted. Re-authenticating...")

    # Create a new context for authentication
    if 'context' in locals():
        context.close()
    context = browser.new_context()
    page = context.new_page()
    
    # Go to login page and authenticate
    page.goto(BASE_URL)
    authenticate(page)
    
    # Save the session for future use
    context.storage_state(path=SESSION_FILE)
    print("✅ New session saved")
    return context, page

def authenticate(page):
    try:
        print("Authenticating...")
        
        # Wait for login form and fill credentials
        page.wait_for_selector('#email', timeout=10000)
        page.fill('#email', USERNAME)
        page.fill('#password', PASSWORD)
        
        page.wait_for_timeout(1000)  # Let autofill finish if any
        
        # Try different methods to click the login button
        try:
            page.get_by_role("button", name="Sign In").click()
        except:
            try:
                page.get_by_role("button", name="Login").click()
            except:
                try:
                    page.locator('button[type="submit"]').click()
                except:
                    # Last resort - try to find any button that might be for login
                    buttons = page.query_selector_all('button')
                    for button in buttons:
                        if "login" in button.inner_text().lower() or "sign in" in button.inner_text().lower():
                            button.click()
                            break
        
        # Wait for dashboard to confirm successful login
        page.wait_for_selector("text=Dashboard", timeout=10000)
        print("✅ Authentication successful")
        
    except PlaywrightTimeoutError as e:
        print(f"❌ Login failed: {e}")
        raise e

def click_launch_challenge_button(page):
    try:
        print("Clicking Launch Challenge button...")
        # Click the 'Launch Challenge' button
        page.get_by_role("button", name="Launch Challenge").click()
        page.wait_for_timeout(3000)  # wait for the page to load after clicking
        print("✅ Challenge launched")
    except PlaywrightTimeoutError as e:
        print(f"❌ Failed to click Launch Challenge button: {e}")
        raise e

def navigate_to_product_table(page):
    try:
        print("Navigating to product table...")
        
        # Navigate to the 'Tools' tab
        print("- Clicking Tools tab")
        page.get_by_role("tab", name="Tools").click()
        page.wait_for_timeout(1000)
        
        print("- Clicking Open Data Tools")
        page.get_by_role("button", name="Open Data Tools").click()
        page.wait_for_timeout(1000)

        # Navigate to the 'Data' tab
        print("- Clicking Data tab")
        page.get_by_role("tab", name="Data").click()
        page.wait_for_timeout(1000)
        
        # Click the 'Inventory' button
        print("- Clicking Open Inventory")
        page.get_by_role("button", name="Open Inventory").click()
        page.wait_for_timeout(1000)

        # Click the 'Inventory' tab selector
        print("- Clicking Select Inventory Tab")
        page.get_by_role("button", name="Select Inventory Tab").click()
        page.wait_for_timeout(1000)

        # Wait for the 'Products' tab and click it
        print("- Clicking Products tab")
        page.wait_for_selector("text=Products", timeout=5000)
        page.get_by_role("tab", name="Products").click()
        page.wait_for_timeout(1000)

        # Wait for the table loading button
        print("- Clicking Load Product Table")
        page.wait_for_selector("text=Load Product Table", timeout=5000)
        page.get_by_role("button", name="Load Product Table").click()
        page.wait_for_timeout(5000)  # Wait longer for the table to load
        
        print("✅ Successfully navigated to product table")

    except PlaywrightTimeoutError as e:
        print(f"❌ Failed to navigate to product table: {e}")
        raise e

# Initialize the JSON file with an empty list
def initialize_json_file():
    with open(OUTPUT_FILE, "w") as f:
        json.dump([], f)
    print(f"✅ Initialized {OUTPUT_FILE} with empty array")

# Save a single product to the JSON file
def save_product_to_json(product, index):
    try:
        # Read current data
        with open(OUTPUT_FILE, "r") as f:
            data = json.load(f)
        
        # Add new product
        data.append(product)
        
        # Write updated data back
        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"  ✓ Saved product #{index} (ID: {product['id']}): {product['name']} - Total: {len(data)}")
        return len(data)  # Return the total count
    except Exception as e:
        print(f"⚠️ Error saving product #{index} to JSON: {e}")
        return -1

# Add a function to save products in batch to reduce file I/O
def save_products_batch(products):
    try:
        # Read current data
        with open(OUTPUT_FILE, "r") as f:
            data = json.load(f)
        
        # Add new products
        original_count = len(data)
        data.extend(products)
        
        # Write updated data back
        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"  ✓ Batch saved {len(products)} products. Total: {len(data)}")
        return len(data)  # Return the total count
    except Exception as e:
        print(f"⚠️ Error saving batch to JSON: {e}")
        return -1

# Helper function for safer text extraction
def extract_text_after(text, marker):
    if marker in text:
        parts = text.split(marker, 1)
        if len(parts) > 1:
            return parts[1].strip()
    return ""

def check_for_pagination_controls(page):
    """Check if there's pagination and handle it"""
    pagination_selectors = [
        "button:has-text('Next')",
        "a:has-text('Next')",
        ".pagination",
        "button:has-text('Show More')",
        "button:has-text('Load More')"
    ]
    
    for selector in pagination_selectors:
        element = page.query_selector(selector)
        if element and element.is_visible():
            print(f"Found pagination control: {selector}")
            return element
    
    return None

def parse_product_card(card, product_ids, total_products):
    """Parse a single product card and extract information"""
    try:
        product = {}
        card_text = card.inner_text()
        
        # Check if this looks like a product card
        if "ID:" not in card_text and "Price:" not in card_text and "Stock:" not in card_text:
            return None
        
        # Extract ID first to check if we've already processed this product
        id_match = extract_text_after(card_text, "ID:")
        product_id = id_match.split("\n")[0].strip() if id_match else f"unknown-{total_products}"
        
        # Skip if we've already processed this ID (avoid duplicates)
        if product_id in product_ids and product_id != f"unknown-{total_products}":
            return None
        
        product_ids.add(product_id)
        product["id"] = product_id
        
        # Extract name (try different approaches)
        name_element = card.query_selector("h3, h2, h4")
        if name_element:
            product["name"] = name_element.inner_text().strip()
        else:
            # Try to get the first line or first bold text
            lines = card_text.split('\n')
            product["name"] = lines[0].strip() if lines else "Unknown Product"
        
        # Extract category
        category_element = card.query_selector("span.category, span.product-category, span")
        product["category"] = category_element.inner_text().strip() if category_element else "N/A"
        
        # Extract description
        desc_match = extract_text_after(card_text, "Description:")
        product["description"] = desc_match.split("\n")[0].strip() if desc_match else "N/A"
        
        # Extract rating
        rating_match = extract_text_after(card_text, "Rating:")
        if rating_match:
            try:
                product["rating"] = float(rating_match.split("\n")[0].strip())
            except ValueError:
                product["rating"] = 0.0
        else:
            product["rating"] = 0.0
        
        # Extract price
        price_match = extract_text_after(card_text, "Price:")
        if price_match:
            try:
                price_text = price_match.split("\n")[0].strip().replace("$", "").replace(",", "")
                product["price"] = float(price_text)
            except ValueError:
                product["price"] = 0.0
        else:
            product["price"] = 0.0
        
        # Extract stock
        stock_match = extract_text_after(card_text, "Stock:")
        if stock_match:
            try:
                product["stock"] = int(stock_match.split("\n")[0].strip())
            except ValueError:
                product["stock"] = 0
        else:
            product["stock"] = 0
        
        # Extract size
        size_match = extract_text_after(card_text, "Size:")
        product["size"] = size_match.split("\n")[0].strip() if size_match else "N/A"
        
        # Extract manufacturer
        manuf_match = extract_text_after(card_text, "Manufacturer:")
        product["manufacturer"] = manuf_match.split("\n")[0].strip() if manuf_match else "N/A"
        
        # Extract updated timestamp
        updated_match = extract_text_after(card_text, "Updated:")
        product["updated"] = updated_match.split("\n")[0].strip() if updated_match else "N/A"
        
        return product
        
    except Exception as e:
        print(f"⚠️ Failed to parse a product card: {str(e)}")
        return None

def extract_product_data(page):
    # Initialize the JSON file before starting extraction
    initialize_json_file()
    
    total_products = 0
    product_ids = set()  # To track duplicate products
    scroll_no_new_product_count = 0  # Track consecutive scrolls with no new products
    
    # First, check for pagination controls
    pagination_element = check_for_pagination_controls(page)
    
    try:
        print("Determining extraction strategy...")
        # Wait for product cards to load
        selectors = [
            "div.product-card", 
            "div.inventory-card", 
            "div[data-product-id]", 
            "div:has-text('ID: ')"
        ]
        
        # Try each selector until one works
        effective_selector = None
        for selector in selectors:
            try:
                print(f"Trying selector: {selector}")
                if page.wait_for_selector(selector, timeout=3000):
                    print(f"Found products with selector: {selector}")
                    effective_selector = selector
                    break
            except:
                continue
                
        if not effective_selector:
            print("⚠️ Warning: No product cards found with standard selectors.")
            print("Using generic div selector as fallback...")
            effective_selector = "div:has-text('ID: ')"
            
        # Determine if we should use pagination or infinite scroll
        if pagination_element:
            print("Using pagination strategy")
            extraction_strategy = "pagination"
        else:
            print("Using infinite scroll strategy")
            extraction_strategy = "infinite_scroll"
            
        # Process batch of products for better memory management
        def process_visible_products():
            nonlocal total_products
            
            batch_products = []
            # Get all cards that are currently visible
            cards = page.query_selector_all(effective_selector)
            print(f"Found {len(cards)} potential product cards")
            
            new_products_in_batch = 0
            for card in cards:
                product = parse_product_card(card, product_ids, total_products)
                if product:
                    batch_products.append(product)
                    new_products_in_batch += 1
            
            # Save the batch if we found new products
            if batch_products:
                save_products_batch(batch_products)
                total_products += new_products_in_batch
                print(f"Processed batch: {new_products_in_batch} new products. Total: {total_products}")
            
            return new_products_in_batch
        
        # Initial extraction of visible products
        print("Starting initial extraction...")
        new_products = process_visible_products()
        
        if extraction_strategy == "pagination":
            # Handle pagination approach
            page_number = 1
            max_page_attempts = 50  # Protect against infinite loops
            
            while page_number < max_page_attempts:
                page_number += 1
                print(f"\nAttempting to navigate to page {page_number}...")
                
                # Try different pagination controls
                next_button = page.query_selector("button:has-text('Next')")
                if not next_button:
                    next_button = page.query_selector("a:has-text('Next')")
                if not next_button:
                    next_button = page.query_selector(".pagination li:last-child a")
                
                if next_button and next_button.is_visible() and not next_button.is_disabled():
                    next_button.click()
                    print(f"Clicked next button to page {page_number}")
                    page.wait_for_timeout(2000)  # Wait for page to load
                    
                    # Extract products on this page
                    new_products = process_visible_products()
                    
                    if new_products == 0:
                        print(f"No new products found on page {page_number}. Trying one more page...")
                        # Try one more page before giving up
                        if page_number >= max_page_attempts - 1:
                            print("Reached maximum pagination attempts. Stopping.")
                            break
                    
                else:
                    print("No more pagination controls found. Reached last page.")
                    break
                    
                if total_products >= EXPECTED_PRODUCT_COUNT:
                    print(f"Reached expected product count ({EXPECTED_PRODUCT_COUNT}). Stopping pagination.")
                    break
        else:
            # Handle infinite scroll approach
            print("\nUsing enhanced infinite scroll extraction...")
            max_scroll_attempts = 400  # Increased from original
            no_new_products_threshold = 10  # Stop after this many consecutive scrolls with no new products
            scroll_attempts = 0
            
            # Alternate between different scrolling techniques
            while scroll_attempts < max_scroll_attempts:
                scroll_attempts += 1
                
                # Different scrolling techniques to try
                if scroll_attempts % 4 == 0:
                    # Fast scroll to bottom
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                elif scroll_attempts % 4 == 1:
                    # Incremental scroll
                    page.evaluate("window.scrollBy(0, 800)")
                elif scroll_attempts % 4 == 2:
                    # Middle scroll
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                else:
                    # Slow scroll
                    for _ in range(5):
                        page.evaluate("window.scrollBy(0, 200)")
                        page.wait_for_timeout(100)
                
                # Wait for content to load
                page.wait_for_timeout(SCROLL_PAUSE_TIME)
                
                # Try to find the "Load more" button if it exists
                load_more_button = page.query_selector("button:has-text('Load More'), button:has-text('Show More')")
                if load_more_button and load_more_button.is_visible():
                    print("Found 'Load More' button - clicking it")
                    load_more_button.click()
                    page.wait_for_timeout(2000)  # Wait longer after clicking
                
                # Check for new products periodically
                if scroll_attempts % 5 == 0:
                    prev_total = total_products
                    new_products = process_visible_products()
                    
                    # Track consecutive scrolls with no new products
                    if new_products == 0:
                        scroll_no_new_product_count += 1
                        print(f"No new products found after scroll #{scroll_attempts}. ({scroll_no_new_product_count}/{no_new_products_threshold})")
                        
                        if scroll_no_new_product_count >= no_new_products_threshold:
                            print(f"No new products found after {no_new_products_threshold} consecutive scrolls.")
                            
                            # Try more aggressive scrolling as a last resort
                            for desperate_attempt in range(5):
                                print(f"Desperate scroll attempt #{desperate_attempt+1}/5...")
                                # Go back to top and then bottom
                                page.evaluate("window.scrollTo(0, 0)")
                                page.wait_for_timeout(1000)
                                page.evaluate("window.scrollTo(0, document.body.scrollHeight * 2)")
                                page.wait_for_timeout(2000)
                                
                                # Check if we got new products
                                new_desperate_products = process_visible_products()
                                if new_desperate_products > 0:
                                    print(f"Success! Found {new_desperate_products} new products with desperate scrolling.")
                                    scroll_no_new_product_count = 0
                                    break
                            
                            # If still no products after desperate attempts, stop
                            if scroll_no_new_product_count >= no_new_products_threshold:
                                print("Stopping scroll extraction - no more products found.")
                                break
                    else:
                        # Reset counter when we find new products
                        scroll_no_new_product_count = 0
                
                # Check if we've reached the expected count
                if total_products >= EXPECTED_PRODUCT_COUNT:
                    print(f"Reached expected product count ({EXPECTED_PRODUCT_COUNT}). Stopping extraction.")
                    break
                    
                # Give progress updates
                if scroll_attempts % 10 == 0:
                    print(f"Scroll progress: {scroll_attempts}/{max_scroll_attempts}, Products: {total_products}/{EXPECTED_PRODUCT_COUNT}")
        
        # Try using "click to load more" button if available
        try_load_more_button(page, product_ids, total_products, process_visible_products)
        
        # Final attempt to find any missed products
        print("\nFinal sweep for any missed products...")
        page.evaluate("window.scrollTo(0, 0)")  # Go back to top
        page.wait_for_timeout(2000)
        final_products = process_visible_products()
        
        if final_products > 0:
            print(f"Found {final_products} additional products in final sweep.")
        
        print(f"\n🎉 Extraction complete! {total_products} products saved to {OUTPUT_FILE}")
        
        # If we didn't get the expected count, try alternative extraction
        if total_products < EXPECTED_PRODUCT_COUNT:
            print(f"\n⚠️ Only extracted {total_products}/{EXPECTED_PRODUCT_COUNT} products.")
            print("Attempting alternative extraction method...")
            
            # Try alternative extraction methods here
            additional_products = try_alternative_extraction(page, product_ids, total_products)
            if additional_products > 0:
                total_products += additional_products
                print(f"Alternative extraction found {additional_products} more products. Total: {total_products}")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
    
    return total_products

def try_load_more_button(page, product_ids, total_products, process_fn):
    """Try to find and click any 'Load More' type buttons"""
    load_more_selectors = [
        "button:has-text('Load More')",
        "button:has-text('Show More')",
        "a:has-text('Load More')",
        ".load-more",
        "button.show-more"
    ]
    
    for selector in load_more_selectors:
        try:
            load_button = page.query_selector(selector)
            if load_button and load_button.is_visible():
                click_attempts = 0
                while click_attempts < 10:  # Try clicking up to 10 times
                    print(f"Clicking '{selector}' button...")
                    load_button.click()
                    page.wait_for_timeout(2000)
                    
                    # Process any new products
                    new_products = process_fn()
                    if new_products == 0:
                        click_attempts += 1
                    else:
                        click_attempts = 0  # Reset if we found new products
                    
                    # Check if the button is still available
                    load_button = page.query_selector(selector)
                    if not load_button or not load_button.is_visible():
                        print(f"'{selector}' button no longer available")
                        break
                        
                    if click_attempts >= 3:
                        print(f"No new products after 3 clicks of '{selector}'. Moving on.")
                        break
        except Exception as e:
            print(f"Error interacting with '{selector}': {e}")

def try_alternative_extraction(page, product_ids, current_total):
    """Try alternative extraction methods when standard methods fail"""
    print("Attempting API/Network request extraction...")
    
    # Monitor network requests for any product data
    product_data_found = False
    additional_products = 0
    
    # Try inspecting network requests
    try:
        # Go back to beginning and enable request interception
        page.goto(page.url)
        page.wait_for_timeout(3000)
        
        # Inject JavaScript to detect and extract product data from network
        script_result = page.evaluate("""() => {
            return new Promise((resolve) => {
                let products = [];
                let originalFetch = window.fetch;
                let originalXHR = window.XMLHttpRequest.prototype.open;
                
                // Intercept fetch
                window.fetch = async function(...args) {
                    const response = await originalFetch.apply(this, args);
                    try {
                        const url = args[0];
                        if (url.toString().includes('product') || url.toString().includes('inventory')) {
                            const clonedResponse = response.clone();
                            const data = await clonedResponse.json();
                            if (Array.isArray(data) && data.length > 0 && data[0].id) {
                                products = products.concat(data);
                                console.log(`Intercepted ${data.length} products via fetch`);
                            }
                        }
                    } catch (e) {}
                    return response;
                };
                
                // Intercept XHR
                window.XMLHttpRequest.prototype.open = function(...args) {
                    const url = args[1].toString();
                    if (url.includes('product') || url.includes('inventory')) {
                        this.addEventListener('load', function() {
                            try {
                                const data = JSON.parse(this.responseText);
                                if (Array.isArray(data) && data.length > 0 && data[0].id) {
                                    products = products.concat(data);
                                    console.log(`Intercepted ${data.length} products via XHR`);
                                }
                            } catch (e) {}
                        });
                    }
                    return originalXHR.apply(this, args);
                };
                
                // Trigger potential API calls by interacting with the page
                setTimeout(() => {
                    // Click various controls to trigger data loading
                    document.querySelectorAll('button').forEach(button => {
                        if (button.innerText.includes('Load') || 
                            button.innerText.includes('Show') || 
                            button.innerText.includes('Product')) {
                            button.click();
                        }
                    });
                    
                    // Scroll to trigger lazy loading
                    window.scrollTo(0, document.body.scrollHeight);
                    
                    // Give time for requests to complete
                    setTimeout(() => {
                        resolve(products);
                    }, 5000);
                }, 1000);
            });
        }""")
        
        if script_result and len(script_result) > 0:
            print(f"Found {len(script_result)} products via network interception!")
            
            # Process these products
            new_products = []
            for product_data in script_result:
                if not isinstance(product_data, dict) or 'id' not in product_data:
                    continue
                    
                product_id = str(product_data['id'])
                if product_id in product_ids:
                    continue
                    
                product_ids.add(product_id)
                new_products.append(product_data)
            
            if new_products:
                save_products_batch(new_products)
                additional_products = len(new_products)
                print(f"Successfully extracted {additional_products} additional products via network interception")
    
    except Exception as e:
        print(f"Alternative extraction failed: {e}")
    
    return additional_products
                
def main():
    try:
        with sync_playwright() as playwright:
            context, page = load_or_authenticate(playwright)
            
            # Set a generous timeout
            page.set_default_timeout(30000)
            
            click_launch_challenge_button(page)
            navigate_to_product_table(page)
            
            # Start the extraction process
            total_products = extract_product_data(page)
            
            if total_products < EXPECTED_PRODUCT_COUNT:
                print(f"\n⚠️ Warning: Only extracted {total_products} out of {EXPECTED_PRODUCT_COUNT} expected products.")
                print("Trying one more time with different approach...")
                
                # Second attempt with different approach
                # Clear product IDs set and reinitialize
                navigate_to_product_table(page)  # Reload the products page
                # Try with headless mode off to ensure all rendering occurs
                total_products = extract_product_data(page)
            
            print(f"\n✅ Script completed. Saved {total_products} products to {OUTPUT_FILE}")
            context.close()
    except Exception as e:
        print(f"❌ Script failed with error: {e}")

if __name__ == "__main__":
    main()