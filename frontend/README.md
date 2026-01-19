# MLB Showdown Bot Frontend

A modern React-based web application for creating and exploring MLB Showdown cards. This frontend provides an intuitive interface for baseball fans to build custom player cards and discover existing ones through a powerful search and filter system.

## 🎯 Overview

The MLB Showdown Bot Frontend is a comprehensive single-page application that recreates the experience of the classic MLB Showdown tabletop baseball game in digital form. Users can create custom player cards with authentic statistics or explore a vast database of existing cards from various MLB Showdown sets.

### Key Features

- **🎨 Custom Card Builder**: Create personalized MLB Showdown cards with authentic player statistics
- **🔍 Card Explorer**: Browse and search through extensive card databases with advanced filtering
- **🌓 Theme System**: Complete light/dark/system theme support with seamless transitions
- **📱 Responsive Design**: Optimized experience across desktop, tablet, and mobile devices
- **⚡ Performance**: State-preserving navigation and optimized component architecture

## 🏗️ Architecture

### Tech Stack

- **React 18** - Modern React with concurrent features
- **TypeScript** - Full type safety and enhanced developer experience
- **Vite** - Lightning-fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework with custom design system
- **TanStack Table** - Powerful data tables with sorting, filtering, and pagination
- **React Router** - Client-side routing with custom state preservation
- **React Icons** - Comprehensive icon library

### Design Patterns

#### Custom Routing Strategy
Instead of traditional React Router component mounting/unmounting, the application uses a visibility-based routing system that preserves component state across navigation:

```tsx
// Components remain mounted, visibility is toggled
<div className={location.pathname === '/explore' ? 'block' : 'hidden'}>
  <Explore />
</div>
```

**Benefits:**
- Preserves form state and user inputs
- Eliminates component re-initialization overhead
- Maintains scroll positions and UI state
- Faster navigation between routes

#### Context-Driven State Management
Global application state is managed through React Context with localStorage persistence:

- **SiteSettingsContext**: Theme preferences and MLB Showdown set selection
- **Automatic persistence**: User preferences saved across sessions
- **SSR-safe utilities**: Graceful handling of server-side rendering scenarios

#### Component Architecture
```
src/components/
├── shared/           # Reusable UI components
├── side_menu/        # Navigation components
├── customs/          # Custom card builder
├── cards/           # Card explorer and display
└── AppLayout.tsx    # Main layout orchestrator
```

## 🎨 Design System

### Theme Management
- **Light Theme**: Clean, professional appearance for daytime use
- **Dark Theme**: Eye-friendly design for low-light environments  
- **System Theme**: Automatically follows OS/browser preference
- **Smooth Transitions**: Seamless switching between themes

### Responsive Breakpoints
- **Mobile First**: Designed for mobile devices, enhanced for larger screens
- **Adaptive Navigation**: Collapsible sidebar on desktop, overlay on mobile
- **Flexible Layouts**: Components adapt to various screen sizes
- **Touch-Friendly**: Optimized for touch interactions on mobile devices

### Visual Design
- **MLB Showdown Aesthetic**: Authentic recreation of original card designs
- **Clean Typography**: Readable fonts optimized for card statistics
- **Consistent Spacing**: Systematic spacing scale for visual harmony
- **Accessible Colors**: WCAG-compliant color contrasts across all themes

## 🚀 Development

### Prerequisites
- Node.js 18+ 
- npm or yarn package manager

### Getting Started

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```

3. **Open browser**
   Navigate to `http://localhost:5173`

### Available Scripts

- `npm run dev` - Start development server with hot reloading
- `npm run build` - Build production bundle
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint for code quality checks

### Development Features
- **Hot Module Replacement (HMR)** - Instant updates during development
- **TypeScript Integration** - Full type checking and IntelliSense
- **ESLint Configuration** - Consistent code style and error detection
- **Path Aliases** - Clean import statements with @ prefix

## 📁 Project Structure

```
frontend/
├── public/              # Static assets (images, icons)
├── src/
│   ├── components/      # React components
│   │   ├── shared/      # Reusable UI components
│   │   ├── side_menu/   # Navigation components
│   │   ├── customs/     # Custom card builder
│   │   └── cards/       # Card explorer
│   ├── types/           # TypeScript type definitions
│   ├── api/            # API integration utilities
│   └── functions/      # Utility functions
├── index.html          # HTML entry point
├── vite.config.ts      # Vite configuration
└── tailwind.config.js  # Tailwind CSS configuration
```

## 🎯 Key Components

### Custom Card Builder (`/customs`)
- **Player Search**: Integration with MLB statistics API
- **Visual Card Preview**: Real-time card generation
- **Statistics Input**: Intuitive forms for card attributes
- **Export Options**: Download cards in multiple formats

### Card Explorer (`/explore`)
- **Advanced Search**: Filter by player, team, position, set, and statistics
- **Data Tables**: Sortable, paginated results with TanStack Table
- **Card Display**: Modal previews with detailed card information
- **Responsive Grid**: Adaptive card layout for different screen sizes

### Navigation System
- **Collapsible Sidebar**: Desktop sidebar with smooth animations
- **Mobile Overlay**: Full-screen navigation for mobile devices
- **Route Detection**: Automatic active state highlighting
- **Theme Toggle**: Integrated theme switching functionality

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:5000
VITE_MLB_STATS_API_URL=https://statsapi.mlb.com

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_DEBUG_MODE=false
```

### Build Configuration
The application is configured for optimal production builds:
- **Code Splitting**: Automatic chunk splitting for better caching
- **Tree Shaking**: Elimination of unused code
- **Asset Optimization**: Compressed images and optimized bundles
- **Modern Browser Support**: ES2020+ with legacy fallbacks

## 🚀 Deployment

### Production Build
```bash
npm run build
```

The build output is generated in the `dist/` directory and includes:
- Optimized JavaScript bundles
- Compressed CSS files
- Static assets with cache-friendly filenames
- HTML with proper meta tags and favicons

### Deployment Targets
- **Static Hosting**: Netlify, Vercel, GitHub Pages
- **CDN**: CloudFront, Cloudflare
- **Traditional Hosting**: Apache, Nginx with proper SPA routing

## 🤝 Contributing

### Code Style
- **TypeScript**: All new code should use TypeScript with proper typing
- **ESLint**: Follow the established linting rules
- **Component Structure**: Use functional components with hooks
- **Documentation**: Add JSDoc comments for all public functions and components

### Development Workflow
1. Create feature branch from `main`
2. Implement changes with comprehensive documentation
3. Add or update tests as needed
4. Ensure all linting and type checking passes
5. Submit pull request with detailed description

## 📝 License

This project is part of the MLB Showdown Bot ecosystem. See the main repository for license information.
