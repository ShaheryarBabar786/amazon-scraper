"""Utility functions for the scraper"""

import re
import json
import requests
from urllib.parse import urljoin, urlparse, parse_qs

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return ' '.join(text.strip().split())


def extract_currency(price_text):
    """Extract currency symbol and amount from price text"""
    currency_match = re.search(r'([^\d\s]+)\s*[\d\.,]+', price_text)
    currency_symbol = currency_match.group(1).strip() if currency_match else "$"
    
    price_match = re.search(r'([\d\.,]+)', price_text)
    price = price_match.group(1).replace(',', '') if price_match else "Not found"
    
    return currency_symbol, price


def extract_from_json_script(script_content, key):
    """Extract JSON data from script tag content"""
    try:
        patterns = [
            f'"{key}":\\s*({{.*?}})\\s*,',
            f'"{key}":\\s*({{.*?}})\\s*}}',
            f'"{key}":\\s*({{.*?}})$',
            f'"{key}":\\s*({{.*?}})\\s*</script>',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, script_content, re.DOTALL)
            if match:
                json_str = match.group(1)
                json_str = re.sub(r',\s*$', '', json_str)
                return json.loads(json_str)

        if f'"{key}":' in script_content:
            start_index = script_content.find(f'"{key}":')
            brace_start = script_content.find('{', start_index)
            if brace_start != -1:
                brace_count = 0
                for i in range(brace_start, len(script_content)):
                    if script_content[i] == '{':
                        brace_count += 1
                    elif script_content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = script_content[brace_start:i+1]
                            return json.loads(json_str)
    except Exception as e:
        print(f"Error extracting JSON for key '{key}': {e}")
        return None
    return None


def get_seller_id_from_url(url):
    """Extract seller ID from URL"""
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return query_params.get('seller', [None])[0]
    except:
        return None


def clean_seller_name(name):
    """Clean seller name"""
    if not name or name == "Not found":
        return name

    name = re.sub(r'\((.*?)\)', '', name).strip()

    name = re.sub(r'^\s*by\s*', '', name, flags=re.I).strip()

    if len(name) > 100:
        name = name[:100] + "..."
    
    return name


def get_live_exchange_rate():
    """Get current PKR to USD exchange rate from API"""
    from config import DEFAULT_EXCHANGE_RATE, EXCHANGE_RATE_API
    try:
        response = requests.get(EXCHANGE_RATE_API, timeout=5)
        data = response.json()
        pkr_per_usd = data['rates']['PKR']
        usd_per_pkr = 1 / pkr_per_usd
        return usd_per_pkr
    except:
        return DEFAULT_EXCHANGE_RATE