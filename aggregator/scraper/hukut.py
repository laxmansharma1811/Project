def scrape_products(query, max_products=5):
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException
    import time
    import re

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.hukut.com/")
    time.sleep(2)

    # Search for the query
    search_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Search']")
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    time.sleep(2)

    # Collect the first `max_products` product links
    product_links = []
    all_links = driver.find_elements(By.CSS_SELECTOR, "div.peer.h-full.w-full a")
    for link in all_links[:max_products]:
        href = link.get_attribute("href")
        if href:
            product_links.append(href)

    scraped_products = []

    # Visit each product link and scrape the details
    for href in product_links:
        try:
            driver.get(href)
            time.sleep(2)

            product_data = {}
            product_data['Product Link'] = driver.current_url
            product_data['Product Name'] = driver.find_element(By.CSS_SELECTOR, "h1.text-md").text

            price_element = driver.find_element(By.XPATH, "//div[contains(@class, 'font-semibold') and contains(text(), 'रु')]")
            product_data['Product Price'] = price_element.text

            img_tag = driver.find_element(By.CSS_SELECTOR, "img[aria-label='Product Image']")
            product_data['Image URL'] = img_tag.get_attribute("src")

            try:
                rating_text = driver.find_element(By.XPATH, '/html/body/div[3]/section/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div/p').text
                rating_match = re.match(r"(\d+\.\d+) \((\d+) Reviews?\)", rating_text)
                if rating_match:
                    product_data['Rating'] = rating_match.group(1)
                    product_data['Number of Ratings'] = rating_match.group(2)
            except NoSuchElementException:
                product_data['Rating'] = '0'
                product_data['Number of Ratings'] = 'No Ratings'

            try:
                spec_section = driver.find_element(By.XPATH, '/html/body/div[3]/section/section[2]/div/div/div/div')
                product_data['Specifications'] = spec_section.text.replace('\n', ' | ')
            except NoSuchElementException:
                product_data['Specifications'] = 'No specifications available'

            scraped_products.append(product_data)

        except Exception as e:
            print(f"Error scraping product from {href}: {e}")
            continue

    driver.quit()
    return scraped_products
