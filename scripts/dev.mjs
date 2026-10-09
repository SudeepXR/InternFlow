import { ensureSetup, child, python, npm } from './runtime.mjs';
ensureSetup();
console.log('Starting API on :8000 and React development server on :5173…');
const api=child(python,['-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000','--reload']);
const web=child(npm,['run','dev:web']);
let stopping=false;
function stop(code=0) { if(stopping)return;stopping=true;api.kill();web.kill();setTimeout(()=>process.exit(code),250); }
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>stop());
api.on('exit',code=>stop(code||0));web.on('exit',code=>stop(code||0));
