# SocialPulse AI

A full-stack starter implementation for social media sentiment analysis.

## Stack
- React + Vite + Tailwind CSS + Recharts
- Flask REST API + SQLAlchemy + JWT
- PostgreSQL (SQLite fallback for local development)
- Scikit-learn TF-IDF + Logistic Regression sentiment model
- YouTube Data API integration; platform adapters clearly report unsupported/missing credentials
- PDF reports with ReportLab

## Quick start

### Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows; use cp on macOS/Linux
python seed_model.py
python app.py
```
API runs at http://localhost:5000.

For PostgreSQL, set `DATABASE_URL` in `.env`, for example:
`postgresql://postgres:password@localhost:5432/socialpulse`

Without it, the app uses SQLite (`socialpulse.db`) for easy local setup.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173.

## Social media access
YouTube comments are fetched using the official YouTube Data API v3. Set `YOUTUBE_API_KEY`.
Other platforms require their own approved developer access and are intentionally implemented as explicit adapters that return a useful setup message rather than scraping private content or fabricating data. Instagram/Facebook Graph API access depends on eligible accounts, permissions and media ownership; X and Reddit require their own API credentials and permitted scopes.

## Demo mode
If no platform credentials are configured, use the clearly labeled **Demo analysis** option in the UI. Demo comments are synthetic examples and are never represented as real social media data.

## Security and production notes
This is a functional academic project foundation, not a production-audited service. Before public deployment:
- Set a long random `JWT_SECRET_KEY` and strong database credentials.
- Configure exact CORS origins.
- Use HTTPS and secure cookie/token storage appropriate to your deployment.
- Add email delivery for password reset (endpoint currently returns a development notice).
- Review each platform's current terms and API permissions.
- Add a production task queue for large comment batches.
- Run migrations and automated security tests.

## Main features
- Registration/login and protected API endpoints
- Dashboard metrics and recent analyses
- URL validation and platform detection
- YouTube video details and public comment retrieval
- Demo analysis using synthetic data
- ML sentiment classification with a trained baseline model
- Topic/complaint extraction and actionable rule-based recommendations
- Analysis history, detail view, PDF report
- Dark/light mode, English/Hindi language toggle
- Guided first-login onboarding
- FAQ chatbot with optional contextual report assistance
