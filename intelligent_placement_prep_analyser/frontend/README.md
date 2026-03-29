# Frontend - Placement Prep Analyser

React + Vite frontend for the Placement Prep Analyser application.

## Setup

### Install Dependencies
```bash
npm install
```

### Development
```bash
npm run dev
```
This will start the development server on `http://localhost:5175`

### Build
```bash
npm run build
```

## Details

- **Framework:** React 18+
- **Build Tool:** Vite
- **UI Library:** PrimeReact
- **HTTP Client:** Axios
- **Routing:** React Router v6
- **Default Port:** 5175

## API Configuration

The frontend communicates with the backend at `http://localhost:8003`.

Environment variables:
- `VITE_API_URL` - Backend API URL (default: http://localhost:8003)
- `VITE_APP_TITLE` - Application title (default: Placement Prep Analyser)

See [.env](.env) for current configuration.
