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
    custom_settings = {
        'FEEDS': {'data/%(name)s_%(time)s.json': {'format': 'json',}}
    }

    def __init__(self, keyword='software engineer', location='California', *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        self.keyword = keyword
        self.location = location

    def start_requests(self):
        indeed_jobs_url = self.get_indeed_search_url(self.keyword, self.location)
        yield scrapy.Request(url=indeed_jobs_url, callback=self.parse_search_results, meta={'keyword': self.keyword, 'location': self.location, 'offset': 0})

    def parse_search_results(self, response):
        location = response.meta['location']
        keyword = response.meta['keyword']
        offset = response.meta['offset']
        script_tag = re.findall(r'window.mosaic.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});', response.text)
        if script_tag is not None:
            json_blob = json.loads(script_tag[0])

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

            if offset == 0:
                meta_data = json_blob["metaData"]["mosaicProviderJobCardsModel"]["tierSummaries"]
                num_results = sum(category["jobCount"] for category in meta_data)
                if num_results > 1000:
                    num_results = 50

                for offset in range(10, num_results + 10, 10):
                    url = self.get_indeed_search_url(keyword, location, offset)
                    yield scrapy.Request(url=url, callback=self.parse_search_results,
                                         meta={'keyword': keyword, 'location': location, 'offset': offset})

    def parse_job(self, response):
        location = response.meta['location']
        keyword = response.meta['keyword']
        position = response.meta['position']
        script_tag = re.findall(r"_initialData=(\{.+?\});", response.text)
        if script_tag:
            json_blob = json.loads(script_tag[0])
            job = json_blob["jobInfoWrapperModel"]["jobInfoModel"]
            loader = ItemLoader(item=IndeedItem(), response=response)
            loader.add_value('position', position)
            loader.add_value('jobkey', response.meta['jobKey'])
            job_title = response.xpath('//h2[@class="jobsearch-JobInfoHeader-title"]/span/text()').get()
            loader.add_xpath('company', '//span[@class="css-775knl e19afand0"]/a/text()')
            loader.add_value('jobDescription', job.get('sanitizedJobDescription', ''))
            loader.add_xpath('salary', '//div[@class="css-tvvxwd ecydgvn1"]/text()')
            loader.add_xpath('benefits', '//div[@class="css-1oelwk6 eu4oa1w0"]/div[@class="css-k3ey05 eu4oa1w0"]//li/text()')
            loader.add_xpath('location', '//div[@data-testid="inlineHeader-companyLocation"]/div/text()')
            loader.add_xpath('jobType', '//div[@class="css-tvvxwd ecydgvn1"]/text()')

            self.logger.info(f"Loaded Item: {loader.load_item()}")
            yield loader.load_item()

    def get_indeed_search_url(self, keyword, location, offset=0):
        parameters = {"q": keyword, "l": location, "filter": 0, "start": offset}
        return "https://proxy.scrapeops.io/v1/?api_key=2839210c-367d-4664-b2e8-2072dd6026c3&url=https://www.indeed.com/jobs?" + urlencode(parameters)






# API Logic
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
from scrapy.utils.log import configure_logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost:3306/flask_scrapper_jobs'
db = SQLAlchemy(app)

# Define a model for the jobs table
class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location = db.Column(db.String(255))
    keyword = db.Column(db.String(255))
    status = db.Column(db.String(255))
    json_data = db.Column(db.JSON)

# Configure Scrapy runner
configure_logging()
runner = CrawlerRunner()

@app.route('/jobcreate', methods=['POST'])
def job_create():
    try:
        data = request.get_json()
        keyword = data.get('keyword', 'software engineer')
        location = data.get('location', 'California')
        print(f"Received job creation request for keyword: {keyword}, location: {location}")

        # Run the Scrapy spider to scrape job data
        d = runner.crawl(MySpider, keyword=keyword, location=location)
        d.addBoth(lambda _: reactor.stop())
        reactor.run()

        # Save job data to the 'jobs' table
        new_job = Job(location=location, keyword=keyword, status='scraping in progress', json_data={})
        db.session.add(new_job)
        db.session.commit()

        response_message = f'Scraping job data for keyword: {keyword} in location: {location} completed. Job entry added to the database.'
        response_data = {'status': 'success', 'message': response_message}
    except Exception as e:
        response_data = {'status': 'error', 'message': str(e)}

    return response_data

@app.route('/jobget', methods=['POST'])
def job_get():
    try:
        data = request.get_json()
        jobid = data.get('jobid')
        print(f"Received request to get job details for jobid: {jobid}")

        # Fetch job details from the 'jobs' table based on jobid
        job_details = Job.query.get(jobid)

        if job_details:
            response_data = {'status': 'success', 'job_details': {
                'id': job_details.id,
                'location': job_details.location,
                'keyword': job_details.keyword,
                'status': job_details.status,
                'json_data': job_details.json_data,
            }}
        else:
            response_data = {'status': 'error', 'message': f'Job details not found for jobid: {jobid}'}
    except Exception as e:
        response_data = {'status': 'error', 'message': str(e)}

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
