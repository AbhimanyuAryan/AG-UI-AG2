# AG-UI Travel Assistant

A full-stack application demonstrating the integration of AutoGen agents with the AG-UI protocol to create an interactive AI travel assistant with human-in-the-loop capabilities.

![Travel Assistant](https://img.shields.io/badge/AI-Travel%20Assistant-blue)
![AG-UI](https://img.shields.io/badge/Protocol-AG--UI-green)
![AutoGen](https://img.shields.io/badge/Framework-AutoGen-orange)
![CopilotKit](https://img.shields.io/badge/Frontend-CopilotKit-purple)

## 📋 Overview

This project showcases a modern AI application architecture that combines:

1. **Backend**: Python-based AutoGen agents that create personalized travel itineraries
2. **Protocol**: AG-UI for standardized AI agent communication
3. **Frontend**: Next.js application with CopilotKit integration for a seamless user experience

The system allows users to interact with an AI travel assistant that can create custom travel plans, recommend destinations, and adjust itineraries based on user feedback - all with real-time streaming responses and interactive tool execution.

## 🌟 Features

### Backend (AG-UI Travel Agent)
- **AutoGen-powered AI**: Leverages AutoGen's multi-agent architecture for sophisticated planning
- **Human-in-the-Loop**: Supports human execution of tool calls when needed
- **Member Data Integration**: Connects to member profiles for personalized recommendations
- **Event-driven Architecture**: Uses Server-Sent Events (SSE) for real-time communication
- **State Management**: Maintains consistent conversation state across interactions

### Frontend (AG-UI Travel Frontend)
- **Modern UI**: Built with Next.js and Tailwind CSS
- **CopilotKit Integration**: Seamless integration with AG-UI backend
- **Real-time Streaming**: Character-by-character response streaming
- **Tool Execution UI**: Interactive interface for executing agent tool calls
- **Responsive Design**: Works across desktop and mobile devices

## 🔧 Prerequisites

- **Backend**:
  - Python 3.12+
  - Poetry (for dependency management)
  - OpenAI API key

- **Frontend**:
  - Node.js 20+
  - npm/yarn/pnpm

## 🚀 Getting Started

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd AG-UI-AG2
```

### Step 2: Set Up the Backend

```bash
cd ag-ui-travel-agent

# Create a .env file with your API key
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Install dependencies
poetry install

# Start the backend server
poetry run uvicorn src.ag_ui_ag2.hitl_workflow:app --host 0.0.0.0 --port 8000 --reload

The backend server will start at `http://localhost:8000`.

### Step 3: Set Up the Frontend

```bash
cd ../ag-ui-travel-frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## 🧩 Project Structure

```
AG-UI-AG2/
├── ag-ui-travel-agent/        # Backend Python application
│   ├── src/
│   │   └── ag_ui_ag2/         # Core Python package
│   │       ├── __init__.py
│   │       ├── ag_ui_adapter.py   # AG-UI protocol adapter
│   │       ├── database.py        # Member database simulation
│   │       ├── hitl_workflow.py   # Human-in-the-loop workflow
│   │       ├── messages.py        # Message handling
│   │       └── tool_events.py     # Tool execution events
│   ├── poetry.lock
│   ├── pyproject.toml         # Python dependencies
│   ├── README.md
│   └── tests/                 # Backend tests
│
└── ag-ui-travel-frontend/     # Frontend Next.js application
    ├── src/
    │   ├── app/               # Next.js app router
    │   │   ├── components/    # React components
    │   │   │   ├── Chat.tsx   # Chat interface
    │   │   │   ├── Travel.tsx # Travel agent component
    │   │   │   ├── Header.tsx
    │   │   │   └── Footer.tsx
    │   │   ├── api/           # API routes
    │   │   │   └── copilotkit/
    │   │   ├── copilotkit/    # CopilotKit pages
    │   │   ├── destinations/  # Travel destinations page
    │   │   └── page.tsx       # Main page
    │   └── lib/               # Shared utilities
    ├── package.json           # Frontend dependencies
    └── README.md
```

## 💻 Usage Examples

### Travel Planning Workflow

1. **Member Identification**:
   - Enter member ID (sample IDs: P12345, P67890, S12345, S67890)
   - System retrieves personalized member information

2. **Destination Selection**:
   - Specify travel destination and dates
   - AI agent provides recommendations based on preferences

3. **Itinerary Creation**:
   - AI generates a custom travel itinerary
   - Review activities, accommodations, and transportation

4. **Refinement**:
   - Request changes to the itinerary
   - AI adjusts plans based on feedback

## 🔌 API Endpoints

### Backend API

#### POST /travel-agent

AG-UI compliant endpoint for the travel agent.

**Request Format**:
```json
{
  "thread_id": "string",
  "run_id": "string",
  "messages": [
    {
      "id": "string",
      "content": "string",
      "role": "user"
    }
  ]
}
```

**Response**: Server-Sent Events (SSE) stream following the AG-UI protocol.

## 🛠️ Advanced Configuration

### Backend Configuration

Environment variables can be set in the `.env` file:

```
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=gpt-4o
PORT=8000
```

### Frontend Configuration

The frontend can be configured in `next.config.ts`:

```typescript
// Example configuration
const nextConfig = {
  env: {
    NEXT_PUBLIC_BACKEND_URL: 'http://localhost:8000',
  },
};
```

## 🧪 Testing

### Backend Tests

```bash
cd ag-ui-travel-agent
poetry run pytest
```

### Frontend Tests

```bash
cd ag-ui-travel-frontend
npm run test
```

## 📚 Technologies Used

### Backend
- **AutoGen**: Multi-agent framework for AI applications
- **FastAPI**: High-performance API framework
- **AG-UI Protocol**: Standardized AI agent communication
- **Poetry**: Python dependency management

### Frontend
- **Next.js**: React framework with app router
- **CopilotKit**: UI components for AI interactions
- **React**: Frontend library
- **Tailwind CSS**: Utility-first CSS framework

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact

For questions or feedback, please open an issue on the repository.

---

Built with ❤️ using AutoGen, AG-UI, and CopilotKit
