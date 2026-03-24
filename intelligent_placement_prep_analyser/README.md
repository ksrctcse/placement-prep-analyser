
# Intelligent Placement Preparation & Tracking Agent

Backend: FastAPI + LangChain + Google Gemini
Frontend: React + PrimeReact

## Backend Setup

cd backend
pip install -r requirements.txt

Create `.env`
GEMINI_API_KEY=your_key

Run server
uvicorn app.main:app --reload

## Frontend Setup

cd frontend/primereact-app
npm install
npm start
