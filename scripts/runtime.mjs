import { spawnSync, spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const windows = process.platform === 'win32';
export const python = path.join(root, '.venv', windows ? 'Scripts/python.exe' : 'bin/python');
export const npm = windows ? 'npm.cmd' : 'npm';
export function run(command, args, options = {}) {
  const result = spawnSync(command, args, { cwd: root, stdio: 'inherit', windowsHide: true, shell: windows && command.endsWith('.cmd'), ...options });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(command + ' exited with code ' + result.status);
}
export function child(command, args) {
  return spawn(command, args, { cwd: root, stdio: 'inherit', windowsHide: true, shell: windows && command.endsWith('.cmd') });
}
export function ensureSetup() {
  if (!existsSync(python) || !existsSync(path.join(root, 'node_modules/vite'))) {
    console.error('Run npm run setup first to install the local dependencies.');
    process.exit(1);
  }
}
