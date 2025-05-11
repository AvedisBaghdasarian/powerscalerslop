# PowerScaler Battle Arena

A web application that determines the winner of fictional character battles using AI analysis.

## Features

- Input two characters and get an AI-powered battle analysis
- Three AI agents (2 fighters, 1 judge) analyze the battle
- Battle history stored in MongoDB
- Modern Svelte frontend with Shadcn UI components
- Monorepo structure for easy development

## Prerequisites

- Node.js 18+
- Python 3.8+
- MongoDB
- Gemini API key

## Project Structure

```
powerscaler/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   └── database.py
│   └── requirements.txt
├── frontend/         # Svelte + Shadcn UI frontend
├── package.json      # Root package.json for monorepo
└── README.md
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   # Install root dependencies
   npm install

   # Install frontend dependencies
   cd frontend
   npm install

   # Install backend dependencies
   cd ../backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the backend directory:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   MONGODB_URI=mongodb://localhost:27017
   ```

4. Start MongoDB

5. Run the development servers:
   ```bash
   # From the root directory
   npm run dev
   ```

This will start both the frontend (http://localhost:5173) and backend (http://localhost:8000) servers.

## Testing

Run the backend tests with:
```bash
npm run test
```

## API Endpoints

- `GET /`: Welcome message
- `POST /battle`: Submit a battle request
  - Body: `{"character1": "Character1", "character2": "Character2"}`
- `GET /battle/history`: Get battle history

## Development

- Frontend: Svelte + Shadcn UI
- Backend: FastAPI + MongoDB
- AI: Gemini API for character analysis 