"""Data models for Amazon products"""

import json

class SellerInfo:
    """Seller information model"""
    def __init__(self):
        self.seller_name = "Not found"
        self.seller_store_url = "Not found"
        self.seller_rating = "Not found"
        self.seller_reviews = "Not found"
        self.seller_since = "Not found"
        self.positive_feedback = "Not found"
        self.shipped_by = "Not found"
        self.sold_by = "Not found"
        self.seller_description = "Not found"
        self.seller_id = "Not found"
        self.is_amazon = False
        self.is_fulfilled_by_amazon = False
        # Add lifetime data fields
        self.lifetime_rating = "Not found"
        self.lifetime_reviews = "Not found"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'seller_name': self.seller_name,
            'seller_store_url': self.seller_store_url,
            'seller_rating': self.seller_rating,
            'seller_reviews': self.seller_reviews,
            'seller_since': self.seller_since,
            'positive_feedback': self.positive_feedback,
            'shipped_by': self.shipped_by,
            'sold_by': self.sold_by,
            'seller_description': self.seller_description,
            'seller_id': self.seller_id,
            'is_amazon': self.is_amazon,
            'is_fulfilled_by_amazon': self.is_fulfilled_by_amazon,
            # Add lifetime data
            'lifetime_rating': self.lifetime_rating,
            'lifetime_reviews': self.lifetime_reviews
        }


class Product:
    """Amazon product model"""
    def __init__(self, title, brand, price, rating, reviews, description, images, seller_info):
        self.title = title
        self.brand = brand
        self.price = price
        self.rating = rating
        self.reviews = reviews
        self.description = description
        self.images = images
        self.image_count = len(images)
        self.seller_details = seller_info
    
    def to_dict(self):
        """Convert product to dictionary"""
        return {
            'title': self.title,
            'brand': self.brand,
            'price': self.price,
            'rating': self.rating,
            'reviews': self.reviews,
            'description': self.description,
            'images': self.images,
            'image_count': self.image_count,
            'seller_details': self.seller_details.to_dict()
        }
    
    def to_json(self, filename='product_data.json'):
        """Save product to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
    
    def display(self):
        """Display product information"""
        print(f"\n Successfully scraped!")
        print(f"Title: {self.title[:50]}...")
        print(f"Brand: {self.brand}")
        print(f"Price: {self.price}")
        print(f"Rating: {self.rating}")
        print(f"Reviews: {self.reviews}")
        print(f"Images: {self.image_count} found")
        
        self.display_seller_details()
    
    def display_seller_details(self):
        """Display seller information"""
        print("\n Seller Details:")
        print(f"  Seller Name: {self.seller_details.seller_name}")
        print(f"  Seller Store URL: {self.seller_details.seller_store_url}")
        
        # Display 12-month data
        print(f"\n  12-Month Performance:")
        if self.seller_details.seller_rating != "Not found":
            print(f"    Seller Rating: {self.seller_details.seller_rating}/5")
        if self.seller_details.seller_reviews != "Not found":
            print(f"    Seller Reviews: {self.seller_details.seller_reviews}")
        
        # Display lifetime data
        print(f"\n  Lifetime Performance:")
        if self.seller_details.lifetime_rating != "Not found":
            print(f"    Lifetime Rating: {self.seller_details.lifetime_rating}/5")
        if self.seller_details.lifetime_reviews != "Not found":
            print(f"    Lifetime Reviews: {self.seller_details.lifetime_reviews}")

        if self.seller_details.seller_since != "Not found":
            print(f"\n  Seller Since: {self.seller_details.seller_since}")
        if self.seller_details.positive_feedback != "Not found":
            print(f"  Positive Feedback: {self.seller_details.positive_feedback}")
        if self.seller_details.shipped_by != "Not found":
            print(f"  Shipped By: {self.seller_details.shipped_by}")
        if self.seller_details.sold_by != "Not found":
            print(f"  Sold By: {self.seller_details.sold_by}")
        if self.seller_details.seller_description != "Not found":
            print(f"  Seller Description: {self.seller_details.seller_description[:100]}...")