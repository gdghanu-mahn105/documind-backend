# DocuMind Backend

DocuMind Backend is a FastAPI application for managing PDF documents, extracting content, building knowledge with RAG, generating quizzes, creating mind maps, and generating/grading essays using AI.

## Key Features

- User registration, email verification, and login with JWT
- PDF upload and automatic text extraction
- AI processing for quiz generation from documents
- Mind map generation and JSON storage
- Essay prompt generation and AI-based grading
- Management of quizzes, essays, mind maps, and document processing status

## Requirements

- Python 3.11
- Docker (optional, for Docker Compose)
- PostgreSQL (or MySQL if using `DATABASE_URL` with MySQL)

## Quick Start

1. Clone the repository:

```bash
git clone <repo-url>
cd documind-backend
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Copy the example environment file:

```bash
cp .env.example .env
```

4. Update `.env` with your own values:

- `DATABASE_URL`: database connection string
- `OPENAI_API_KEY`: OpenAI API key
- `RESEND_API_KEY`: Resend API key
- Note: if your Resend API key is not verified with a custom domain, it can only send email to which email you registered to RESEND.


## Run Locally

```bash
uvicorn app.main:app --reload
```

The app will be available at `http://127.0.0.1:8000`.

## Run with Docker Compose

```bash
docker-compose up --build
```

Docker Compose will create:

- `db`: PostgreSQL
- `app`: FastAPI backend

## Main API Endpoints

- `POST /auth/register`: register a new user and send OTP email
- `POST /auth/verify-otp`: verify email using OTP
- `POST /auth/login`: login and receive JWT token
- `GET /auth/me`: get current authenticated user

- `POST /documents/upload`: upload a PDF and process the document
- `GET /documents/{document_id}/status`: get document processing status
- `POST /documents/{document_id}/generate-quiz`: generate a quiz from the document
- `GET /documents/{document_id}/view`: view the uploaded PDF
- `GET /documents/{document_id}/summarize`: get the document summary

- `GET /quizzes`: list quizzes grouped by documents
- `GET /quizzes/{quiz_id}`: get quiz details
- `POST /quizzes/{quiz_id}/submit`: submit quiz answers
- `DELETE /quizzes/{quiz_id}`: delete a quiz

- `POST /essays/generate/{document_id}`: create an essay prompt from a document
- `GET /essays/list-by-documents`: list essays by document
- `GET /essays/{essay_id}`: get essay details
- `POST /essays/{essay_id}/submit`: submit an essay answer

- `GET /mindmaps/list-by-documents`: list mind maps by document
- `POST /mindmaps/{document_id}/mindmap`: generate a mind map
- `GET /mindmaps/{mindmap_id}/status`: check mind map status
- `GET /mindmaps/{mindmap_id}`: get mind map details
- `PUT /mindmaps/{mindmap_id}`: update a mind map
- `DELETE /mindmaps/{mindmap_id}`: delete a mind map

## Additional Resources

- Swagger UI: `http://127.0.0.1:8000/docs`
- Redoc: `http://127.0.0.1:8000/redoc`

## Notes

- The API uses `python-dotenv` to load environment variables from `.env`
- When running with Docker Compose, `DATABASE_URL` is automatically configured from `POSTGRES_*` variables
- Uploaded PDF files are stored in the `upload` folder
- RAG data is stored in the `lightrag_storage` folder with separeated sub-folder for each documents
