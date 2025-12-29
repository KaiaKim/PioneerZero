# React Migration Setup Instructions

## Quick Start

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Move Static Assets to Public Folder**
   The images and audio folders need to be moved to the `public/` folder for Vite to serve them correctly:
   
   ```bash
   # Windows PowerShell
   Move-Item -Path "images" -Destination "public\images" -Force
   Move-Item -Path "audio" -Destination "public\audio" -Force
   ```
   
   Or manually move:
   - `images/` → `public/images/`
   - `audio/` → `public/audio/`

3. **Start Development Server**
   ```bash
   npm run dev
   ```
   
   The app will be available at `http://localhost:3000`

4. **Build for Production**
   ```bash
   npm run build
   ```
   
   Output will be in the `dist/` folder.

## What's Changed

- ✅ React app structure created
- ✅ All components migrated to React
- ✅ WebSocket hooks created
- ✅ Routing set up (React Router)
- ✅ CSS files preserved (imported in components)

## File Structure

```
src/
├── components/
│   ├── auth.jsx          # Authentication component
│   ├── lobby.jsx         # Lobby page
│   └── gameRoom.jsx      # Game room page
├── hooks/
│   ├── useAuth.js        # Auth WebSocket logic
│   ├── useLobby.js       # Lobby WebSocket logic
│   └── useGame.js        # Game WebSocket logic
├── util.js               # Utility functions
├── App.jsx               # Main app with routing
└── main.jsx              # React entry point

public/
├── images/               # Move from root
├── audio/                # Move from root
└── index.html            # HTML template
```

## Important Notes

- **WebSocket URLs**: Currently hardcoded to `ws://localhost:8000/ws`
- **Asset Paths**: Use absolute paths from public folder (e.g., `/images/file.png`)
- **Routing**: 
  - `/` → Lobby page
  - `/room/:gameId` → Game room page
- **Old Files**: The original HTML/JS files are still in the project. You can remove them after testing.

## Testing Checklist

- [ ] Install dependencies (`npm install`)
- [ ] Move images and audio to public folder
- [ ] Start dev server (`npm run dev`)
- [ ] Test lobby page loads
- [ ] Test authentication
- [ ] Test creating a game
- [ ] Test joining a game
- [ ] Test game room functionality
- [ ] Test WebSocket connections
- [ ] Test chat functionality

## Troubleshooting

**WebSocket connection fails:**
- Make sure your Python backend is running on `localhost:8000`
- Check browser console for errors

**Images/audio not loading:**
- Make sure files are in `public/images/` and `public/audio/`
- Use absolute paths: `/images/file.png` not `./images/file.png`

**Routing issues:**
- Make sure you're using React Router's `useNavigate` instead of `window.open`
- Game room URL format: `/room/{gameId}` not `room.html?game_id={gameId}`

