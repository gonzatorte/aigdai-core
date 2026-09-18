const { spawn } = require('child_process');

console.log('🔨 Building project...');

// First, do an initial build
const buildProcess = spawn('bun', ['run', 'build.js'], {
  stdio: 'inherit',
  shell: true
});

buildProcess.on('close', (code) => {
  if (code !== 0) {
    console.error('❌ Build failed');
    process.exit(1);
  }
  
  console.log('✅ Initial build complete');
  console.log('🚀 Starting development server with live reload...');
  
  // Start the watch build process in the background
  const watchProcess = spawn('bun', ['run', 'build.js', '--watch', '--dev'], {
    stdio: 'inherit',
    shell: true
  });
  
  // Start the live-server process
  const serveProcess = spawn('bun', ['run', 'serve:dev'], {
    stdio: 'inherit',
    shell: true
  });
  
  // Handle process termination
  const cleanup = () => {
    console.log('\n🛑 Shutting down development server...');
    watchProcess.kill('SIGINT');
    serveProcess.kill('SIGINT');
    process.exit(0);
  };
  
  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
}); 