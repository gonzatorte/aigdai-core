const esbuild = require('esbuild');
const path = require('path');
const dotenv = require('dotenv');

// Development build
async function build() {
  // Load environment variables
  dotenv.config();
  
  const isWatch = process.argv.includes('--watch');
  const isDev = process.argv.includes('--dev');

  const envs = {
    NODE_ENV: isDev ? 'development' : 'production',
    STAGE: process.env.STAGE || (isDev ? 'development' : 'production'),
    SPARQL_API_URL: process.env.SPARQL_API_URL || '',
  };
  const envsInline = Object.fromEntries(
    Object.entries(envs).map(
      ([key, value]) => [`process.env.${key}`, JSON.stringify(value)],
    ),
  );

  const context = await esbuild.context({
    entryPoints: ['src/index.tsx'],
    bundle: true,
    outdir: 'dist',
    format: 'iife',
    target: ['chrome58', 'firefox57', 'safari11'],
    sourcemap: isDev,
    minify: !isDev,
    loader: {
      // '.json': 'json',
      '.css': 'css',
    },
    define: {
      ...envsInline,
      'process.env': JSON.stringify(envs),
    },
    plugins: [
      {
        name: 'html-plugin',
        setup(build) {
          build.onEnd(async () => {
            const fs = require('fs');
            const htmlContent = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta
      name="description"
      content="Force Directed Graph Application"
    />
          <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>" />
    <title>Force Directed Graph</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
    <script src="index.js"></script>
  </body>
</html>`;
            
            fs.writeFileSync(path.join('dist', 'index.html'), htmlContent);
          });
        },
      },
    ],
  });

  if (isWatch) {
    await context.watch();
    console.log('Watching for changes...');
  } else {
    await context.rebuild();
    context.dispose();
  }
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
}); 