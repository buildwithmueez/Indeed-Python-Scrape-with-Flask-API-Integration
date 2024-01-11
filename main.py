# scrapy_spider.py
import scrapy
from scrapy.crawler import CrawlerProcess
import re
import json
from urllib.parse import urlencode

from flask import Flask, render_template
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
from scrapy.utils.log import configure_logging
from mySpider import MySpider


app = Flask(__name__)

# Configure Scrapy crawler settings
configure_logging()
runner = CrawlerRunner()

@app.route('/')
def index():
    # Run Scrapy spider when the Flask route is accessed
    d = runner.crawl(MySpider)
    d.addBoth(lambda _: reactor.stop())
    reactor.run()
    # Start the Twisted reactor to run Scrapy spider

    # Read scraped data (stored in the spider) and pass it to the template
    # scraped_data = MySpider.custom_data  # Access the scraped data from the spider

    return 'hello world'
    # print("Database tables created.")
    # Render the template and pass the scraped data for display
    # return render_template('index.html', scraped_data=scraped_data)

if __name__ == '__main__':
    app.run(debug=True)
