from flask import Flask
import os, socket

app = Flask(__name__)

@app.route('/')
def home():
    return f"""
    <h1>Hello from Azure App Service!</h1>
    <p>Hostname: {socket.gethostname()}</p>
    <p>Environment: {os.environ.get('ENVIRONMENT', 'production')}</p>
    <p>Version: 1.0</p>
    """

@app.route('/health')
def health():
    return '{"status": "healthy", "version": "1.0"}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
