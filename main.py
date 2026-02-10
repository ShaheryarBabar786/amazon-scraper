"""Main entry point for the Amazon scraper"""

from scraper import AmazonScraper

def main():
    """Main function to run the scraper"""
    
    url = input("\nEnter Amazon product URL: ").strip()
    
    if not url:
        print("No URL provided. Exiting.")
        return
    
    # Create scraper instance
    scraper = AmazonScraper()
    
    # Scrape product
    product = scraper.scrape(url)
    
    if product:
        product.display()

        product.to_json('product_data.json')
        print(f"\n Data saved to product_data.json")
    else:
        print("\n Failed to scrape product.")

if __name__ == "__main__":
    main()