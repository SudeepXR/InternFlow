import React, { useCallback, useEffect, useState } from 'react';
import { Compass, Bookmark, BriefcaseBusiness, CalendarDays, Inbox, ChartNoAxesCombined, UserRound, Database, Bell, ChevronDown, ArrowUpRight, Menu, X, CircleHelp, RefreshCw, Check, TriangleAlert } from 'lucide-react';
import { api, initials, date, time } from './api';
import { AppContext } from './context';
import { IconButton, OpportunityModal } from './components';
import Discover from './Discover';
import { Applications, ApplicationModal, Calendar } from './Workflow';
import { Profile, InboxPage, SkillRoadmap } from './Intelligence';
import DatabasePage from './Database';

const nav = [
  ['discover','Discover',Compass],['saved','Saved opportunities',Bookmark],['applications','My applications',BriefcaseBusiness],['calendar','Calendar',CalendarDays],
  ['inbox','Announcement inbox',Inbox],['skills','Skill roadmap',ChartNoAxesCombined],['profile','My profile',UserRound],['database','Database explorer',Database]
];
export default function App() {
  const [page, setPage] = useState('discover');
  const [data,setData] = useState(null);
  const [error,setError] = useState('');
  const [loading,setLoading] = useState(true);
  const [toast,setToast] = useState(null);
  const [detail,setDetail] = useState(null);
  const [application,setApplication] = useState(null);
  const [mobile,setMobile] = useState(false);
  const [bells,setBells] = useState(false);
  const notify = useCallback((message,type='success') => setToast({ message,type }),[]);
  const refresh = useCallback(async () => {
    const [profile,opportunities,dashboard,applications,events,health] = await Promise.all(['/profile','/internships','/dashboard','/applications','/calendar','/health'].map(p => api(p)));
    setData({ profile,opportunities,dashboard,applications,events,health }); setError('');
  },[]);
  useEffect(() => { refresh().catch(e => setError(e.message)).finally(() => setLoading(false)); },[refresh]);
  useEffect(() => { if(toast) { const t = setTimeout(() => setToast(null),4500); return () => clearTimeout(t); } },[toast]);
  const navigate = p => { setPage(p); setMobile(false); setBells(false); window.scrollTo({ top:0 }); };
  const toggleBookmark = async id => { try { const r=await api('/internships/'+id+'/bookmark',{method:'POST'}); await refresh(); notify(r.bookmarked ? 'Opportunity saved to your shortlist' : 'Opportunity removed from saved'); } catch(e) { notify(e.message,'error'); } };
  const prepareApplication = async id => { try { const r=await api('/internships/'+id+'/prepare',{method:'POST'}); await refresh(); setDetail(null); setApplication(r.id); } catch(e) { notify(e.message,'error'); } };
  const value={data,refresh,notify,navigate,toggleBookmark,prepareApplication,openOpportunity:setDetail,openApplication:setApplication};
  const title=nav.find(n => n[0]===page)?.[1];
  return <AppContext.Provider value={value}><div className="app-shell">
    {mobile && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setMobile(false)}/>}
    <aside className={'sidebar '+(mobile ? 'mobile-open' : '')}>
      <button className="brand" onClick={() => navigate('discover')} aria-label="InternFlow home"><span className="brand-mark"><span/><span/><span/></span>internflow<span className="brand-period">.</span></button>
      <div className="workspace-label"><span className="workspace-dot"/>STUDENT WORKSPACE</div>
      <nav aria-label="Main navigation">{nav.map(([id,label,Icon],idx) => <React.Fragment key={id}>{idx===4 && <div className="nav-divider"><span>YOUR TOOLKIT</span></div>}<button aria-label={label} aria-current={page===id ? 'page' : undefined} className={'nav-item '+(page===id ? 'active' : '')} onClick={() => navigate(id)}><Icon size={19}/><span>{label}</span>{id==='saved' && data && <small>{data.opportunities.filter(i => i.bookmarked).length}</small>}{id==='inbox' && <span className="new-dot"/>}</button></React.Fragment>)}</nav>
      <div className="sidebar-bottom"><div className="profile-nudge"><span className="nudge-icon">✦</span><h4>A profile that opens doors.</h4><p>Keep your skills up to date for better recommendations.</p><button onClick={() => navigate('profile')}>Improve my profile<ArrowUpRight size={15}/></button></div><button className="sidebar-user" onClick={() => navigate('profile')}><span className="avatar">{initials(data?.profile.name || 'Demo Student')}</span><span><strong>{data?.profile.name || 'Demo student'}</strong><small>Student account</small></span><ChevronDown size={16}/></button><div className="sidebar-footnote">Built for your next chapter <span>↗</span></div></div>
    </aside>
    <main className="main-shell"><header className="topbar"><div className="topbar-path"><IconButton label="Open navigation" className="icon-button mobile-menu" onClick={() => setMobile(!mobile)}><Menu size={21}/></IconButton><span>Workspace</span><span className="path-slash">/</span><strong>{title}</strong></div><div className="topbar-actions"><span className="demo-badge">COURSE DEMO</span><div className="notification-wrap"><IconButton label="Upcoming reminders" onClick={() => setBells(!bells)}><Bell size={19}/>{!!data?.dashboard.notifications.length && <span className="bell-dot"/>}</IconButton>{bells && <div className="notification-panel"><h3>Coming up soon <span>{data?.dashboard.notifications.length || 0}</span></h3><p className="muted small-text">In-app reminders for the next 3 days · IST</p>{data?.dashboard.notifications.length ? data.dashboard.notifications.map(e => <button key={e.id} onClick={() => { setDetail(e.internship_id); setBells(false); }}><span className={'event-dot '+e.kind}/><span><strong>{e.message}</strong><small>{date(e.starts_at)} · {time(e.starts_at)}</small></span></button>) : <p className="muted">You’re all caught up.</p>}<button className="text-button" onClick={() => navigate('calendar')}>View calendar<ArrowUpRight size={14}/></button></div>}</div><button className="top-avatar avatar" onClick={() => navigate('profile')} aria-label="Open profile">{initials(data?.profile.name || 'Demo Student')}</button></div></header>
      <div className="page-content">{loading ? <div className="loading-screen"><span className="loader"/><h2>Finding your next chapter…</h2><p>Loading your profile and opportunities.</p></div> : error ? <div className="error-screen"><TriangleAlert size={32}/><h2>Let’s get connected.</h2><p>{error}</p><p className="muted">Start the backend on port 8000, then try again.</p><button className="button primary" onClick={() => { setLoading(true); refresh().catch(e => setError(e.message)).finally(() => setLoading(false)); }}><RefreshCw size={16}/>Try again</button></div> : <>
      {(page==='discover' || page==='saved') && <Discover savedOnly={page==='saved'}/>}
      {page==='applications' && <Applications/>}{page==='calendar' && <Calendar/>}{page==='inbox' && <InboxPage/>}{page==='skills' && <SkillRoadmap/>}{page==='profile' && <Profile/>}{page==='database' && <DatabasePage/>}
      <footer className="page-footer"><span>Thoughtful opportunities. Clear next steps.</span><span><span className="status-dot"/> {data.health.relational === 'sqlite' ? 'SQLite' : 'PostgreSQL'} connected · {data.health.ai.enabled ? 'AI available' : 'Local intelligence'}</span></footer></>}</div>
    </main>
    {detail && data && <OpportunityModal item={data.opportunities.find(i => i.id===detail)} onClose={() => setDetail(null)}/>}
    {application && data && <ApplicationModal application={data.applications.find(a => a.id===application)} onClose={() => setApplication(null)}/>}
    {toast && <div className={'toast '+toast.type} role="status">{toast.type==='error' ? <TriangleAlert size={18}/> : <Check size={18}/>}<span>{toast.message}</span><IconButton label="Dismiss notification" onClick={() => setToast(null)}><X size={16}/></IconButton></div>}
  </div></AppContext.Provider>;
}
