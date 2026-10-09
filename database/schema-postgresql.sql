-- InternFlow schema. Generated from backend/models.py.
-- Run against an empty database; app startup creates and seeds tables automatically.


CREATE TABLE branches (
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (name)
);

CREATE TABLE companies (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	color VARCHAR(20), 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE documents (
	id VARCHAR(36) NOT NULL, 
	kind VARCHAR(40) NOT NULL, 
	payload TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_documents_kind ON documents (kind);

CREATE TABLE skills (
	id SERIAL NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE internships (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	role VARCHAR(180) NOT NULL, 
	domain VARCHAR(80) NOT NULL, 
	location VARCHAR(120) NOT NULL, 
	work_mode VARCHAR(30) NOT NULL, 
	stipend INTEGER NOT NULL, 
	duration_months INTEGER NOT NULL, 
	min_cgpa FLOAT NOT NULL, 
	eligible_year INTEGER NOT NULL, 
	experience_months INTEGER NOT NULL, 
	description TEXT NOT NULL, 
	application_url TEXT, 
	source VARCHAR(100), 
	is_demo BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (min_cgpa >= 0 AND min_cgpa <= 10), 
	CHECK (eligible_year >= 1 AND eligible_year <= 5), 
	CHECK (stipend >= 0), 
	CHECK (duration_months >= 1 AND duration_months <= 24), 
	CHECK (experience_months >= 0), 
	CHECK (work_mode IN ('On-site','Remote','Hybrid')), 
	UNIQUE (company_id, role, location), 
	FOREIGN KEY(company_id) REFERENCES companies (id)
);

CREATE INDEX ix_internships_company_id ON internships (company_id);

CREATE TABLE students (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	email VARCHAR(200) NOT NULL, 
	college VARCHAR(200) NOT NULL, 
	branch VARCHAR(100) NOT NULL, 
	year INTEGER NOT NULL, 
	cgpa FLOAT NOT NULL, 
	graduation_year INTEGER NOT NULL, 
	bio TEXT, 
	experience_months INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (cgpa >= 0 AND cgpa <= 10), 
	CHECK (year >= 1 AND year <= 5), 
	CHECK (experience_months >= 0), 
	UNIQUE (email), 
	FOREIGN KEY(branch) REFERENCES branches (name)
);

CREATE TABLE applications (
	id SERIAL NOT NULL, 
	student_id INTEGER NOT NULL, 
	internship_id INTEGER NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	cover_letter TEXT, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (student_id, internship_id), 
	CHECK (status IN ('Draft','Applied','Assessment','Interview','Offer','Rejected','Withdrawn')), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE, 
	FOREIGN KEY(internship_id) REFERENCES internships (id) ON DELETE CASCADE
);

CREATE INDEX ix_applications_student_id ON applications (student_id);

CREATE TABLE bookmarks (
	student_id INTEGER NOT NULL, 
	internship_id INTEGER NOT NULL, 
	PRIMARY KEY (student_id, internship_id), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE, 
	FOREIGN KEY(internship_id) REFERENCES internships (id) ON DELETE CASCADE
);

CREATE TABLE ingestions (
	id SERIAL NOT NULL, 
	source_hash VARCHAR(64) NOT NULL, 
	internship_id INTEGER NOT NULL, 
	document_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (source_hash), 
	FOREIGN KEY(internship_id) REFERENCES internships (id)
);

CREATE TABLE internship_branches (
	internship_id INTEGER NOT NULL, 
	branch_name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (internship_id, branch_name), 
	FOREIGN KEY(internship_id) REFERENCES internships (id) ON DELETE CASCADE, 
	FOREIGN KEY(branch_name) REFERENCES branches (name)
);

CREATE TABLE internship_skills (
	internship_id INTEGER NOT NULL, 
	skill_id INTEGER NOT NULL, 
	PRIMARY KEY (internship_id, skill_id), 
	FOREIGN KEY(internship_id) REFERENCES internships (id) ON DELETE CASCADE, 
	FOREIGN KEY(skill_id) REFERENCES skills (id)
);

CREATE TABLE preferences (
	id SERIAL NOT NULL, 
	student_id INTEGER NOT NULL, 
	kind VARCHAR(20) NOT NULL, 
	value VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (student_id, kind, value), 
	CHECK (kind IN ('domain','location')), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE INDEX ix_preferences_student_id ON preferences (student_id);

CREATE TABLE projects (
	id SERIAL NOT NULL, 
	student_id INTEGER NOT NULL, 
	title VARCHAR(160) NOT NULL, 
	description TEXT, 
	domain VARCHAR(80) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE INDEX ix_projects_student_id ON projects (student_id);

CREATE TABLE student_skills (
	student_id INTEGER NOT NULL, 
	skill_id INTEGER NOT NULL, 
	PRIMARY KEY (student_id, skill_id), 
	FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE, 
	FOREIGN KEY(skill_id) REFERENCES skills (id)
);

CREATE TABLE timeline_events (
	id SERIAL NOT NULL, 
	internship_id INTEGER NOT NULL, 
	kind VARCHAR(20) NOT NULL, 
	starts_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (internship_id, kind), 
	CHECK (kind IN ('deadline','oa','ppt')), 
	FOREIGN KEY(internship_id) REFERENCES internships (id) ON DELETE CASCADE
);

CREATE INDEX ix_timeline_events_starts_at ON timeline_events (starts_at);

CREATE INDEX ix_timeline_events_internship_id ON timeline_events (internship_id);

CREATE TABLE application_history (
	id SERIAL NOT NULL, 
	application_id INTEGER NOT NULL, 
	previous_status VARCHAR(30), 
	new_status VARCHAR(30) NOT NULL, 
	changed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE CASCADE
);

CREATE INDEX ix_application_history_application_id ON application_history (application_id);
