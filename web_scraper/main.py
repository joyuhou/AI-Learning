import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from scraper.fetcher import fetch_page_with_resources_recursive



def run():

    seed_url = "https://curaballusn.findconsumerguide.com/reviewseniorball/"
    offer_url = "https://curaballusn.findconsumerguide.com/reviewseniorball/enshop.php?"
    offer_url_2 = "https://www.dfdfdfdfdfdf.com/pw-autoinsurance/"
    replace_url = "https://www.g8mv2trk.com/5RPW1X/24NCH8Z/?sub1={tracking_id}"
    output_dir = 'curaball'
    
    fetch_page_with_resources_recursive(seed_url, offer_url, offer_url_2, replace_url, output_dir)

if __name__ == "__main__":
    run()
