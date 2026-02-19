import scrapy
import json
import os
from datetime import datetime

class TigerEtfSpider(scrapy.Spider):
    name = "tiger_etf_ajax"
    
    # The URL for the AJAX endpoint
    ajax_url = "https://investments.miraeasset.com/tigeretf/en/product/search/list.ajax"
    
    # Data storage directory
    DATA_DIR = "data/raw/websites/tiger"
    
    def __init__(self, *args, **kwargs):
        super(TigerEtfSpider, self).__init__(*args, **kwargs)
        os.makedirs(self.DATA_DIR, exist_ok=True)
        self.page_index = 1
        self.list_count = 20  # Number of items per page
        self.results = []

    def start_requests(self):
        """
        Starts the crawling by sending a POST request to the AJAX endpoint.
        """
        yield self.create_form_request(self.page_index)

    def create_form_request(self, page_index):
        """
        Helper function to create a Scrapy FormRequest.
        """
        formdata = {
            'pdfNameYn': 'N',
            'pageIndex': str(page_index),
            'firstIndex': str((page_index - 1) * self.list_count),
            'listCnt': str(self.list_count),
            'periodType': 'short',
            'listType': 'table',
            'q': '', # Search query, empty for all
        }
        
        self.logger.info(f"Crawling page {page_index}")
        return scrapy.FormRequest(
            url=self.ajax_url,
            formdata=formdata,
            callback=self.parse
        )

    def parse(self, response):
        """
        Parses the HTML snippet returned by the AJAX call.
        The response body is a list of <tr> elements.
        """
        etf_rows = response.css("tr")
        
        if not etf_rows:
            self.logger.info("No more rows found on this page.")
            return

        items_scraped_on_page = 0
        for row in etf_rows:
            # ksd_fund_code is in the <tr> tag's data-ksd-fund attribute
            ksd_fund_code = row.attrib.get('data-ksd-fund')
            if not ksd_fund_code:
                continue

            items_scraped_on_page += 1

            # Get product name from the 'item-subject' div
            product_name = row.css("div.item-subject a::text").get()
            
            # All other data is in <td> cells
            cells = row.css("td")

            def get_text_from_cell(cell_index, selector="::text"):
                try:
                    # Use re_first to get the number, stripping out blind text like '하락' or '상승'
                    value = cells[cell_index].css(selector).re_first(r'[-+]?\d*\.\d+|\d+')
                    return value.strip() if value else None
                except (IndexError, AttributeError):
                    return None

            item = {
                'ksd_fund_code': ksd_fund_code.strip(),
                'product_name': product_name.strip() if product_name else None,
                'trading_price': get_text_from_cell(2, "span.base-price::text"),
                'standard_price_nav': get_text_from_cell(3, "span.total-assets::text"),
                'yield_1_week': get_text_from_cell(5, "span::text"),
                'yield_1_month': get_text_from_cell(6, "span::text"),
                'yield_3_month': get_text_from_cell(7, "span::text"),
                'yield_6_month': get_text_from_cell(8, "span::text"),
                'crawled_at': datetime.now().isoformat(),
            }
            self.results.append(item)
            yield item

        # Pagination: if we got the number of items we expected, try fetching the next page.
        if items_scraped_on_page >= self.list_count:
            self.page_index += 1
            yield self.create_form_request(self.page_index)
        else:
            self.logger.info(f"Finished crawling. Found {items_scraped_on_page} items on the last page.")

    def closed(self, reason):
        """
        Saves all collected results to a single JSON file when the spider closes.
        """
        if self.results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_tiger_etf_list.json"
            filepath = os.path.join(self.DATA_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=4)
            
            self.logger.info(f"Spider closed: {reason}. Saved {len(self.results)} items to {filepath}")
        else:
            self.logger.warning(f"Spider closed: {reason}. No items were scraped.")

