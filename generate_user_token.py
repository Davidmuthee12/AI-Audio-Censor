from propelauth_fastapi import init_auth

from app.config import api_settings

if __name__ == "__main__":
    auth = init_auth(
        auth_url=api_settings.PROPELAUTH_AUTH_URL,
        api_key=api_settings.PROPELAUTH_API_KEY,
    )

    response = auth.create_access_token(
        user_id="541df3e3-73ba-4596-9b71-3438a5c4bffc",
        duration_in_minutes=60 * 24,  # 1 day
    )

    print("Access token:", response.access_token)
