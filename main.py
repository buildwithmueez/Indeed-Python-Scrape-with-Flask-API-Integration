import subprocess
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from multiprocessing import Process
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from indeed_python_scrapy_scraper.indeed.spiders.jobs_spider import IndeedJobSpider
from flask_migrate import Migrate



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/flask_scrapper_jobs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

crawling_process = None  # Global variable to store the subprocess object




# Function to start the Scrapy process
def start_scrapy_process(keyword, location, job_id):
    process = CrawlerProcess(get_project_settings())

    # Set proxy settings
    proxy_url = 'https://proxy.scrapeops.io/v1/?api_key=2839210c-367d-4664-b2e8-2072dd6026c3&url='
    process.settings.set('HTTP_PROXY', proxy_url)
    process.settings.set('HTTPS_PROXY', proxy_url)

    # Get the command used to start the spider
    command = process.crawl(IndeedJobSpider, keyword=keyword, location=location, job_id=job_id)
    
    # Print the command
    print(f"Scrapy command: {command}")

    process.start()
    process.stop()


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(255))
    keyword = db.Column(db.String(255))
    status = db.Column(db.String(50))  


# Endpoint for job creation and scraping
@app.route('/jobCreate', methods=['POST'])
def job_create():
    global crawling_process  # Use the global variable

    try:
        # Get JSON data from the request
        data = request.get_json()

        # Check if 'location' and 'keyword' are present in the JSON data
        location = data.get('location')
        keyword = data.get('keyword')

        # Save job details to the database
        with app.app_context():
            job_ids = []
            for loc, key in zip(location, keyword):
                new_job = Job(location=loc, keyword=key, status='started')
                db.session.add(new_job)
                db.session.commit()  # Commit each job individually
                job_ids.append(new_job.id)

            print("Successfully connected to the database and saved job details.")

        # Terminate the existing crawling process if it exists
        if crawling_process and crawling_process.is_alive():
            crawling_process.terminate()
            crawling_process.join()

        # Run Scrapy spider programmatically in a separate process
        crawling_process = Process(target=start_scrapy_process, args=(keyword, location, job_ids))
        print(keyword, location, job_ids)
        crawling_process.start()

        # ... (other logic)

        response = {
            'code': 200,
            'result': 'Success! Jobs started and saved to the database',
            'jobIDs': job_ids
        }

        return jsonify(response)

    except Exception as e:
        # Handle any exceptions and return an error response
        error_response = {
            'code': 500,
            'error': str(e)
        }

        # Update job status to 'failed' in case of an error
        with app.app_context():
            for job_id in job_ids:
                job = Job.query.get(job_id)
                if job:
                    job.status = 'failed'
                    db.session.commit()

        return jsonify(error_response), 500



@app.route('/getJobData', methods=['POST'])
def get_job_data():
    try:
        # Get JSON data from the request
        data = request.get_json()
        job_id = data.get('jobID')

        # Search the database for the entry with the given job ID
        job = Job.query.filter_by(id=job_id).first()

        if job:
            # Check the status of the job
            if job.status in ['started', 'failed']:
                # Assuming you have some data associated with the job, modify this part accordingly
                job_data = {
                    'code': 200,
                    'jobIDs': [job.id],
                    'status': job.status,
                    'data': []  # You can add the actual data associated with the job here
                }

                return jsonify(job_data)
            else:
                response = {
                    'code': 400,
                    'error': f"Job with ID {job_id} has an invalid status."
                }
                return jsonify(response), 400
        else:
            response = {
                'code': 404,
                'error': f"Job with ID {job_id} not found."
            }
            return jsonify(response), 404

    except Exception as e:
        # Handle any exceptions and return an error response
        error_response = {
            'code': 500,
            'error': str(e)
        }
        return jsonify(error_response), 500






















# Endpoint to stop the crawling job
@app.route('/stopCrawl', methods=['POST'])
def stop_crawl():
    global crawling_process  # Use the global variable

    try:
        # Terminate the existing crawling process if it exists
        if crawling_process and crawling_process.is_alive():
            crawling_process.terminate()
            crawling_process.join()
            response = {
                'code': 200,
                'result': 'Crawling job terminated successfully'
            }
        else:
            response = {
                'code': 200,
                'result': 'No crawling job is currently running'
            }

        return jsonify(response)

    except Exception as e:
        # Handle any exceptions and return an error response
        error_response = {
            'code': 500,
            'error': str(e)
        }
        return jsonify(error_response), 500

if __name__ == '__main__':
    # Run the application
    with app.app_context():
        # Create the database tables before running the app
        db.create_all()
        print("Database tables created.")
    app.run(debug=True)

