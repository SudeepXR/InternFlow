import { ensureSetup, run, child, python, npm } from './runtime.mjs';
ensureSetup();
run(npm, ['run', 'build']);
console.log('\nInternFlow: http://127.0.0.1:8000\nAPI docs: http://127.0.0.1:8000/docs\n');
const server=child(python,['-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000']);
for (const signal of ['SIGINT','SIGTERM']) process.on(signal,()=>server.kill(signal));
server.on('exit',code=>process.exit(code || 0));
