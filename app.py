from flask import Flask, redirect, url_for
from auth import auth_routes  # Import the Blueprint from auth module

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for flash messages

# Register the Blueprint
app.register_blueprint(auth_routes, url_prefix='/auth')

# Define the root route and redirect to the login page
@app.route('/')
def home():
    return redirect(url_for('auth_routes.login'))  # Updated to 'auth_routes.login'

if __name__ == '__main__':
    app.run(debug=True, port=8000)
