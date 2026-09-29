# Personal Finance Advisor Bot

A Flask + SQLAlchemy personal finance dashboard with secure login, income/expense tracking, category analysis, savings calculation, and AI-style financial recommendations.

## Features

- User registration and login
- Password hashing with Werkzeug
- Monthly income tracking
- Daily expense tracking by category
- Income vs expense summary
- Savings calculation
- Category-wise spending analysis
- Rule-based AI financial advisor
- JSON summary API
- SQLite locally and PostgreSQL on Render
- Responsive dashboard
- Render deployment configuration
- GitHub-ready structure

## Run locally on Windows

1. Install Python 3.11+.
2. Open Command Prompt in this project folder.
3. Create a virtual environment:
   `python -m venv venv`
4. Activate it:
   `venv\Scripts\activate`
5. Install packages:
   `pip install -r requirements.txt`
6. Start the app:
   `python app.py`
7. Open:
   `http://127.0.0.1:5000`

## Login

There is no hard-coded public password. Click **Create account**, register with your own email and password, and you will be logged in automatically. Later, use the same email/password on the Login page.

## GitHub

Create a new GitHub repository named `personal-finance-advisor-bot`, then run:

`git init`
`git add .`
`git commit -m "Initial Personal Finance Advisor Bot"`
`git branch -M main`
`git remote add origin YOUR_GITHUB_REPO_URL`
`git push -u origin main`

## Render

1. Push the project to GitHub.
2. In Render, choose **New + -> Blueprint**.
3. Select the GitHub repository.
4. Render reads `render.yaml`.
5. Create the web service and PostgreSQL database.
6. Wait for deployment.
7. Open the generated `onrender.com` URL.
8. Register a new account and log in.

## Important

Do not commit `.env` or real API keys/passwords to GitHub.
