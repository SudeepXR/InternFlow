import { existsSync } from 'node:fs';
import { root, windows, python, npm, run } from './runtime.mjs';
import path from 'node:path';
console.log('Setting up InternFlow…');
if (!existsSync(python)) run(windows ? 'python' : 'python3', ['-m', 'venv', '.venv']);
const requirements = process.argv.includes('--integrations') ? 'backend/requirements-integrations.txt' : 'backend/requirements.txt';
run(python, ['-m', 'pip', 'install', '-r', requirements]);
run(npm, ['install', '--no-audit', '--no-fund', '--cache', path.join(root, '.npm-cache')]);
console.log('\nReady. Run npm start for the built app, or npm run dev for live development.');
