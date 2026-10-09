import React, { useEffect, useRef } from 'react';
import { X, ArrowUpRight, Bookmark, MapPin, Clock3, Check, AlertCircle, BriefcaseBusiness, ChevronRight, Sparkles } from 'lucide-react';
import { date, daysLeft, money } from './api';
import { useApp } from './context';

export function IconButton({ label, children, ...props }) { return <button className="icon-button" aria-label={label} title={label} {...props}>{children}</button>; }
export function Empty({ icon: Icon = BriefcaseBusiness, title, description, action }) { return <div className="empty"><span className="empty-icon"><Icon size={28}/></span><h3>{title}</h3><p>{description}</p>{action}</div>; }
export function PageIntro({ eyebrow, title, text, action }) { return <div className="page-intro"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{text}</p></div>{action}</div>; }
export function CompanyLogo({ item, large = false }) {
  return <div className={'company-logo ' + (large ? 'large' : '')} style={{ '--company-color': item.color }}>
    {item.company === 'Microsoft' ? <span className="ms-grid"><i/><i/><i/><i/></span> : item.company === 'Google' ? <span className="google-g">G</span> : item.company === 'Amazon' ? <span className="amazon-a">a<span>⌣</span></span> : item.company === 'Atlassian' ? <span className="atlassian-a">A</span> : item.company.slice(0,1)}
  </div>;
}
export function MatchRing({ score, small = false }) { return <span className={'match-ring ' + (small ? 'small' : '')} style={{ '--score': score + '%' }}><span>{score}<small>%</small></span></span>; }
export function InternshipCard({ item }) {
  const { openOpportunity, toggleBookmark } = useApp();
  const left = daysLeft(item.dates.deadline);
  return <article className="internship-card">
    <div className="card-top"><CompanyLogo item={item}/><div className="company-info"><strong>{item.company}</strong><span>{item.domain}</span></div><IconButton label={item.bookmarked ? 'Remove saved internship' : 'Save internship'} className={'icon-button bookmark ' + (item.bookmarked ? 'is-saved' : '')} onClick={() => toggleBookmark(item.id)}><Bookmark size={18} fill={item.bookmarked ? 'currentColor' : 'none'}/></IconButton></div>
    <button className="card-title" onClick={() => openOpportunity(item.id)}>{item.role}<ArrowUpRight size={18}/></button>
    <div className="card-meta"><span><MapPin size={13}/>{item.location}</span><i/> <span>{item.work_mode}</span></div>
    <div className="card-pay"><strong>{item.stipend ? '₹' + money(item.stipend) : 'Unpaid'}<small>{item.stipend ? ' / month' : ''}</small></strong><span><Clock3 size={13}/>{item.duration_months} months</span></div>
    <div className="skill-tags">{item.skills.slice(0,3).map(s => <span key={s} className={item.match.missing_skills.includes(s) ? 'gap' : ''}>{s}</span>)}{item.skills.length > 3 && <span>+{item.skills.length - 3}</span>}</div>
    <div className="card-match"><MatchRing score={item.match.score} small/><div><strong>{!item.match.eligible ? 'Eligibility gap' : item.match.score >= 80 ? 'Strong match' : 'Room to grow'}</strong><span>{item.match.matched_skills.length} of {item.skills.length} skills match</span></div><button onClick={() => openOpportunity(item.id)} aria-label={'View match for ' + item.company}><ChevronRight size={18}/></button></div>
    <div className="card-bottom"><span className={item.closed ? 'closed' : left <= 4 ? 'urgent' : ''}><span className="status-dot"/>{item.closed ? 'Closed' : left === 0 ? 'Closes today' : left === 1 ? 'Closes tomorrow' : 'Closes ' + date(item.dates.deadline)}</span><span>{item.application ? item.application.status : item.is_demo ? 'Sample listing' : 'Imported'}</span></div>
  </article>;
}
export function Modal({ children, title, onClose, wide = false }) {
  const dialog = useRef(null);
  useEffect(() => {
    const previous = document.activeElement;
    dialog.current?.showModal();
    const close = e => { e.preventDefault(); onClose(); };
    const el = dialog.current; el?.addEventListener('cancel', close);
    document.body.style.overflow = 'hidden';
    return () => { el?.removeEventListener('cancel', close); document.body.style.overflow = ''; previous?.focus(); };
  }, []);
  return <dialog ref={dialog} className={'modal ' + (wide ? 'wide' : '')} aria-label={title} onClick={e => { if (e.target === dialog.current) onClose(); }}><div className="modal-head"><span>{title}</span><IconButton label="Close dialog" onClick={onClose}><X size={20}/></IconButton></div>{children}</dialog>;
}
export function OpportunityModal({ item, onClose }) {
  const { toggleBookmark, prepareApplication } = useApp();
  return <Modal title="Opportunity details" onClose={onClose} wide><div className="opportunity-detail">
    <div className="detail-title"><CompanyLogo item={item} large/><div><div className="eyebrow">{item.company}</div><h2>{item.role}</h2><p>{item.location} · {item.work_mode} · {item.duration_months} months</p></div><MatchRing score={item.match.score}/></div>
    {item.is_demo && <div className="info-note"><AlertCircle size={16}/>Fictional listing for the course demo. No real hiring dates or availability are implied.</div>}
    <div className="detail-columns"><section><h3>What you’ll work on</h3><p className="body-copy">{item.description}</p><h3>At a glance</h3><div className="detail-facts"><div><span>Stipend</span><strong>{item.stipend ? '₹' + money(item.stipend) + ' / month' : 'Unpaid'}</strong></div><div><span>Minimum CGPA</span><strong>{item.min_cgpa} / 10</strong></div><div><span>Eligible year</span><strong>Year {item.eligible_year}</strong></div><div><span>Branches</span><strong>{item.eligible_branch}</strong></div></div><h3>Timeline · IST</h3><div className="detail-timeline">{[['deadline','Application deadline'],['ppt','Pre-placement talk'],['oa','Online assessment']].map(([kind,label]) => <div key={kind}><span className={'event-dot ' + kind}/><span>{label}</span><strong>{date(item.dates[kind], { hour: '2-digit', minute: '2-digit' })}</strong></div>)}</div></section>
    <section className="match-panel"><div className="section-title"><h3><Sparkles size={17}/>Your match, explained</h3><span className="pill">Rule based</span></div>{item.match.factors.map(f => <div className="factor" key={f.name}><div><span>{f.name}</span><strong>{f.score}/{f.max}</strong></div><div className="bar"><i style={{ width: f.score / f.max * 100 + '%' }}/></div><small>{f.detail}</small></div>)}
    <div className="match-checks">{item.match.matched_skills.map(s => <span key={s}><Check size={14}/>{s} found in your profile</span>)}{item.match.missing_skills.map(s => <span className="warning" key={s}><AlertCircle size={14}/>{s} is a skill gap</span>)}{item.match.eligibility_reasons.map(r => <span className="warning" key={r}><AlertCircle size={14}/>{r}</span>)}</div>
    {!item.match.eligible && <p className="muted small-text">Eligibility is a hard gate. The recommendation score is capped at 49%.</p>}</section></div>
    <div className="modal-footer"><button className="button secondary" onClick={() => toggleBookmark(item.id)}><Bookmark size={16}/>{item.bookmarked ? 'Saved' : 'Save opportunity'}</button><button className="button primary" disabled={(!item.match.eligible || item.closed) && !item.application} onClick={() => prepareApplication(item.id)}>{item.application ? 'View application' : 'Prepare application'}<ArrowUpRight size={16}/></button></div>
  </div></Modal>;
}
