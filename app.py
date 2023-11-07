from flask import Flask, jsonify, render_template_string
import random
import urllib3
from urllib3.util.retry import Retry
from urllib3.exceptions import MaxRetryError

# we will use the flask library to deploy the app

app = Flask(__name__)

base_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Retry Logic Demo</title>
    <link href="https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap" rel="stylesheet">
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: 'Roboto', sans-serif;
            background-color: #121212;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            text-align: center;
        }
        a {
            color: #4A90E2;
            text-decoration: none;
            font-weight: bold;
        }
        a:hover {
            text-decoration: underline;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        p {
            font-size: 1.25rem;
            margin-bottom: 2rem;
        }
    </style>
</head>
<body>
    <h1>Welcome to the HTTP Retry Logic Demo</h1>
    <p>Try accessing <a href="/test-retry">/test-retry</a> to see the retry logic in action.</p>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(base_html)


# Randomly return a mock status to simulate an error

@app.route('/unstable-endpoint')
def unstable_endpoint():
    response = random.choice([
        (jsonify({'message': 'Success'}), 200),
        (jsonify({'error': 'Service Unavailable'}), 503),
        (jsonify({'error': 'Gateway Timeout'}), 504)
    ])
    return response


# Define the retry strategy

@app.route('/test-retry')
def test_retry():
    retries = Retry(
        total=10,
        backoff_factor=1,
        status_forcelist=[503, 504],
        raise_on_redirect=False,
        raise_on_status=False
    )

    retry_html = """
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Retry Test Result</title>
        <link href="https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap" rel="stylesheet">
        <style>
            /* Existing styles from base_html */
            /* ... */
            .result {
                text-align: center;
                margin-top: 50px;
            }
        </style>
    </head>
    <body>
        <div class="retry-info">
            <h2>Test Retry Result</h2>
            <p>Status Code: {{ status_code }}</p>
            <p>Response: {{ response }}</p>
            <p>Retries Attempted: {{ retries }}</p>
            <p><a href="/">Go back</a></p>
        </div>
    </body>
    </html>
    """

    # Create a PoolManager with the retry strategy
    http = urllib3.PoolManager(retries=retries)

    try:
        # Make a request to the unstable endpoint
        response = http.request(
            'GET', 'http://localhost:5000/unstable-endpoint')

        # Return the response status code, body, and retry history as a JSON response
        return render_template_string(
            retry_html,
            status_code=response.status,
            response=response.data.decode('utf-8'),
            retries=[
                str(retry) for retry in response.retries.history] if response.retries else 'None'
        )


# If the maximum retries are exceeded, return an error response

    except MaxRetryError as e:

        return jsonify({'error': 'Max retries reached', 'details': str(e)}), 503


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
