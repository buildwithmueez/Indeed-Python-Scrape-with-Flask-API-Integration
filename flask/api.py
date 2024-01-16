from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from twisted.internet import reactor, threads
from multiprocessing import Process, Queue
from scrapy.utils.log import configure_logging
from scrapy.crawler import CrawlerRunner
from scrapy_spider import MySpider
import time
import json
import shared
import pymysql
pymysql.install_as_MySQLdb()

global job_id

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


def run_crawler(keyword, location, job_id):


    def f(q, keyword, location, job_id):
        try:
            print(f"Running crawler for job id {job_id}")
            MySpider.custom_settings = {
                'FEEDS': {f'data/{job_id}.json': {'format': 'json',}}
            }
            runner = CrawlerRunner()
            d = runner.crawl(MySpider, keyword=keyword, location=location, job_id=job_id)
            d.addBoth(lambda _: update_job_status(job_id, 'completed'))
            # deferred = runner.crawl(spider)
            # deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            q.put(None)
        except Exception as e:
            q.put(e)
            print(f"Exception during crawling: {e}")
            update_job_status(job_id, 'failed')

    q = Queue()
    p = Process(target=f, args=(q, keyword, location, job_id))
    p.start()
    result = q.get()
    p.join()

    if result is not None:
        raise result


    # try:
    #     print(f"Running crawler for job id {job_id}")
    #     MySpider.custom_settings = {
    #         'FEEDS': {f'data/{job_id}.json': {'format': 'json',}}
    #     }
    #     runner = CrawlerRunner()
    #     d = runner.crawl(MySpider, keyword=keyword, location=location, job_id=job_id)
    #     d.addBoth(lambda _: update_job_status(job_id, 'completed'))
    # except Exception as e:
    #     print(f"Exception during crawling: {e}")
    #     update_job_status(job_id, 'failed')
    #     raise e

def update_job_status(job_id, status):
    try:
         with app.app_context():
            job_details = Job.query.get(job_id)
            job_details.status = status
            db.session.commit()
            print(f"Job status updated to {status} for job id {job_id}")
            if status == 'completed':
                reactor.stop()
    except Exception as e:
        print(f"Exception when updating job status: {e}")


def save_json_data_to_db(job_id, json_file):
    try:
        with app.app_context():
            # Fetch job details from the 'jobs' table based on job_id
            job_details = Job.query.get(job_id)

            if job_details:
                # Read the content of the JSON file
                with open(json_file, 'r') as file:
                    json_data = json.load(file)

                # Update the 'json_data' field in the database
                if json_data is not None:
                    job_details.json_data = json_data
                    db.session.commit()
                    print(f'Data saved for job ID: {job_id}')
                return True
            else:
                print(f'Job details not found for job ID: {job_id}')
                return False
    except Exception as e:
        print(f'Error saving data to the database: {e}')
        return False



# Endpoints
@app.route('/jobcreate', methods=['POST'])
def job_create():
    # try:
    data = request.get_json() 
    keyword = data.get('keyword', 'software engineer')
    location = data.get('location', 'California')

    new_job = Job(location=location, keyword=keyword, status='started', json_data={})
    db.session.add(new_job)
    db.session.commit()

    # job_id = new_job.id
    # shared.job_id = job_id
    print(f"Job created with id {new_job.id}")
    # print(f"Reactor running before starting crawler: {reactor.running}")

    try:
        # threads.deferToThread(run_crawler, keyword, location, new_job.id)
        run_crawler(keyword, location, new_job.id)
    except Exception as e:
        print(f"Exception when creating job 2: {e}")

    # print(f"Reactor running after starting crawler: {reactor.running}")
    
    # if not reactor.running:
    #     reactor.run(installSignalHandlers=0)
        
    response_data = {'status': 'success', 'job_id': new_job.id, 'message': f'Scraping job data for keyword: {keyword} in location: {location} started. Job entry added to the database.'}
    json_file = f'./data/{new_job.id}.json'
    save_success = save_json_data_to_db(new_job.id, json_file)



    if save_success:
        print('Data saved successfully!')
    else:
        print('Failed to save data.')
    # except Exception as e:
    #     print(f"Exception when creating job: {e}")
    #     response_data = {'status': 'error', 'message': str(e)}

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
