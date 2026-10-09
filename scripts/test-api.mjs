import { ensureSetup, run, python } from './runtime.mjs';
ensureSetup();
run(python,['-m','unittest','discover','-s','backend/tests','-v']);
