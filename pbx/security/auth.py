"""Authentication helpers for communicating with the Paperbox Integration API"""

import time
import json
import google.auth.crypt
import google.auth.jwt


def generate_jwt(
    sa_keyfile_path,
    expiry_length=3600,
):

    """Generates a signed JSON Web Token using a Google API Service Account."""

    now = int(time.time())

    # load service account credentials in sa_keyfile_path
    sa_content = json.load(open(sa_keyfile_path, "r"))
    sa_email = sa_content["client_email"]
    environment = sa_content["project_id"].split("-")[-1]
    endpoint = f"https://integration.{environment}.paperbox.ai"
    # build payload
    payload = {
        "iat": now,
        # expires after 'expiry_length' seconds.
        "exp": now + expiry_length,
        # iss must match 'issuer' in the security configuration in your
        # swagger spec (e.g. service account email). It can be any string.
        "iss": sa_email,
        # aud must be either your Endpoints service name, or match the value
        # specified as the 'x-google-audience' in the OpenAPI document.
        "aud": endpoint,
        # sub and email should match the service account's email address
        "sub": sa_email,
        "email": sa_email,
    }

    # sign with keyfile
    signer = google.auth.crypt.RSASigner.from_service_account_file(sa_keyfile_path)
    jwt = google.auth.jwt.encode(signer, payload).decode()
    return jwt, endpoint
