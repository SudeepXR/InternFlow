export async function api(path, options = {}) {
  const response = await fetch('/api' + path, { ...options, headers: options.body instanceof FormData ? options.headers : { 'Content-Type': 'application/json', ...options.headers } });
  if (!response.ok) {
    let result; try { result = await response.json(); } catch { throw new Error('Could not reach InternFlow. Check that the backend is running.'); }
    const detail = result.detail;
    throw new Error(Array.isArray(detail) ? detail.map(d => d.loc.slice(1).join('.') + ': ' + d.msg).join('; ') : detail || 'Something went wrong');
  }
  return response.json();
}
export const send = (method, body) => ({ method, body: JSON.stringify(body) });
export const money = value => new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(value);
export const date = (value, opts = {}) => value ? new Date(value).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: 'numeric', month: 'short', ...opts }) : 'Not scheduled';
export const time = value => new Date(value).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' });
export const daysLeft = value => value ? Math.ceil((new Date(value) - Date.now()) / 86400000) : null;
export const initials = name => name.split(' ').slice(0,2).map(n => n[0]).join('');
export const eventName = kind => ({ deadline: 'Application deadline', oa: 'Online assessment', ppt: 'Pre-placement talk' }[kind]);
export const localInput = value => value ? new Date(new Date(value).getTime() + 330 * 60000).toISOString().slice(0,16) : '';
export const fromLocalInput = value => value ? value + ':00+05:30' : null;
