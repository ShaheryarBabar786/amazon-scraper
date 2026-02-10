"""Configuration settings for the Amazon scraper"""

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

TIMEOUT = 30
EXCHANGE_RATE_API = 'https://api.exchangerate-api.com/v4/latest/USD'
DEFAULT_EXCHANGE_RATE = 0.00359
BASE_URL = 'https://www.amazon.com'
MAX_IMAGES = 10