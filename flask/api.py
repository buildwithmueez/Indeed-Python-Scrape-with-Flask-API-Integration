
# # api.py
# from flask import Flask, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
# from scrapy.crawler import CrawlerProcess
# from twisted.internet import reactor
# from scrapy.utils.log import configure_logging
# from scrapy_spider import MySpider

# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost:3306/flask_scrapper_jobs'
# db = SQLAlchemy(app)

# # Define a model for the jobs table
# class Job(db.Model):
#     __tablename__ = 'jobs'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     location = db.Column(db.String(255))
#     keyword = db.Column(db.String(255))
#     status = db.Column(db.String(255))
#     json_data = db.Column(db.JSON)

# # Configure Scrapy runner
# configure_logging()
# runner = CrawlerProcess()

# @app.route('/jobcreate', methods=['POST'])
# def job_create():
#     try:
#         data = request.get_json()
#         keyword = data.get('keyword', 'software engineer')
#         location = data.get('location', 'California')
#         print(f"Received job creation request for keyword: {keyword}, location: {location}")

#         # Run the Scrapy spider to scrape job data
#         d = runner.crawl(MySpider, keyword=keyword, location=location)
#         d.addBoth(lambda _: reactor.stop())
#         reactor.run()

#         # Save job data to the 'jobs' table
#         new_job = Job(location=location, keyword=keyword, status='scraping in progress', json_data={})
#         db.session.add(new_job)
#         db.session.commit()

#         response_message = f'Scraping job data for keyword: {keyword} in location: {location} completed. Job entry added to the database.'
#         response_data = {'status': 'success', 'message': response_message}
#     except Exception as e:
#         response_data = {'status': 'error', 'message': str(e)}

#     return response_data

# @app.route('/jobget', methods=['POST'])
# def job_get():
#     try:
#         data = request.get_json()
#         jobid = data.get('jobid')
#         print(f"Received request to get job details for jobid: {jobid}")

#         # Fetch job details from the 'jobs' table based on jobid
#         job_details = Job.query.get(jobid)

#         if job_details:
#             response_data = {'status': 'success', 'job_details': {
#                 'id': job_details.id,
#                 'location': job_details.location,
#                 'keyword': job_details.keyword,
#                 'status': job_details.status,
#                 'json_data': job_details.json_data,
#             }}
#         else:
#             response_data = {'status': 'error', 'message': f'Job details not found for jobid: {jobid}'}
#     except Exception as e:
#         response_data = {'status': 'error', 'message': str(e)}

#     return jsonify(response_data)

# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from twisted.internet import reactor, threads
from scrapy.utils.log import configure_logging
from scrapy.crawler import CrawlerRunner
from scrapy_spider import MySpider

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost:3306/flask_scrapper_jobs'
db = SQLAlchemy(app)

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location = db.Column(db.String(255))
    keyword = db.Column(db.String(255))
    status = db.Column(db.String(255))
    json_data = db.Column(db.JSON)

configure_logging()
runner = CrawlerRunner()

def run_crawler(keyword, location, job_id):
    try:
        print(f"Running crawler for job id {job_id}")
        d = runner.crawl(MySpider, keyword=keyword, location=location)
        d.addBoth(lambda _: update_job_status(job_id, 'completed'))
    except Exception as e:
        print(f"Exception during crawling: {e}")
        update_job_status(job_id, 'failed')
        raise e

def update_job_status(job_id, status):
    try:
        job_details = Job.query.get(job_id)
        job_details.status = status
        db.session.commit()
        print(f"Job status updated to {status} for job id {job_id}")
        if status == 'completed':
            reactor.stop()
    except Exception as e:
        print(f"Exception when updating job status: {e}")

@app.route('/jobcreate', methods=['POST'])
def job_create():
    try:
        data = request.get_json() 
        keyword = data.get('keyword', 'software engineer')
        location = data.get('location', 'California')

        new_job = Job(location=location, keyword=keyword, status='started', json_data={})
        db.session.add(new_job)
        db.session.commit()

        job_id = new_job.id
        print(f"Job created with id {job_id}")
        print(f"Reactor running before starting crawler: {reactor.running}")
        threads.deferToThread(run_crawler, keyword, location, job_id)
        print(f"Reactor running after starting crawler: {reactor.running}")
        
        if not reactor.running:
            reactor.run(installSignalHandlers=0)
            
        response_data = {'status': 'success', 'job_id': job_id, 'message': f'Scraping job data for keyword: {keyword} in location: {location} started. Job entry added to the database.'}
    except Exception as e:
        print(f"Exception when creating job: {e}")
        response_data = {'status': 'error', 'message': str(e)}

    return jsonify(response_data)


@app.route('/jobget', methods=['POST'])
def job_get():
    try:
        data = request.get_json()
        jobid = data.get('jobid')

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
        print(f"Exception when getting job details: {e}")
        response_data = {'status': 'error', 'message': str(e)}

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
