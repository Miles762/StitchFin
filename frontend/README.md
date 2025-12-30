# VocalBridge Ops - Frontend Dashboard

Modern React + TypeScript dashboard for managing AI agents.

## Features

✨ **Product & Design Thinking**
- Clean, intuitive UI with TailwindCSS
- Helpful empty states and onboarding
- Real-time cost visibility
- Smart error messages

✨ **Pages**
- **Login**: Secure API key authentication
- **Agents**: Create, view, and manage AI agents
- **Chat**: Test agents in real-time with cost/latency metrics
- **Analytics**: Usage statistics and cost breakdowns

✨ **User Experience**
- Responsive design (mobile, tablet, desktop)
- Loading skeletons
- Optimistic updates
- Error recovery
- Keyboard shortcuts

## Quick Start

### Prerequisites

- Node.js 18+ (check: `node --version`)
- Backend API running on http://localhost:8000

### Setup

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```

Then open: **http://localhost:5173**

### One-Command Setup

```bash
./setup_and_run_frontend.sh
```

## First Time Use

1. **Start Backend First**
   ```bash
   cd ../backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Get API Key**
   - Run seed script: `python scripts/seed.py`
   - Copy the API key from output

3. **Login to Dashboard**
   - Open http://localhost:5173
   - Paste your API key
   - Click "Sign In"

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool (fast!)
- **React Router** - Navigation
- **React Query** - API state management
- **TailwindCSS** - Styling
- **Recharts** - Analytics charts
- **Lucide React** - Icons

## Project Structure

```
src/
├── api/          # API client & endpoints
├── components/   # Reusable components (Layout)
├── pages/        # Page components (Login, Agents, Chat, Analytics)
├── hooks/        # Custom hooks (useAuth, useAgents, useChat)
├── types/        # TypeScript types
├── App.tsx       # Main app with routing
└── main.tsx      # Entry point
```

## Key Features

### Agent Management
- Create agents with custom prompts
- Configure primary/fallback providers
- Enable tools (invoice lookup)
- Delete agents with confirmation

### Chat Interface
- Select agent to chat with
- Real-time message exchange
- Cost per message ($0.00xxxx)
- Latency metrics (234ms)
- Token counts (in/out)
- Provider used (vendorA/B)
- Tool execution indicators

### Analytics Dashboard
- Total sessions, messages, tokens, cost
- Provider breakdown (VendorA vs VendorB)
- Top agents by cost
- Visual charts

## Product Thinking Examples

### 1. Smart Defaults
- Pre-filled system prompts
- Suggested provider: VendorA (cheaper)
- Recommended fallback: VendorB (for reliability)

### 2. Cost Transparency
- Every message shows exact cost
- Visual indicators: 🟢 Low, 🟡 Medium, 🔴 High
- "This conversation cost $0.45 so far"

### 3. Error Recovery
- "VendorA failed, trying VendorB..." in chat
- Retry button on failed messages
- Clear, actionable error messages

### 4. Empty States
- "No agents yet. Create your first agent to get started"
- Helpful prompts with CTAs
- Visual icons

### 5. Productivity
- Enter key to send messages
- Auto-scroll to new messages
- Persistent API key (localStorage)
- Fast page navigation

## Building for Production

```bash
# Build optimized bundle
npm run build

# Preview production build
npm run preview
```

## Environment Variables

```env
# Backend API URL (default: http://localhost:8000)
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

### Cannot connect to backend
- Check backend is running: `curl http://localhost:8000/health`
- Check CORS settings in backend
- Check browser console for errors

### API key invalid
- Get new key: `python scripts/seed.py`
- Make sure you copied the full key (starts with "sk_")
- Check backend logs for authentication errors

### Port 5173 already in use
```bash
# Use different port
vite --port 3000
```

## Customer-First Features

✅ **Transparent billing** - See exact costs per message
✅ **Cost optimization** - "Top agents by cost" helps identify expensive agents
✅ **Debugging support** - Correlation IDs, provider used, retry counts visible
✅ **Business value** - Invoice lookup tool demonstrates real workflows

## Accessibility

- Semantic HTML (nav, main, article)
- ARIA labels where needed
- Keyboard navigation support
- Focus states visible
- Color contrast meets WCAG AA

## License

MIT - See LICENSE file

---

**Built with ❤️ for VocalBridge Ops Assignment**
