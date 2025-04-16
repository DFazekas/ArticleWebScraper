import jwt
import json
import time
import os

# Path to your downloaded service account JSON key file.
SERVICE_ACCOUNT_FILE = 'service_account_file.json'

# Define the OAuth 2.0 token endpoint (audience).
TOKEN_URI = "https://oauth2.googleapis.com/token"

# Define the scope(s) your application needs.
SCOPES = "https://www.googleapis.com/auth/spreadsheets"


def generate_jwt(output_filename="jwt.txt"):
    """
    Generates a JWT token based on the service account credentials and saves it to a file.
    
    Args:
        output_filename (str): Path to the file where the JWT token will be saved.
        
    Returns:
        str: The generated JWT token.
    
    Raises:
        IOError: If an error occurs while reading the service account file or writing the JWT file.
    """
    # Load your service account credentials from the JSON file.
    try:
        with open(SERVICE_ACCOUNT_FILE, 'r', encoding="utf-8") as f:
            service_account_info = json.load(f)
    except Exception as e:
        raise IOError(f"Error reading service account file: {e}")
    
    # Extract the necessary information from your service account.
    private_key = service_account_info['private_key']
    client_email = service_account_info['client_email']

    # Get the current time and set the token's expiration (1 hour from now).
    now = int(time.time())
    expires_in = 3600  # Token valid for 1 hour
    exp_time = now + expires_in

    # Construct the JWT payload.
    payload = {
        "iss": client_email,         # The service account email.
        "scope": SCOPES,             # Permissions required.
        "aud": TOKEN_URI,            # The token endpoint.
        "exp": exp_time,             # Expiration time.
        "iat": now                   # Issued at time.
    }

    # Generate the JWT token using RS256 algorithm.
    # PyJWT version 2.x returns the token as a string.
    jwt_token = jwt.encode(payload, private_key, algorithm='RS256')

    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(jwt_token)
        print(f"Saved JWT in file: {output_filename}.")
    except IOError as e:
        raise IOError(f"Error writing to file {output_filename}: {e}")

    return jwt_token

def main():
    """
    Command-line entry point for generating the JWT token.
    """
    generate_jwt()

if __name__ == "__main__":
    main()
