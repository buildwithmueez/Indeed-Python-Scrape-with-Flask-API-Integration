# scrapy_spider.py
import scrapy
from scrapy.crawler import CrawlerProcess
import re
import json
from urllib.parse import urlencode
from scrapy.loader import ItemLoader

class IndeedItem(scrapy.Item):
    position = scrapy.Field()
    jobkey = scrapy.Field()
    jobTitle = scrapy.Field()
    company = scrapy.Field()
    jobDescription = scrapy.Field()
    salary = scrapy.Field()
    benefits = scrapy.Field()
    location = scrapy.Field()
    jobType = scrapy.Field()

class MySpider(scrapy.Spider):
    name = 'myspider'
    # Define scraping logic, start_urls, parsing methods, etc.
    custom_settings = {
        'FEEDS': { 'data/%(name)s_%(time)s.csv': { 'format': 'csv',}}
        }


    def start_requests(self):
        keyword_list = ['software engineer']
        location_list = ['California']
        for keyword in keyword_list:
            for location in location_list:
                indeed_jobs_url = self.get_indeed_search_url(keyword, location)
                yield scrapy.Request(url=indeed_jobs_url, callback=self.parse_search_results, meta={'keyword': keyword, 'location': location, 'offset': 0})

    def parse_search_results(self, response):
        location = response.meta['location']
        keyword = response.meta['keyword'] 
        offset = response.meta['offset'] 
        script_tag  = re.findall(r'window.mosaic.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});', response.text)
        if script_tag is not None:
            json_blob = json.loads(script_tag[0])

            ## Extract Jobs From Search Page
            jobs_list = json_blob['metaData']['mosaicProviderJobCardsModel']['results']
            for index, job in enumerate(jobs_list):
                if job.get('jobkey') is not None:
                    job_url = 'https://proxy.scrapeops.io/v1/?api_key=2839210c-367d-4664-b2e8-2072dd6026c3&url=https%3A%2F%2Fwww.indeed.com%2Fviewjob%3Fviewtype%3Dembedded%26jk%3D' + job.get('jobkey')
                    yield scrapy.Request(url=job_url, 
                            callback=self.parse_job, 
                            meta={
                                'keyword': keyword, 
                                'location': location, 
                                'page': round(offset / 10) + 1 if offset > 0 else 1,
                                'position': index,
                                'jobKey': job.get('jobkey'),
                            })

            
            # Paginate Through Jobs Pages
            if offset == 0:
                meta_data = json_blob["metaData"]["mosaicProviderJobCardsModel"]["tierSummaries"]
                num_results = sum(category["jobCount"] for category in meta_data)
                if num_results > 1000:
                    num_results = 50
                
                for offset in range(10, num_results + 10, 10):
                    url = self.get_indeed_search_url(keyword, location, offset)
                    yield scrapy.Request(url=url, callback=self.parse_search_results, meta={'keyword': keyword, 'location': location, 'offset': offset})
    
    def parse_job(self, response):
        location = response.meta['location']
        keyword = response.meta['keyword'] 
        page = response.meta['page'] 
        position = response.meta['position'] 
        script_tag  = re.findall(r"_initialData=(\{.+?\});", response.text)
        if script_tag:
            json_blob = json.loads(script_tag[0])
            job = json_blob["jobInfoWrapperModel"]["jobInfoModel"]
            loader = ItemLoader(item=IndeedItem(), response=response)
            loader.add_value('position', response.meta['position'])
            loader.add_value('jobkey', response.meta['jobKey'])
            job_title = response.xpath('//h2[@class="jobsearch-JobInfoHeader-title"]/span/text()').get()
            loader.add_xpath('company', '//span[@class="css-775knl e19afand0"]/a/text()')
            loader.add_value('jobDescription', job.get('sanitizedJobDescription',''))
            loader.add_xpath('salary', '//div[@class="css-tvvxwd ecydgvn1"]/text()')
            loader.add_xpath('benefits', '//div[@class="css-1oelwk6 eu4oa1w0"]/div[@class="css-k3ey05 eu4oa1w0"]//li/text()')
            loader.add_xpath('location', '//div[@data-testid="inlineHeader-companyLocation"]/div/text()')
            loader.add_xpath('jobType', '//div[@class="css-tvvxwd ecydgvn1"]/text()')

            self.logger.info(f"Loaded Item: {loader.load_item()}")
            yield loader.load_item()


    def get_indeed_search_url(self, keyword, location, offset=0):
        parameters = {"q": keyword, "l": location, "filter": 0, "start": offset}
        # print("https://proxy.scrapeops.io/v1/?api_key=2839210c-367d-4664-b2e8-2072dd6026c3&url=" + urlencode("https://www.indeed.com/jobs?") + urlencode(parameters))
        return "https://proxy.scrapeops.io/v1/?api_key=2839210c-367d-4664-b2e8-2072dd6026c3&url=https://www.indeed.com/jobs?" + urlencode(parameters)
        # return "https://www.indeed.com/jobs?" + urlencode(parameters)





# app.py

from flask import Flask, render_template
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
from scrapy.utils.log import configure_logging
# from spiders.my_spider import MySpider  # Import your Scrapy spider

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
