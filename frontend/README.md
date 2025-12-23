# VeritasLoop Frontend

React-based web interface for the VeritasLoop news verification system featuring real-time adversarial debate visualization.

## Overview

VeritasLoop Frontend is a modern, accessible web application that provides a visual interface for real-time fact-checking powered by adversarial multi-agent debates. The interface displays live debate exchanges between PRO and CONTRA agents, culminating in a nuanced 5-category verdict from the JUDGE agent.

## Tech Stack

- **React** 19.2.0 - UI framework
- **Vite** 7.2.4 - Build tool and dev server
- **Tailwind CSS** 4.1.17 - Utility-first styling
- **Framer Motion** 12.23.25 - Animations and transitions
- **Lucide React** 0.469.0 - Icon library
- **WebSocket** - Real-time communication with backend

## Features

- **Real-Time Debate Stream**: Watch PRO and CONTRA agents exchange arguments live
- **Agent Personality Selection**: Choose from 3 personality styles per agent (Passive, Assertive, Aggressive)
- **Visual Agent Nodes**: Animated agent avatars with dynamic status indicators
- **Progress Tracking**: Visual representation of debate rounds
- **Verdict Modal**: Full-screen dramatic reveal of final verdict with confidence score
- **Responsive Design**: Mobile-first design with glassmorphism UI
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support
- **Error Handling**: React Error Boundary with graceful degradation
- **WebSocket Reconnection**: Automatic retry logic for connection failures

## Development

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000` (see root README)

### Installation

```bash
cd frontend
npm install
```

### Running Dev Server

```bash
npm run dev
```

Opens at [http://localhost:5173](http://localhost:5173)

### Environment Configuration

The frontend uses Vite environment variables. Copy `.env.example` to `.env` and configure:

```bash
# WebSocket API endpoint
VITE_API_URL=ws://localhost:8000/ws/verify

# Environment name (development/production)
VITE_ENVIRONMENT=development
```

**Environment Files:**
- `.env.development` - Local development (auto-loaded by Vite)
- `.env.production` - Production build configuration
- `.env` - Local overrides (gitignored)
- `.env.example` - Template with all variables

### Build for Production

```bash
npm run build
```

Output: `dist/` directory

### Preview Production Build

```bash
npm run preview
```

### Linting

```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── AgentNode.jsx           # Visual agent representation
│   │   ├── ConfigPanel.jsx         # Settings and personality selector
│   │   ├── DebateStream.jsx        # Real-time message display
│   │   ├── ErrorBoundary.jsx       # Error isolation boundary
│   │   ├── ProgressTracker.jsx     # Debate progress visualization
│   │   └── VerdictReveal.jsx       # Full-screen verdict modal
│   ├── styles/
│   │   └── variables.css           # CSS custom properties
│   ├── App.jsx                     # Main application component
│   ├── index.css                   # Global styles
│   └── main.jsx                    # React entry point
├── public/                          # Static assets
├── .env.example                     # Environment template
├── .env.development                 # Development config
├── .env.production                  # Production config
├── index.html                       # HTML entry point
├── vite.config.js                   # Vite configuration
└── package.json                     # Dependencies
```

## Component Documentation

### App.jsx

**Main application component managing:**
- WebSocket connection lifecycle
- Global state (messages, verdict, agent status)
- Input validation and submission
- Connection retry logic (3 attempts with 3s delay)

**Key State:**
```javascript
{
  messages: [],              // Debate message history
  verdict: null,             // Final verdict object
  agentStatus: {             // Agent activity states
    pro: 'idle',            // 'idle' | 'thinking' | 'speaking'
    contra: 'idle',
    judge: 'idle'
  },
  isProcessing: false,       // Overall processing state
  wsStatus: 'disconnected'   // 'connected' | 'disconnected' | 'error'
}
```

### ConfigPanel.jsx

**Configuration interface with:**
- Max iterations (1-10 debate rounds)
- Max searches (-1 for unlimited)
- Input type selector (Text/URL)
- Language selector (Italian/English)
- Agent personality buttons with visual feedback
- Full ARIA support for accessibility

### AgentNode.jsx

**Visual agent representation showing:**
- Agent name based on personality
- Dynamic status indicator (idle/thinking/speaking)
- Color-coded borders (PRO: green, CONTRA: red, JUDGE: purple)
- Animated status transitions

### DebateStream.jsx

**Real-time message display with:**
- Auto-scrolling to latest message
- Staggered entry animations
- Source citations with clickable links
- Distinct styling for PRO/CONTRA messages
- ARIA live region for accessibility

### VerdictReveal.jsx

**Full-screen verdict modal featuring:**
- Color-coded verdict categories
- Confidence score display
- Summary and analysis breakdown
- PRO/CONTRA strength assessments
- Action buttons (verify another, review debate)
- Modal dialog accessibility (focus trap, ESC key)

### ErrorBoundary.jsx

**React error boundary that:**
- Catches rendering errors in component tree
- Displays user-friendly error UI
- Provides reload functionality
- Logs errors to console in development only

## WebSocket Communication

### Message Types (Backend → Frontend)

```javascript
// Status update
{ type: "status", data: { pro: "thinking", contra: "idle", judge: "idle" } }

// Debate message
{ type: "message", data: { agent: "PRO", round: 1, content: "...", sources: [...] } }

// Final verdict
{ type: "verdict", data: { verdict: "VERO", confidence_score: 85, summary: "...", ... } }

// Error
{ type: "error", data: { message: "Error description" } }
```

### Request Format (Frontend → Backend)

```javascript
{
  input: "Claim text or URL",
  type: "Text" | "URL",
  max_iterations: 3,
  max_searches: -1,
  language: "Italian" | "English",
  proPersonality: "PASSIVE" | "ASSERTIVE" | "AGGRESSIVE",
  contraPersonality: "PASSIVE" | "ASSERTIVE" | "AGGRESSIVE"
}
```

## Styling System

### CSS Variables

Defined in `src/styles/variables.css`:

```css
--color-pro: #4caf50        /* PRO agent green */
--color-contra: #f44336     /* CONTRA agent red */
--color-judge: #ab47bc      /* JUDGE agent purple */
--color-accent: #00d4ff     /* Interactive elements */
```

### Tailwind Utilities

- **Glassmorphism**: `backdrop-blur-xl` with semi-transparent backgrounds
- **Gradients**: `bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900`
- **Animations**: Framer Motion for all transitions

### Accessibility Classes

- `.sr-only` - Screen reader only text (visually hidden)

## Accessibility Features

### ARIA Attributes

- **Regions**: `role="region"` with `aria-label` for major sections
- **Radio Groups**: Personality selectors use `role="radiogroup"` with `aria-checked`
- **Live Regions**: Debate stream uses `aria-live="polite"` for real-time updates
- **Dialog Modals**: Verdict modal uses `role="dialog"` and `aria-modal="true"`
- **Form Labels**: All inputs have proper `htmlFor` associations

### Keyboard Navigation

- **Tab Order**: Logical flow through all interactive elements
- **Focus States**: Visible focus rings on all interactive elements
- **Button States**: `disabled` attribute with visual feedback

### Screen Reader Support

- **Descriptive Labels**: ARIA labels provide context for all controls
- **Hidden Decorations**: Decorative icons marked with `aria-hidden="true"`
- **Status Announcements**: Agent status changes announced via live regions

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Considerations

- **Code Splitting**: Vite automatic chunking
- **Tree Shaking**: Unused code removed in production
- **Asset Optimization**: Images and fonts optimized by Vite
- **Lazy Rendering**: AnimatePresence for conditional rendering
- **Memoization**: React.memo() on heavy components (not implemented yet)

## Troubleshooting

### WebSocket Connection Fails

1. Verify backend is running on `http://localhost:8000`
2. Check `VITE_API_URL` in `.env` file
3. Inspect browser console for CORS errors
4. Ensure firewall allows WebSocket connections

### Styles Not Loading

1. Run `npm install` to ensure Tailwind is installed
2. Check `vite.config.js` for PostCSS configuration
3. Verify `@import "tailwindcss"` in `index.css`

### Environment Variables Not Working

1. Restart dev server after changing `.env` files
2. Ensure variables start with `VITE_` prefix
3. Use `import.meta.env.VITE_*` to access in code

## Contributing

See root [CONTRIBUTING.md](../docs/CONTRIBUTING.md) for development guidelines.

## Related Documentation

- [Main README](../README.md) - Project overview
- [REACT_UI.md](../docs/REACT_UI.md) - Frontend architecture deep dive
- [API Documentation](../docs/API.md) - WebSocket protocol details
- [CLAUDE.md](../CLAUDE.md) - Developer guide
