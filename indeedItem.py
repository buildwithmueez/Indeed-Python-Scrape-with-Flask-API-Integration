import scrapy

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