from flask import Flask, request, jsonify

app = Flask(__name__)

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

        # Return a JSON response
        response = {
            'code': 200,
            'result': 'Success! Job started',
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
    app.run(debug=True)
