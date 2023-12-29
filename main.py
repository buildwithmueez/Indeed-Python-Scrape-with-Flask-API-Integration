from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure the SQLALCHEMY_DATABASE_URI based on your local MySQL setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/flask_scrapper_jobs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(255))
    keyword = db.Column(db.String(255))
    job_id = db.Column(db.String(255))

# Endpoint for job creation
@app.route('/jobCreate', methods=['POST'])
def job_create():
    try:
        # Get JSON data from the request
        data = request.get_json()

        # Check if 'location' and 'keyword' are present in the JSON data
        location = data.get('location')
        keyword = data.get('keyword')

        # Perform any additional logic with the parameters if needed
        print(location, keyword)

        # Dummy job ID for demonstration purposes
        job_id = '12313123'

        # Save job details to the database
        with app.app_context():
            new_job = Job(location=location, keyword=keyword, job_id=job_id)
            db.session.add(new_job)
            db.session.commit()

        # Print success message
        print("Successfully connected to the database and saved job details.")

        # Return a JSON response
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

if __name__ == '__main__':
    # Run the application
    with app.app_context():
        # Create the database tables before running the app
        db.create_all()
        print("Database tables created.")
    app.run(debug=True)
