# PromptVault — Frontend

The React frontend for **PromptVault**, a full-stack application for securely organizing, categorizing, and managing reusable LLM prompts.

PromptVault provides an authenticated interface for creating, editing, searching, pinning, and organizing personal prompts.

**Repository:** [PromptVault](https://github.com/OmShetty26/PromptVault)  
**Live application:** [https://promptvault-app-8w2n.onrender.com](https://promptvault-app-8w2n.onrender.com)

## Tech Stack

- **Framework:** React
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Routing:** React Router DOM
- **HTTP Requests:** Fetch API
- **Backend Integration:** FastAPI REST API

## Features

- **Authentication:** Registration, login, and logout with persistent authenticated sessions.
- **Prompt Management:** Create, view, edit, and delete prompts.
- **Organization:** Categorize, pin, and rename saved prompts.
- **User-specific Data:** Displays prompts belonging to the authenticated user.
- **Prompt Editor:** Dedicated interface for creating and modifying prompt content.
- **REST API Integration:** Communicates with the FastAPI backend through centralized API URL handling.

## Project Structure

```text
frontend/
├── public/
├── src/
│   ├── components/
│   ├── pages/
│   ├── App.jsx
│   └── api.js
├── package.json
└── vite.config.js
```

## Local Development

### Prerequisites

- Node.js 24 or a compatible supported Node.js version
- npm
- A running PromptVault backend and PostgreSQL database

### 1. Clone the repository

```bash
git clone https://github.com/OmShetty26/PromptVault.git
cd PromptVault/frontend
```

### 2. Install dependencies

```bash
npm ci
```

### 3. Start the development server

```bash
npm run dev
```

The Vite development server runs at:

`http://localhost:5173`

The frontend development configuration communicates with the backend at `http://localhost:8000` by default. Ensure the backend is running before using authenticated application features.

## Available Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the Vite development server |
| `npm run lint` | Run ESLint |
| `npm run build` | Create a production build |

## Production Architecture

In production, the React application is built into static assets and served by the FastAPI application through a single Render web service.

The frontend and backend share the same production origin, so API requests use relative URLs rather than requiring a separate frontend deployment or production API URL.

## Related Documentation

- [Backend README](../backend/README.md)
- [Root repository](https://github.com/OmShetty26/PromptVault)
