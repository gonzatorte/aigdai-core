# Force Directed Graph Application

This project is a React TypeScript application that visualizes force-directed graphs using D3.js. It uses [Bun](https://bun.sh/) as the package manager and [esbuild](https://esbuild.github.io/) for fast builds.

## Prerequisites

Make sure you have Bun installed on your system. If not, install it using:

```bash
curl -fsSL https://bun.sh/install | bash
```

## Available Scripts

In the project directory, you can run:

### `bun start` or `bun run dev`

Runs the app in development mode with live reloading.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will automatically reload when you make changes to the source files.\
You may also see any lint errors in the console.

### `bun run build`

Builds the app for production to the `dist` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and ready for deployment.

### `bun run type-check`

Runs TypeScript type checking without emitting files.

### `bun run lint`

Runs ESLint to check for code quality issues.

### `bun run lint:fix`

Automatically fixes ESLint issues where possible.

### `bun run format`

Formats all source files using Prettier.

### `bun run format:check`

Checks if all files are properly formatted.

## Package Management

### Installing Dependencies

To install all dependencies:
```bash
bun install
```

To add a new dependency:
```bash
bun add <package-name>
```

To add a development dependency:
```bash
bun add -d <package-name>
```

### Running Scripts

All scripts can be run with Bun:
```bash
bun start          # Start development server
bun run build      # Build for production
bun run type-check # Type checking
bun run lint       # Code linting
bun run format     # Code formatting
```

## Technology Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **D3.js** - Data visualization
- **Bun** - Package manager and runtime
- **esbuild** - Fast bundler
- **live-server** - Development server with live reload
- **ESLint** - Code linting
- **Prettier** - Code formatting

## Notes

- **No favicon**: This application intentionally has no favicon to keep the setup minimal
- **No public assets**: All assets are bundled through esbuild

## Development Workflow

1. **Start development**: `bun run dev`
   - Builds the project initially
   - Starts esbuild in watch mode
   - Launches live-server with automatic browser reload
2. **Make changes**: Edit files in `src/`
   - esbuild automatically rebuilds on file changes
   - live-server automatically reloads the browser
3. **Stop development**: Press `Ctrl+C` to stop all processes

## Learn More

To learn React, check out the [React documentation](https://reactjs.org/).

To learn TypeScript, visit the [TypeScript documentation](https://www.typescriptlang.org/docs/).

To learn D3.js, check out the [D3.js documentation](https://d3js.org/).

To learn more about Bun, visit the [Bun documentation](https://bun.sh/docs).

To learn more about esbuild, visit the [esbuild documentation](https://esbuild.github.io/).


