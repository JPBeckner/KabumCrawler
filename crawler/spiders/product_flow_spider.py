from scrapy.http.request import Request
from scrapy.responsetypes import Response
import scrapy

from crawler.models import Home, Category, Product, product


class ProductFlowSpiderSpider(scrapy.Spider):
    name = 'product_flow_spider'
    # allowed_domains = ['kabum.com.br']
    base_url = "https://www.kabum.com.br/"
    start_urls = [base_url]

    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

        self.home_model = Home
        self.category_model = Category
        self.product_model = Product

    def parse(self, response: Response):
        home = self.home_model(response)
        for category in home.categories:
            yield Request(
                url=home.get_category_link(category=category),
                callback=self.access_category,
                headers={
                    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Refer": self.base_url
                },
                meta={
                    'dont_redirect': True
                }
            )

    def access_category(self, response: Response):
        category = self.category_model(response=response)
        for page_link in category.get_pages_links():
            yield Request(
                url=page_link,
                callback=self.access_products
            )

    def access_products(self, response: Response):
        # import ipdb; ipdb.set_trace()
        category = self.category_model(response=response)
        for product_link in category.get_products_links():
            yield Request(
                url=self.base_url + product_link.lstrip('/'),
                callback=self.get_product_data
            )

    def get_product_data(self, response: Response):
        product = self.product_model(response=response)
        self.logger.debug(
            f"original: {product.original_price} | "
            f"main: {product.main_price} | "
            f"defer: {product.defer_price}"
        )
        if product.unavailable:
            self.logger.warning(
                f"product unavailable: {response.url}"
            )
            return
        yield {
            'name': product.title,
            "defer_price": product.defer_price,
            "main_price": product.main_price,
            "original_price": product.original_price
        }

# End Of File