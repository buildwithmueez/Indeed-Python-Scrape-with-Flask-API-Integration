
# import re
# import json
# import scrapy
# from urllib.parse import urlencode
# from scrapy.loader import ItemLoader
# from indeed.items import IndeedItem


# class IndeedJobSpider(scrapy.Spider):
#   name = "indeed_jobs"

#   def get_indeed_search_url(self, keyword, location, offset=0):
#     parameters = {"q": keyword, "l": location, "filter": 0, "start": offset}
#     return "https://www.indeed.com/jobs?" + urlencode(parameters)

#   def start_requests(self):
#     keyword_list = ['python']
#     location_list = ['texas']
#     for keyword in keyword_list:
#       for location in location_list:
#         indeed_jobs_url = self.get_indeed_search_url(keyword, location)
#         yield scrapy.Request(url=indeed_jobs_url,
#                              callback=self.parse_search_results,
#                              meta={
#                                  'keyword': keyword,
#                                  'location': location,
#                                  'offset': 0
#                              })

#   def parse_search_results(self, response):
#     script_tag = re.findall(
#         r'window.mosaic.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});',
#         response.text)
#     if script_tag:
#       json_blob = json.loads(script_tag[0])

#       if response.meta['offset'] == 0:
#         meta_data = json_blob["metaData"]["mosaicProviderJobCardsModel"][
#             "tierSummaries"]
#         num_results = sum(category["jobCount"] for category in meta_data)
#         if num_results > 1000:
#           num_results = 50

#         for offset in range(10, num_results + 10, 10):
#           url = self.get_indeed_search_url(response.meta['keyword'],
#                                            response.meta['location'], offset)
#           yield scrapy.Request(url=url,
#                                callback=self.parse_search_results,
#                                meta={
#                                    'keyword': response.meta['keyword'],
#                                    'location': response.meta['location'],
#                                    'offset': offset
#                                })

#       jobs_list = json_blob['metaData']['mosaicProviderJobCardsModel'][
#           'results']
#       for index, job in enumerate(jobs_list):
#         if job.get('jobkey') is not None:
#           job_url = 'https://www.indeed.com/viewjob?viewtype=embedded&jk=' + job.get(
#               'jobkey')
#           yield scrapy.Request(url=job_url,
#                                callback=self.parse_job,
#                                meta={
#                                    'keyword': response.meta['keyword'],
#                                    'location': response.meta['location'],
#                                    'offset': response.meta['offset'],
#                                    'position': index,
#                                    'jobKey': job.get('jobkey'),
#                                })

#   def parse_job(self, response):
#     script_tag = re.findall(r"_initialData=(\{.+?\});", response.text)
#     if script_tag:
#       json_blob = json.loads(script_tag[0])
#       job = json_blob["jobInfoWrapperModel"]["jobInfoModel"]
#       loader = ItemLoader(item=IndeedItem(), response=response)
#       loader.add_value('position', response.meta['position'])
#       loader.add_value('jobkey', response.meta['jobKey'])
#       job_title = response.xpath('//h2[@class="jobsearch-JobInfoHeader-title"]/span/text()').get()
#       loader.add_xpath('company','//span[@class="css-775knl e19afand0"]/a/text()')
#       # loader.add_value('jobDescription', job.get('sanitizedJobDescription',''))
#       loader.add_xpath('salary', '//div[@class="css-tvvxwd ecydgvn1"]/text()')
#       loader.add_xpath('benefits','//div[@class="css-1oelwk6 eu4oa1w0"]/div[@class="css-k3ey05 eu4oa1w0"]//li/text()')
#       loader.add_xpath('location','//div[@data-testid="inlineHeader-companyLocation"]/div/text()')
#       loader.add_xpath('jobType', '//div[@class="css-tvvxwd ecydgvn1"]/text()')

#       self.logger.info(f"Loaded Item: {loader.load_item()}")
#       yield loader.load_item()



import re
import json
import scrapy
from urllib.parse import urlencode
from scrapy.loader import ItemLoader
# from indeed.items import IndeedItem
from indeed_python_scrapy_scraper.indeed.items import IndeedItem



class IndeedJobSpider(scrapy.Spider):
    name = "indeed_jobs"

    def start_requests(self):
        # Retrieve keyword and location from command line arguments
        keyword = getattr(self, 'keyword', 'python')
        location = getattr(self, 'location', 'texas')

        indeed_jobs_url = self.get_indeed_search_url(keyword, location)
        yield scrapy.Request(url=indeed_jobs_url,
                             callback=self.parse_search_results,
                             meta={
                                 'keyword': keyword,
                                 'location': location,
                                 'offset': 0
                             })

    def parse_search_results(self, response):
        script_tag = re.findall(
            r'window.mosaic.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});',
            response.text)
        if script_tag:
            json_blob = json.loads(script_tag[0])

            if response.meta['offset'] == 0:
                meta_data = json_blob["metaData"]["mosaicProviderJobCardsModel"][
                    "tierSummaries"]
                num_results = sum(category["jobCount"] for category in meta_data)
                if num_results > 1000:
                    num_results = 50

                for offset in range(10, num_results + 10, 10):
                    url = self.get_indeed_search_url(response.meta['keyword'],
                                                       response.meta['location'], offset)
                    yield scrapy.Request(url=url,
                                         callback=self.parse_search_results,
                                         meta={
                                             'keyword': response.meta['keyword'],
                                             'location': response.meta['location'],
                                             'offset': offset
                                         })

            jobs_list = json_blob['metaData']['mosaicProviderJobCardsModel'][
                'results']
            for index, job in enumerate(jobs_list):
                if job.get('jobkey') is not None:
                    job_url = 'https://www.indeed.com/viewjob?viewtype=embedded&jk=' + job.get(
                        'jobkey')
                    yield scrapy.Request(url=job_url,
                                         callback=self.parse_job,
                                         meta={
                                             'keyword': response.meta['keyword'],
                                             'location': response.meta['location'],
                                             'offset': response.meta['offset'],
                                             'position': index,
                                             'jobKey': job.get('jobkey'),
                                         })

    def parse_job(self, response):
        script_tag = re.findall(r"_initialData=(\{.+?\});", response.text)
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
        return "https://www.indeed.com/jobs?" + urlencode(parameters)
