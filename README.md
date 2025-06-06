# Trading Journal Web Application

A minimal, secure trading journal web application built with FastAPI and MySQL. This application helps traders track their deposits, withdrawals, and daily trading performance while providing AI-powered insights using Google's Gemini AI.

## Feature

- User authentication with JWT
- Deposit and withdrawal tracking
- Daily trading entries with profit/loss tracking
- Interactive monthly calendar view
- Dashboard with key statistics
- AI-powered trading tips and lessons learned using Gemini AI (falls back to simple summaries if the API is unavailable)

## Prerequisites

- Docker and Docker Compose
- Google Gemini API key (optional but recommended)
- Without an API key the dashboard will generate basic summaries instead of AI responses

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd trading-journal
```

2. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

3. Edit the `.env` file and set your environment variables:
```
DB_HOST=db
DB_USER=trading_user
DB_PASSWORD=your_secure_password
DB_NAME=trading_journal
JWT_SECRET=your_jwt_secret_key
GEMINI_API_KEY=your_gemini_api_key
```

4. Build and start the containers:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

## Usage

1. Register a new account at `/register`
2. Log in at `/login`
3. Access the dashboard at `/dashboard`
4. Make deposits at `/deposit`
5. Make withdrawals at `/withdraw`
6. Add daily trading entries at `/daily-entry`

## Security Features

- Password hashing using bcrypt
- JWT-based authentication
- Protected routes for authenticated users
- Input sanitization
- HTTPS support (configure at deployment)

## Development

The application is structured as follows:

```
/app
├─ main.py           # FastAPI application
├─ models.py         # SQLAlchemy models
├─ schemas.py        # Pydantic schemas
├─ crud.py          # CRUD operations
├─ auth.py          # JWT and password utilities
├─ database.py      # Database connection
├─ templates/       # Jinja2 templates
└─ static/          # Static files
```

## API Endpoints

- `POST /register` - Register a new user
- `POST /token` - Login and get JWT token
- `GET /dashboard` - View trading dashboard
- `POST /deposit` - Make a deposit
- `POST /withdraw` - Make a withdrawal
- `POST /daily-entry` - Add a daily trading entry
- `PUT /daily-entry/{entry_id}` - Update a daily entry

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
