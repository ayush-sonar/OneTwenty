# Nightscout SaaS Backend (Python)

This is the new multi-tenant backend built with FastAPI.

## Prerequisites

-   Python 3.10+
-   PostgreSQL (NeonDB)
-   MongoDB (Atlas)

## Setup

1.  **Install Dependencies**:
    ```bash
    cd backend_python
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    Ensure your `app/core/config.py` (or `.env`) has valid `MONGO_URI` and `SQLALCHEMY_DATABASE_URL`.

3.  **Initialize Database**:
    This will create the necessary tables (`tenants`, `users`, `api_keys`) in your Postgres DB.
    ```bash
    python scripts/init_db_schema.py
    ```

## Running the Server

```bash
uvicorn main:app --reload
```

## First Steps (Authentication)

1.  **Signup**:
    ```bash
    curl -X POST "http://127.0.0.1:8000/api/v1/auth/signup" \
         -H "Content-Type: application/json" \
         -d '{"email": "myuser@example.com", "password": "securepassword"}'
    ```

2.  **Login** (Get Token):
    ```bash
    curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
         -H "Content-Type: application/json" \
         -d '{"user_id": "myuser@example.com", "password": "securepassword"}'
    ```

3.  **Get API Secret** (For Uploader):
    Use the `access_token` from the previous step.
    ```bash
    curl -X POST "http://127.0.0.1:8000/api/v1/auth/api-secret" \
         -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
    ```

4.  **Upload Data**:
    Use the `api_secret` from step 3.
    ```bash
    curl -X POST "http://127.0.0.1:8000/api/v1/entries" \
         -H "api-secret: <YOUR_API_SECRET>" \
         -H "Content-Type: application/json" \
         -d '[{"type": "sgv", "dateString": "2023-10-27T10:00:00.000Z", "date": 1698400800000, "sgv": 120}]'
    ```
