# KG-RAG Frontend

Modern React frontend for the Knowledge Graph RAG system.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **React Router** for routing
- **shadcn/ui** for UI components (built on Radix UI + Tailwind CSS)
- **Axios** for API calls
- **Lucide React** for icons

## Getting Started

### Prerequisites

- Node.js 18+ (recommended: Node.js 20+)
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173` (Vite's default port).

The development server is configured to proxy API requests to `http://localhost:8000`.

### Build

Build for production:

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

### Docker Deployment

The frontend is integrated into the main Docker Compose stack. To run the entire application (backend + frontend):

```bash
# From the project root
cd ..
make up
```

The frontend will be available at:
- **http://localhost:3001** (new React frontend)
- **http://localhost:3000** (old minimal UI, still available)

The Docker setup:
- Builds the frontend using a multi-stage build (Node.js → Nginx)
- Serves the production build via Nginx
- Proxies API requests to the backend service
- Includes gzip compression and caching for static assets

To rebuild just the frontend service:

```bash
cd ../infra
docker-compose build frontend
docker-compose up -d frontend
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/          # Layout components (Sidebar, Header, Layout)
│   │   └── ui/              # shadcn/ui components (Button, Card, Input, etc.)
│   ├── pages/               # Page components
│   │   ├── HomePage.tsx
│   │   ├── DocumentsPage.tsx
│   │   ├── SearchPage.tsx
│   │   ├── QAPage.tsx
│   │   ├── RoadmapPage.tsx
│   │   └── AdminPage.tsx
│   ├── services/            # API service layer
│   │   ├── api.ts           # Base API client
│   │   ├── documents.ts     # Document management
│   │   ├── search.ts        # Search operations
│   │   ├── qa.ts            # Q&A and roadmap
│   │   └── admin.ts         # Admin operations
│   ├── types/               # TypeScript type definitions
│   │   └── api.ts           # API types
│   ├── utils/               # Utility functions
│   │   └── cn.ts            # Class name utility
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Features

### Document Management
- Upload single or multiple PDF documents
- Specify domain for better classification
- Track upload status

### Search
- **Vector Search**: Semantic similarity search across documents
- **Graph Search**: Execute read-only Cypher queries on the knowledge graph

### Q&A Assistant
- Ask questions and get AI-powered answers
- View citations with document references
- Automatic domain classification

### Learning Roadmaps
- Generate personalized learning paths
- Week-by-week breakdown
- Hour estimates for each topic

### Admin Dashboard
- System metrics and statistics
- Database status (Qdrant, Neo4j, Redis, PostgreSQL)
- Document overview

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Dark Mode

The app supports dark mode. Toggle it using the moon/sun icon in the header. The preference is saved in localStorage.

## API Integration

All API calls are made through the service layer in `src/services/`. The base API client (`src/services/api.ts`) handles:

- Request/response interceptors
- Error handling
- Base URL configuration

## Styling

The app uses Tailwind CSS with shadcn/ui components. The theme is defined in:

- `tailwind.config.js` - Tailwind configuration
- `src/index.css` - CSS variables for theming

## Development Tips

- Use the `@/` alias for imports (e.g., `import { Button } from '@/components/ui/button'`)
- All components are TypeScript with full type safety
- API types are defined in `src/types/api.ts` to match the backend

## License

Same as the main project.
