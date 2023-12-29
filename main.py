import subprocess
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from multiprocessing import Process
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from indeed_python_scrapy_scraper.indeed.spiders.jobs_spider import IndeedJobSpider

app = Flask(__name__)

# Configure the SQLALCHEMY_DATABASE_URI based on your local MySQL setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/flask_scrapper_jobs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
crawling_process = None  # Global variable to store the subprocess object

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(255))
    keyword = db.Column(db.String(255))
    job_id = db.Column(db.String(255))

# Function to start the Scrapy process
def start_scrapy_process(keyword, location, job_id):
    process = CrawlerProcess(get_project_settings())
    process.crawl(IndeedJobSpider, keyword=keyword, location=location, job_id=job_id)
    process.start()
    process.stop()

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
        print(location,keyword)
        # Dummy job ID for demonstration purposes
        job_id = '12313123'

        # Save job details to the database
        with app.app_context():
            for loc, key in zip(location, keyword):
                new_job = Job(location=loc, keyword=key, job_id=job_id)
                db.session.add(new_job)

            db.session.commit()
            print("Successfully connected to the database and saved job details.")

        # Terminate the existing crawling process if it exists
        if crawling_process and crawling_process.is_alive():
            crawling_process.terminate()
            crawling_process.join()

        # Run Scrapy spider programmatically in a separate process
        crawling_process = Process(target=start_scrapy_process, args=(keyword, location, job_id))
        crawling_process.start()

        # ... (other logic)

        response = {
            'code': 200,
            'result': 'Success! Job started and saved to the database',
            'jobID': job_id
        }

        return jsonify(response)

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

# ... (other configurations)

if __name__ == '__main__':
    # Run the application
    with app.app_context():
        # Create the database tables before running the app
        db.create_all()
        print("Database tables created.")
    app.run(debug=True)
