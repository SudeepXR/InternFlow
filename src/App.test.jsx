import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import fixtures from './test/fixtures.json';

let records, requests;
beforeEach(() => {
 records=structuredClone(fixtures);requests=[];
 global.fetch=vi.fn(async(url,options={})=>{
   const path=String(url).replace('/api/','');requests.push({path,...options});
   let result;
   if(path.endsWith('/bookmark')) {
     const id=Number(path.split('/')[1]);const item=records.internships.find(i=>i.id===id);item.bookmarked=!item.bookmarked;result={bookmarked:item.bookmarked};
   } else if(path.endsWith('/prepare')) {
     const id=Number(path.split('/')[1]);result=id===1?records['existing-app']:records['prepared-app'];
     if(!records.applications.some(a=>a.id===result.id))records.applications.push(result);
     else records.applications=records.applications.map(a=>a.id===result.id?result:a);
   } else if(path.startsWith('applications/')&&options.method==='PATCH') {
     const id=Number(path.split('/')[1]);const a=records.applications.find(a=>a.id===id);Object.assign(a,JSON.parse(options.body));result=a;
   } else if(path==='profile'&&options.method==='PUT') {
     records.profile={...records.profile,...JSON.parse(options.body)};result=records.profile;
   } else if(path==='extract/announcement')result=records.extraction;
   else if(path==='ingestions') {
     result=records['new-opportunity'];records.internships.push(result);
   } else if(path.startsWith('skill-gaps?'))result=records['skill-simulation'];
   else if(path.startsWith('database/queries/'))result=records['query-result'];
   else result=records[path];
   if(result===undefined)throw new Error('Unmocked API request: '+path);
   return new Response(JSON.stringify(result),{status:200,headers:{'Content-Type':'application/json'}});
 });
});
async function start() {const user=userEvent.setup();render(<App/>);await screen.findByRole('heading',{name:/Your next chapter/});return user;}
async function nav(user,name) {await user.click(within(screen.getByRole('navigation')).getByRole('button',{name}));}

describe('Student workflows',()=>{
 it('loads real API-shaped data and filters opportunities by search',async()=>{
   const user=await start();
   expect(screen.getAllByRole('article').length).toBe(12);
   await user.type(screen.getByRole('textbox',{name:'Search companies, roles or skills'}),'Razorpay');
   expect(screen.getAllByRole('article').length).toBe(1);
   expect(screen.getByRole('button',{name:/Frontend Engineering Intern/})).toBeTruthy();
 });
 it('persists a bookmark and shows it in saved opportunities',async()=>{
   const user=await start();
   const card=screen.getAllByRole('article').find(el=>el.textContent.includes('Razorpay'));
   await user.click(within(card).getByRole('button',{name:'Save internship'}));
   await screen.findByText('Opportunity saved to your shortlist');
   await nav(user,'Saved opportunities');
   expect(screen.getByRole('button',{name:/Frontend Engineering Intern/})).toBeTruthy();
   expect(requests.some(r=>r.path==='internships/2/bookmark'&&r.method==='POST')).toBe(true);
 });
 it('opens a match breakdown and prepares a reviewable application',async()=>{
   const user=await start();
   await user.click(screen.getByRole('button',{name:'Software Engineering Intern'}));
   const dialog=await screen.findByRole('dialog');
   expect(within(dialog).getByText('Your match, explained')).toBeTruthy();
   expect(within(dialog).getByText('C++ found in your profile')).toBeTruthy();
   await user.click(within(dialog).getByRole('button',{name:'View application'}));
   await screen.findByRole('dialog',{name:'Review your application'});
   expect(screen.getByRole('textbox',{name:'Edit cover letter'}).value).toContain('Alex Morgan');
   expect(screen.getByText('Form answers')).toBeTruthy();
 });
 it('extracts an announcement, requires review, and preserves the source on import',async()=>{
   const user=await start();await nav(user,'Announcement inbox');
   await user.click(screen.getByRole('button',{name:/Try a sample/}));
   const source=screen.getByRole('textbox',{name:'Internship announcement'}).value;
   await user.click(screen.getByRole('button',{name:/Extract opportunity/}));
   await screen.findByRole('heading',{name:'Review the details'});
   expect(screen.getByLabelText('Company').value).toBe('Nova Labs');
   expect(requests.filter(r=>r.path==='ingestions').length).toBe(0);
   await user.click(screen.getByRole('button',{name:/Confirm & import/}));
   await screen.findByText('Opportunity imported. Matches and calendar updated.');
   const imported=JSON.parse(requests.find(r=>r.path==='ingestions').body);
   expect(imported.source_text).toBe(source);
   expect(imported.announcement.company).toBe('Nova Labs');
 });
 it('saves an edited profile through the API',async()=>{
   const user=await start();await nav(user,'My profile');
   const name=screen.getByLabelText('Full name');
   await user.clear(name);await user.type(name,'Sam Rivera');
   await user.click(screen.getByRole('button',{name:/Save profile/}));
   await screen.findByText('Profile saved. Your matches have been recalculated.');
   expect(JSON.parse(requests.find(r=>r.path==='profile'&&r.method==='PUT').body).name).toBe('Sam Rivera');
 });
 it('simulates a missing skill without saving it to the profile',async()=>{
   const user=await start();await nav(user,'Skill roadmap');
   const docker=await screen.findByRole('button',{name:/Docker.*eligible opportunities/});
   await user.click(docker);
   await waitFor(()=>expect(requests.some(r=>r.path==='skill-gaps?extra=Docker')).toBe(true));
   expect(requests.some(r=>r.path==='profile'&&r.method==='PUT')).toBe(false);
   expect(await screen.findByText('+'+(fixtures['skill-simulation'].after-fixtures['skill-simulation'].before)+' opportunities at 80% or above')).toBeTruthy();
 });
 it('executes a named SQL example and displays relational results',async()=>{
   const user=await start();await nav(user,'Database explorer');
   await screen.findByText('A connected model');
   await user.click(screen.getByRole('button',{name:'SQL playground'}));
   await user.click(screen.getByRole('button',{name:'Run query'}));
   await screen.findByText(fixtures['query-result'].rows.length+' rows');
   expect(screen.getByRole('table')).toBeTruthy();
   expect(requests.some(r=>r.path==='database/queries/opportunities'&&r.method==='POST')).toBe(true);
 });
 it('shows calendar events and provides an ICS export',async()=>{
   const user=await start();await nav(user,'Calendar');
   expect(screen.getByRole('link',{name:'Export calendar'}).getAttribute('href')).toBe('/api/calendar/export');
   expect(screen.getByLabelText('Saved & applied only')).toBeTruthy();
   expect(screen.getByText(/All times are in Asia/)).toBeTruthy();
 });
 it('handles a disconnected backend with a retry action',async()=>{
   global.fetch=vi.fn().mockRejectedValue(new Error('Server unavailable'));
   render(<App/>);
   expect(await screen.findByRole('heading',{name:'Let’s get connected.'})).toBeTruthy();
   expect(screen.getByRole('button',{name:'Try again'})).toBeTruthy();
 });
});
