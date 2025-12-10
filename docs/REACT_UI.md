# React Web UI Architecture

Complete guide to the modern React-based web interface.

## Overview

The React-based web interface represents a complete modernization of the VeritasLoop user experience. Built with React 19, Vite, and Tailwind CSS, it provides a professional, responsive single-page application with real-time WebSocket communication.

## Key Design Principles

### 1. Cyber-Courtroom Aesthetic
- Dark theme with glassmorphism effects
- Three-column layout representing the adversarial debate structure
- Animated agent status indicators (idle, thinking, speaking)
- Real-time visual feedback for all system states

### 2. Real-Time Communication
- WebSocket connection to FastAPI backend (`ws://localhost:8000/ws/verify`)
- Bidirectional streaming for instant updates
- Live agent status transitions
- Progressive message rendering

### 3. Professional UX
- Smooth animations using Framer Motion
- Configurable verification parameters (max iterations, max searches)
- Full-screen verdict reveal with dramatic presentation
- Responsive design for desktop and tablet devices

## Component Architecture

### App.jsx (Main Application)

The root component managing the entire application state:

**Responsibilities:**
- WebSocket connection lifecycle
- State management for debate messages, agent status, and verdict
- Configuration controls (max iterations, max searches)
- Input handling (text or URL)
- Real-time event processing from backend

**Key Features:**
- Automatic WebSocket reconnection handling
- State synchronization with backend stream
- Agent animation coordination
- Verdict display orchestration

**State Structure:**
```javascript
const [debateMessages, setDebateMessages] = useState([]);
const [verdict, setVerdict] = useState(null);
const [isVerifying, setIsVerifying] = useState(false);
const [wsStatus, setWsStatus] = useState('disconnected');
const [agentStatus, setAgentStatus] = useState({
  pro: 'idle',
  contra: 'idle'
});
const [config, setConfig] = useState({
  maxIterations: 3,
  maxSearches: -1
});
```

### AgentNode.jsx (Agent Status Indicator)

Visual representation of each agent's current state.

**Props:**
```javascript
{
  agent: 'pro' | 'contra',
  status: 'idle' | 'thinking' | 'speaking'
}
```

**Visual States:**
- **idle** (gray): Agent is waiting
- **thinking** (pulsing): Agent is processing (searching, analyzing)
- **speaking** (animated): Agent is generating argument/rebuttal

**Styling:**
- Glassmorphism card with backdrop blur
- PRO color: cyan (#00e5ff)
- CONTRA color: orange (#ff9100)
- Smooth transitions using Tailwind and Framer Motion

### DebateStream.jsx (Message Feed)

Scrollable real-time message display.

**Props:**
```javascript
{
  messages: Array<{
    round: number,
    agent: 'PRO' | 'CONTRA',
    content: string,
    sources: Array<Source>
  }>
}
```

**Features:**
- Auto-scroll to latest messages
- Color-coded by agent (PRO: cyan, CONTRA: orange)
- Source links with reliability indicators
- Round number display
- Smooth entry animations

### VerdictReveal.jsx (Verdict Modal)

Full-screen modal displaying final verdict.

**Props:**
```javascript
{
  verdict: {
    verdict: string,
    confidence_score: number,
    summary: string,
    analysis: object,
    sources_used: Array<Source>
  },
  onReset: () => void
}
```

**Features:**
- Color-coded by verdict type:
  - True: green
  - False: red
  - Partially True: yellow
  - Missing Context: blue
  - Cannot Verify: gray
- Confidence score display
- Italian summary
- PRO/CONTRA strength analysis
- Source list with reliability indicators
- Reset button to start new verification

## Styling System

### Tailwind CSS 4.1.17

Utility-first CSS framework providing:
- Responsive grid layout
- Flexbox utilities
- Typography classes
- Color system
- Animation utilities

**Configuration**: [`frontend/tailwind.config.js`](../frontend/tailwind.config.js)

### CSS Variables

Design tokens for consistent theming:

```css
/* frontend/src/styles/variables.css */
:root {
  --color-pro: #00e5ff;       /* cyan */
  --color-contra: #ff9100;    /* orange */
  --color-judge: #ffd700;     /* gold */
  --bg-dark: #0a0f1c;         /* dark background */
  --accent: #00e5ff;          /* primary accent */
}
```

### Glassmorphism Effects

CSS classes for frosted glass effect:
- `backdrop-blur-sm/md`: Blur effect
- `bg-black/20`: Semi-transparent backgrounds
- `border-white/10`: Subtle borders

Example:
```css
.glass-card {
  @apply backdrop-blur-md bg-black/20 border border-white/10;
}
```

## WebSocket Protocol

### Request Format (Client → Server)

```json
{
  "input": "claim text or URL",
  "type": "Text|URL",
  "max_iterations": 3,
  "max_searches": -1
}
```

### Response Events (Server → Client)

#### Status Update
```json
{
  "type": "status",
  "message": "Analyzing input...",
  "node": "initialize|extract|pro_research|contra_research|debate|judge"
}
```

**Frontend Action**: Update status message in arena

#### Graph Update
```json
{
  "type": "update",
  "node": "pro_research",
  "data": {
    "messages": [...],
    "round_count": 1
  },
  "description": "PRO Agent searching for evidence"
}
```

**Frontend Actions**:
- Update agent status (thinking/speaking)
- Add messages to debate stream
- Update round counter

#### Verdict
```json
{
  "type": "verdict",
  "data": {
    "verdict": "VERO|FALSO|PARZIALMENTE_VERO|CONTESTO_MANCANTE|NON_VERIFICABILE",
    "confidence_score": 85,
    "summary": "Italian summary text...",
    "analysis": {
      "pro_strengths": [...],
      "contra_strengths": [...],
      "shared_facts": [...],
      "disputed_points": [...]
    },
    "sources_used": [...],
    "metadata": {...}
  }
}
```

**Frontend Action**: Display verdict reveal modal

#### Completion/Error
```json
{
  "type": "complete|error",
  "message": "Verification finished|Error message"
}
```

**Frontend Actions**:
- Reset agent status to idle
- Show completion/error message
- Re-enable verify button

## Development Workflow

### Local Development

```bash
# Terminal 1: Backend with hot reload
uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend with HMR (Hot Module Replacement)
cd frontend
npm run dev
```

**Benefits:**
- Instant updates on code changes (both frontend and backend)
- Preserved state during development
- Fast iteration cycle

**Vite HMR**: Changes to React components update instantly without full page reload

### Building for Production

```bash
cd frontend
npm run build
```

**Output**: `frontend/dist/` directory with optimized static files

**Optimizations**:
- Code splitting
- Minification
- Tree shaking (removes unused CSS/JS)
- Asset optimization

### Preview Production Build

```bash
cd frontend
npm run preview
```

Serves the production build locally for testing.

## Technology Choices

### Why React?
- Component-based architecture for reusability
- Rich ecosystem of libraries
- Strong TypeScript support (future enhancement)
- Excellent performance with Virtual DOM
- Large community and resources

### Why Vite?
- Lightning-fast Hot Module Replacement (HMR)
- Optimized production builds with Rollup
- Native ES modules support
- Better developer experience than Webpack
- Faster cold start and build times

### Why Tailwind CSS?
- Utility-first approach reduces CSS complexity
- Consistent design system out of the box
- Responsive design made easy
- Smaller bundle sizes (tree-shaking unused styles)
- No CSS naming conflicts

### Why Framer Motion?
- Production-ready animations
- Declarative API (animations as props)
- Performance optimized (GPU acceleration)
- Rich animation primitives (variants, gestures)
- Excellent documentation

## React vs Streamlit Comparison

| Aspect | React Web UI | Streamlit UI (Legacy) |
|--------|--------------|----------------------|
| **Architecture** | SPA with WebSocket | Server-driven with reruns |
| **Performance** | Fast, client-side rendering | Slower, server reruns on interaction |
| **UI Updates** | Real-time streaming | Incremental updates via st.stream() |
| **Styling** | Full control with Tailwind CSS | Limited CSS customization |
| **Animations** | Smooth (Framer Motion) | Basic transitions |
| **Responsiveness** | Fully responsive | Limited mobile support |
| **Development** | HMR (instant feedback) | Auto-reload (slower) |
| **Deployment** | Static files + API server | Single Python app |
| **Customization** | Highly customizable | Constrained by Streamlit |
| **User Experience** | Professional, modern | Functional, rapid prototype |

**When to use each:**
- **React UI**: Production deployments, professional presentation, best UX
- **Streamlit UI**: Quick demos, internal tools, rapid prototyping

## File Structure

```
frontend/
├── src/
│   ├── App.jsx                 # Main application component
│   ├── main.jsx                # React entry point
│   ├── index.css               # Global styles with Tailwind
│   ├── App.css                 # Component-specific styles
│   ├── components/
│   │   ├── AgentNode.jsx       # Agent status indicator
│   │   ├── DebateStream.jsx    # Real-time debate message feed
│   │   └── VerdictReveal.jsx   # Verdict reveal modal
│   └── styles/
│       └── variables.css       # Design tokens and CSS variables
├── public/                     # Static assets
├── package.json                # npm dependencies
├── tailwind.config.js          # Tailwind configuration
├── postcss.config.js           # PostCSS configuration
├── vite.config.js              # Vite build configuration
├── index.html                  # HTML entry point
└── .gitignore                  # Git ignore rules
```

## State Management Strategy

**Current**: React useState hooks
- Simple, no external dependencies
- Sufficient for current app complexity

**Future Enhancement**: Consider for larger apps
- **Context API**: Share config across components
- **Zustand**: Lightweight state management
- **Redux Toolkit**: If app becomes very complex

## Error Handling

### WebSocket Errors

```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  setWsStatus('error');
  // Show error notification to user
};
```

### Connection Loss

```javascript
ws.onclose = () => {
  setWsStatus('disconnected');
  // Attempt reconnection after delay
  setTimeout(() => connectWebSocket(), 3000);
};
```

### API Errors

```javascript
if (event.type === 'error') {
  setIsVerifying(false);
  setAgentStatus({ pro: 'idle', contra: 'idle' });
  // Display error message to user
  alert(`Error: ${event.message}`);
}
```

## Accessibility Considerations

**Current**:
- Semantic HTML elements
- Alt text for icons (via Lucide React)
- Keyboard navigation support

**Future Enhancements**:
- ARIA labels for screen readers
- Focus management for modal
- Color contrast improvements
- Keyboard shortcuts

## Performance Optimizations

### Current
- Vite's optimized build
- React's virtual DOM
- CSS tree-shaking
- Lazy loading (not yet implemented)

### Future Enhancements
- Code splitting for components
- React.lazy() for route-based splitting
- Memoization (React.memo, useMemo)
- Virtual scrolling for long debate streams
- Service worker for offline support

## Future Enhancements

### Planned Features
- **User Authentication**: Login/signup system
- **Historical Dashboard**: View past verifications
- **Advanced Filtering**: Search and filter results
- **Theme Toggle**: Dark/light mode switch
- **Mobile App**: React Native version
- **PWA**: Progressive Web App capabilities
- **i18n**: Internationalization (English, Italian, more)
- **Export**: PDF/Markdown reports
- **Share**: URL sharing of verification results
- **Collaboration**: Multi-user verification sessions

### Technical Improvements
- TypeScript migration for type safety
- Unit tests with Vitest/Jest
- E2E tests with Playwright
- Storybook for component documentation
- Performance monitoring with Web Vitals

## Related Documentation

- [Usage Guide](USAGE.md) - How to use the React UI
- [Deployment Guide](DEPLOYMENT.md) - Deploy the React app
- [Development Guide](DEVELOPMENT.md) - Contributing to the UI
