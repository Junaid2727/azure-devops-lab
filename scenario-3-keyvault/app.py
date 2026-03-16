from flask import Flask
from azure.keyvault.secrets import SecretClient
from azure.identity import ManagedIdentityCredential
import os

app = Flask(__name__)
KV_URL = os.environ.get("KEY_VAULT_URL")

def get_secret(secret_name):
    try:
        credential = ManagedIdentityCredential()
        client = SecretClient(vault_url=KV_URL, credential=credential)
        return client.get_secret(secret_name).value
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def home():
    db_password = get_secret("db-password")
    api_key = get_secret("api-key")
    return f"""
    <h1>Key Vault Demo!</h1>
    <p>DB Password: {db_password[:4]}**** (from Key Vault)</p>
    <p>API Key: {api_key[:4]}**** (from Key Vault)</p>
    <p>Zero credentials in code!</p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
