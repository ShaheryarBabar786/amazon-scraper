"""Main Amazon scraper module"""

import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin

from config import HEADERS, TIMEOUT, BASE_URL, MAX_IMAGES
from models import Product, SellerInfo
from utils import (
    clean_text, extract_currency, extract_from_json_script,
    get_seller_id_from_url, clean_seller_name, get_live_exchange_rate
)


class AmazonScraper:
    """Amazon product scraper"""
    
    def __init__(self):
        self.headers = HEADERS
        self.timeout = TIMEOUT
        self.base_url = BASE_URL
    
    def scrape(self, url):
        """Scrape product information from Amazon URL"""
        try:
            print(f"Scraping: {url}")
            
            # Fetch page
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract product information
            title = self._extract_title(soup)
            brand = self._extract_brand(soup)
            price, currency_symbol = self._extract_price(soup)
            rating = self._extract_rating(soup)
            reviews = self._extract_reviews(soup)
            images = self._extract_images(soup)
            description = self._extract_description(soup)
            seller_info = self._extract_seller_details(soup, url)
            
            # Create product object
            product = Product(
                title=title,
                brand=brand,
                price=f"{currency_symbol}{price}" if price != "Not found" else "Not found",
                rating=f"{rating}/5" if rating != "Not found" else "Not found",
                reviews=reviews,
                description=description,
                images=images[:MAX_IMAGES],
                seller_info=seller_info
            )
            
            return product
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def _extract_title(self, soup):
        """Extract product title"""
        title_elem = soup.find('span', id='productTitle')
        return clean_text(title_elem.get_text()) if title_elem else "Not found"
    
    def _extract_brand(self, soup):
        """Extract product brand"""
        brand_elem = soup.find('a', id='bylineInfo')
        return clean_text(brand_elem.get_text()) if brand_elem else "Not found"
    
    def _extract_price(self, soup):
        """Extract product price and currency"""
        price_div = soup.find('div', class_='a-section a-spacing-none aok-align-center aok-relative')
        if price_div:
            hidden_price = price_div.find('span', class_='aok-offscreen')
            if hidden_price:
                price_text = hidden_price.get_text(strip=True)
                currency_symbol, price = extract_currency(price_text)
                if price != "Not found":
                    return self._handle_currency_conversion(price, currency_symbol)

        main_price = soup.find('span', class_='a-price aok-align-center reinventPricePriceToPayMargin priceToPay')
        if main_price:
            currency_elem = main_price.find('span', class_='a-price-symbol')
            currency_symbol = currency_elem.get_text(strip=True) if currency_elem else "$"
            
            whole_part = main_price.find('span', class_='a-price-whole')
            fraction_part = main_price.find('span', class_='a-price-fraction')
            
            if whole_part and fraction_part:
                whole = whole_part.get_text(strip=True).replace(',', '')
                if '.' in whole:
                    whole = whole.replace('.', '')
                fraction = fraction_part.get_text(strip=True)
                price = f"{whole}.{fraction}"
                return self._handle_currency_conversion(price, currency_symbol)
        
        return "Not found", "$"
    
    def _handle_currency_conversion(self, price, currency_symbol):
        """Handle currency conversion if needed"""
        if price != "Not found" and currency_symbol in ["PKR", "₨", "Rs"]:
            try:
                pkr_to_usd_rate = get_live_exchange_rate()
                price_float = float(price)
                usd_price = price_float * pkr_to_usd_rate
                price = f"{usd_price:.2f}"
                currency_symbol = "$"
            except:
                pass
        return price, currency_symbol
    
    def _extract_rating(self, soup):
        """Extract product rating"""
        rating_elem = soup.find('span', class_='a-icon-alt')
        rating_text = rating_elem.get_text(strip=True) if rating_elem else "Not found"
        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
        return rating_match.group(1) if rating_match else "Not found"
    
    def _extract_reviews(self, soup):
        """Extract number of reviews"""
        reviews_elem = soup.find('span', id='acrCustomerReviewText')
        return clean_text(reviews_elem.get_text()) if reviews_elem else "Not found"
    
    def _extract_images(self, soup):
        """Extract product images"""
        images = []
        image_selectors = [
            '#landingImage',
            '[data-old-hires]',
            '.a-dynamic-image',
            'img[data-a-dynamic-image]',
            '#imgTagWrapperId img'
        ]
        
        for selector in image_selectors:
            img_elements = soup.select(selector)
            for img in img_elements:
                src = img.get('src') or img.get('data-src') or img.get('data-old-hires')
                
                if not src and 'data-a-dynamic-image' in img.attrs:
                    try:
                        img_data = json.loads(img['data-a-dynamic-image'])
                        if img_data:
                            src = list(img_data.keys())[0]
                    except:
                        pass
                
                if src and 'http' in src and src not in images:
                    if '._SL' in src:
                        base_url = src.split('._SL')[0]
                        high_res = f"{base_url}._SL1500_"
                        images.append(high_res)
                    else:
                        images.append(src)
        
        return list(dict.fromkeys(images))
    
    def _extract_description(self, soup):
        """Extract product description"""
        desc_elem = soup.find('div', id='productDescription')
        description = desc_elem.get_text(strip=True) if desc_elem else "Not found"
        return description[:500]
    
    def _extract_seller_details(self, soup, product_url):
        """Extract seller information"""
        seller_info = SellerInfo()
        
        try:
            # Check for FBA
            fba_elements = soup.find_all(string=re.compile(r'fulfilled.*amazon|amazon.*fulfilled', re.I))
            if fba_elements:
                seller_info.is_fulfilled_by_amazon = True
            
            # Check for Amazon's Choice or other indicators
            if soup.find('span', {'class': 'ac-badge-rectangle'}):
                amazon_seller = soup.find('span', string=re.compile(r'^Amazon\.com$', re.I))
                if amazon_seller:
                    seller_info.seller_name = "Amazon.com"
                    seller_info.sold_by = "Amazon.com"
                    seller_info.shipped_by = "Amazon.com"
                    seller_info.is_amazon = True
            
            # Extract from various sections
            self._extract_seller_from_buybox(soup, seller_info)
            self._extract_seller_from_links(soup, seller_info)
            self._extract_seller_feedback(soup, seller_info)
            
            # Check detailed seller information section
            details_section = soup.find('div', {'id': 'detailBullets_feature_div'})
            if details_section:
                bullets = details_section.find_all('li')
                for bullet in bullets:
                    text = bullet.get_text(strip=True)
                    if 'Sold by:' in text:
                        seller_match = re.search(r'Sold by:\s*(.+)', text)
                        if seller_match:
                            seller_info.sold_by = seller_match.group(1).strip()
                            if seller_info.seller_name == "Not found":
                                seller_info.seller_name = seller_info.sold_by
            
            # Scrape seller page if available
            if seller_info.seller_store_url != "Not found" and not seller_info.is_amazon:
                self._scrape_seller_page(seller_info)
            
            # Clean seller name
            seller_info.seller_name = clean_seller_name(seller_info.seller_name)
            seller_info.sold_by = clean_seller_name(seller_info.sold_by)
            
        except Exception as e:
            print(f"Error extracting seller details: {e}")
        
        return seller_info
    
    def _extract_seller_from_buybox(self, soup, seller_info):
        """Extract seller info from buybox section"""
        seller_section = (soup.find('div', {'id': 'merchant-info'}) or 
                         soup.find('div', {'id': 'sellerProfileTriggerId'}) or 
                         soup.find('div', {'id': 'availability'}))
        
        if seller_section:
            seller_text = seller_section.get_text(' ', strip=True)
            
            # Extract sold by
            sold_by_match = re.search(r'sold by\s*(.+?)(?:\s*and|$)', seller_text, re.I)
            if sold_by_match:
                seller_name = sold_by_match.group(1).strip()
                seller_name = re.sub(r'\((.*?)\)', '', seller_name).strip()
                seller_info.sold_by = seller_name
                seller_info.seller_name = seller_name
                seller_info.is_amazon = 'amazon' in seller_name.lower()
            
            # Extract shipped by
            shipped_by_match = re.search(r'shipped by\s*(.+?)(?:\s*and|$)', seller_text, re.I)
            if shipped_by_match:
                seller_info.shipped_by = shipped_by_match.group(1).strip()
    
    def _extract_seller_from_links(self, soup, seller_info):
        """Extract seller info from links"""
        # Seller profile link
        seller_link = soup.find('a', {'id': 'sellerProfileTriggerId'})
        if seller_link:
            if seller_link.get_text(strip=True):
                seller_name = seller_link.get_text(strip=True)
                seller_name = re.sub(r'^\s*by\s*', '', seller_name, flags=re.I).strip()
                if seller_info.seller_name == "Not found":
                    seller_info.seller_name = seller_name
                    seller_info.sold_by = seller_name
            
            if 'href' in seller_link.attrs:
                seller_url = urljoin(self.base_url, seller_link['href'])
                seller_info.seller_store_url = seller_url
                seller_info.seller_id = get_seller_id_from_url(seller_url)
        
        # Brand/store link
        store_link = soup.find('a', id='bylineInfo')
        if store_link:
            store_text = store_link.get_text(strip=True)
            if 'Visit the' in store_text and 'Store' in store_text:
                store_name = store_text.replace('Visit the', '').replace('Store', '').strip()
                if store_name and seller_info.seller_name == "Not found":
                    seller_info.seller_name = store_name
            
            if 'href' in store_link.attrs:
                store_url = urljoin(self.base_url, store_link['href'])
                if seller_info.seller_store_url == "Not found":
                    seller_info.seller_store_url = store_url
    
    def _extract_seller_feedback(self, soup, seller_info):
        """Extract seller feedback"""
        feedback_link = soup.find('a', {'href': re.compile(r'feedback')})
        if feedback_link:
            feedback_text = feedback_link.get_text(strip=True)
            rating_match = re.search(r'(\d+\.?\d*)\s*out of', feedback_text)
            if rating_match:
                seller_info.seller_rating = rating_match.group(1)
            
            feedback_match = re.search(r'(\d+[\d,]*)', feedback_text)
            if feedback_match:
                seller_info.seller_reviews = feedback_match.group(1)

    def _scrape_seller_page(self, seller_info):

        try:            
            response = requests.get(
                seller_info.seller_store_url, 
                headers=self.headers, 
                timeout=self.timeout
            )
            
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Get all script tags with rating data
                scripts = soup.find_all('script', type='a-state')                
                script_data_list = []
                for i, script in enumerate(scripts):
                    if script.string:
                        script_content = script.string.strip()
                        # Check if this contains rating data
                        if 'ratingCount' in script_content and 'star5' in script_content:
                            try:
                                # Try to parse as JSON
                                data = json.loads(script_content)
                                script_data_list.append((i+1, data))
                            except json.JSONDecodeError:
                                print(f"  Script {i+1} is not valid JSON")

                twelve_month_data = None
                lifetime_data = None
                
                for script_num, data in script_data_list:
                    rating_count = data.get('ratingCount', 0)
                    star5 = data.get('star5', 0)
                                
                if not twelve_month_data and script_data_list:
                    # Find data with ratingCount (12-month)
                    for script_num, data in script_data_list:
                        rating_count = data.get('ratingCount', 0)
                        if 400 <= rating_count <= 500:  
                            twelve_month_data = data
                            break
                
                if not lifetime_data and script_data_list:
                    max_data = max(script_data_list, key=lambda x: x[1].get('ratingCount', 0))
                    if max_data[1].get('ratingCount', 0) > 500:
                        lifetime_data = max_data[1]

                if twelve_month_data:
                    if 'ratingCount' in twelve_month_data:
                        seller_info.seller_reviews = str(twelve_month_data['ratingCount'])
                    
                    if 'star5' in twelve_month_data:
                        star5_percent = twelve_month_data.get('star5', 0)
                        star4_percent = twelve_month_data.get('star4', 0)
                        star3_percent = twelve_month_data.get('star3', 0)
                        star2_percent = twelve_month_data.get('star2', 0)
                        star1_percent = twelve_month_data.get('star1', 0)
                        
                        
                        weighted_sum = (star5_percent * 5 + 
                                       star4_percent * 4 + 
                                       star3_percent * 3 + 
                                       star2_percent * 2 + 
                                       star1_percent * 1)
                        total_percent = (star5_percent + star4_percent + 
                                        star3_percent + star2_percent + star1_percent)
                        
                        if total_percent > 0:
                            avg_rating = weighted_sum / total_percent
                            seller_info.seller_rating = f"{avg_rating:.1f}"
                else:
                    print(f"  Could not identify 12-month data")
                
                # Process lifetime data
                if lifetime_data:
                    if 'ratingCount' in lifetime_data:
                        seller_info.lifetime_reviews = str(lifetime_data['ratingCount'])
                    
                    if 'star5' in lifetime_data:
                        star5_percent = lifetime_data.get('star5', 0)
                        star4_percent = lifetime_data.get('star4', 0)
                        star3_percent = lifetime_data.get('star3', 0)
                        star2_percent = lifetime_data.get('star2', 0)
                        star1_percent = lifetime_data.get('star1', 0)
                        
                        
                        
                        weighted_sum = (star5_percent * 5 + 
                                       star4_percent * 4 + 
                                       star3_percent * 3 + 
                                       star2_percent * 2 + 
                                       star1_percent * 1)
                        total_percent = (star5_percent + star4_percent + 
                                        star3_percent + star2_percent + star1_percent)
                        
                        if total_percent > 0:
                            avg_rating = weighted_sum / total_percent
                            seller_info.lifetime_rating = f"{avg_rating:.1f}"
                            
                else:
                    print(f"  Could not identify lifetime data")

                rating_year_div = soup.find('div', id='rating-year')
                if rating_year_div:
                    rating_span = rating_year_div.find('span', class_='ratings-reviews')
                    if rating_span:
                        correct_rating = rating_span.get_text(strip=True)
                        if correct_rating:
                            seller_info.seller_rating = correct_rating
                            
                
                if seller_info.seller_rating in ["4.9", "Not found"]: 
                    year_rating_span = soup.find('span', id='effective-timeperiod-rating-year-description')
                    if year_rating_span:
                        correct_rating = year_rating_span.get_text(strip=True)
                        if correct_rating:
                            seller_info.seller_rating = correct_rating
                            

                if seller_info.seller_reviews == "Not found":
                    rating_num_div = soup.find('div', id='rating-365d-num')
                    if rating_num_div:
                        count_span = rating_num_div.find('span', class_='ratings-reviews-count')
                        if count_span:
                            seller_info.seller_reviews = count_span.get_text(strip=True)

                five_star_percent = soup.find('span', id='percentFiveStar')
                if five_star_percent:
                    seller_info.positive_feedback = five_star_percent.get_text(strip=True)
                elif not seller_info.positive_feedback:
                    percentage_elem = soup.find(string=re.compile(r'\d+%\s*positive'))
                    if percentage_elem:
                        percent_match = re.search(r'(\d+%)', percentage_elem)
                        if percent_match:
                            seller_info.positive_feedback = percent_match.group(1)
                
        except Exception as e:
            print(f"  Could not fetch seller page: {e}")
            import traceback
            traceback.print_exc()