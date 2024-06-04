import os
from dotenv import load_dotenv, find_dotenv
from datetime import date

# Load the secrets
_ = load_dotenv(find_dotenv(filename="config/.secrets.env", raise_error_if_not_found=True)
) # read local .env file

if __name__ == "__main__":
	print("hello world")
	
API_KEY_OPENROUTE = os.environ["api_key_openrouteservice"]
API_KEY_BINGMAPS = os.environ["api_key_bingmaps"]


