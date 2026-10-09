-- Company + opportunity join
SELECT c.name AS company, i.role, i.location, i.stipend, i.min_cgpa
FROM internships i JOIN companies c ON c.id = i.company_id
ORDER BY i.stipend DESC LIMIT 50;

-- Most requested skills
SELECT s.name AS skill, COUNT(isk.internship_id) AS opportunities
FROM skills s JOIN internship_skills isk ON isk.skill_id = s.id
GROUP BY s.id, s.name ORDER BY opportunities DESC LIMIT 50;

-- Student application pipeline
SELECT s.name AS student, c.name AS company, i.role, a.status
FROM applications a
JOIN students s ON s.id = a.student_id
JOIN internships i ON i.id = a.internship_id
JOIN companies c ON c.id = i.company_id
ORDER BY a.updated_at DESC LIMIT 50;

-- Eligibility using relational filters
SELECT c.name AS company, i.role, i.min_cgpa, s.cgpa AS student_cgpa
FROM students s CROSS JOIN internships i
JOIN companies c ON c.id = i.company_id
WHERE s.id = 1 AND s.cgpa >= i.min_cgpa AND s.year = i.eligible_year
AND (NOT EXISTS (SELECT 1 FROM internship_branches ib WHERE ib.internship_id = i.id)
     OR EXISTS (SELECT 1 FROM internship_branches ib
                WHERE ib.internship_id = i.id AND ib.branch_name = s.branch))
ORDER BY i.min_cgpa DESC LIMIT 50;

-- Transactional status history
SELECT c.name AS company, h.previous_status, h.new_status, h.changed_at
FROM application_history h
JOIN applications a ON a.id = h.application_id
JOIN internships i ON i.id = a.internship_id
JOIN companies c ON c.id = i.company_id
ORDER BY h.changed_at DESC LIMIT 50;

-- Upcoming timelines
SELECT c.name AS company, i.role, t.kind AS event, t.starts_at
FROM timeline_events t
JOIN internships i ON i.id = t.internship_id
JOIN companies c ON c.id = i.company_id
ORDER BY t.starts_at LIMIT 50;
