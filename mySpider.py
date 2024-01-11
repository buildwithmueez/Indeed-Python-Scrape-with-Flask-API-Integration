import scrapy
from urllib.parse import urlencode
import re
import json
from scrapy.loader import ItemLoader
from indeedItem import IndeedItem
import pymysql


db = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='flask_scrapper_jobs',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

""" try:
    with db.cursor() as cursor:
        sql = "INSERT INTO jobs (location, keyword, status, json_data) VALUES (%s, %s, %s, %s)"
        val = ('abcd', "def", "testing", '[]')  # Replace with the actual values you want to insert
        cursor.execute(sql, val)
    db.commit()
    print("Data inserted successfully!")
finally:
    db.close() """

API_KEY = '4c8d755c-86fb-4da2-b438-f61be22b771f'

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
                    job_url = 'https://proxy.scrapeops.io/v1/?api_key='+ API_KEY +'&url=https%3A%2F%2Fwww.indeed.com%2Fviewjob%3Fviewtype%3Dembedded%26jk%3D' + job.get('jobkey')
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
        print("called")
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

            try:
                with db.cursor() as cursor:
                    # Create a new record
                    sql = "INSERT INTO jobs (location, keyword, status, json_data) VALUES (%s, %s, %s, %s)"
                    val = ('location', "def", "testing", json.dumps(loader.__dict__))  # Replace with the actual values you want to insert
                    cursor.execute(sql, val)
                # Commit changes to the database
                db.commit()
                print("Data inserted successfully!")
            finally:
                db.close()

            # self.logger.info(f"Loaded Item: {loader.load_item()}")
            yield loader.load_item()


    def get_indeed_search_url(self, keyword, location, offset=0):
        parameters = {"q": keyword, "l": location, "filter": 0, "start": offset}
        # print("https://proxy.scrapeops.io/v1/?api_key=2839210c-367d-4664-b2e8-2072dd6026c3&url=" + urlencode("https://www.indeed.com/jobs?") + urlencode(parameters))
        return "https://proxy.scrapeops.io/v1/?api_key="+ API_KEY +"&url=https://www.indeed.com/jobs?" + urlencode(parameters)
        # return "https://www.indeed.com/jobs?" + urlencode(parameters)