-- ============================================================
-- CampusHire - sample data
-- Demo password for every seeded account: password123
-- ============================================================
USE campushire;

-- ------------------------------------------------------------
-- Lookups
-- ------------------------------------------------------------
INSERT INTO branch (branch_id, branch_name) VALUES
    (1, 'CSE'),
    (2, 'IT'),
    (3, 'ECE'),
    (4, 'Mechanical'),
    (5, 'Civil');

INSERT INTO skill (skill_id, skill_name) VALUES
    (1, 'Python'),
    (2, 'Java'),
    (3, 'C++'),
    (4, 'SQL'),
    (5, 'JavaScript'),
    (6, 'React'),
    (7, 'Node.js'),
    (8, 'Machine Learning'),
    (9, 'Data Structures'),
    (10, 'Algorithms'),
    (11, 'Cloud Computing'),
    (12, 'Docker'),
    (13, 'Spring Boot'),
    (14, 'HTML/CSS'),
    (15, 'Git'),
    (16, 'Communication'),
    (17, 'Problem Solving'),
    (18, 'Django');

INSERT INTO company (company_id, company_name, industry, website, hr_contact, location) VALUES
    (1, 'Apex Quantum Technologies', 'Artificial Intelligence', 'https://apexquantum.example.com', 'hr@apexquantum.com', 'Bengaluru'),
    (2, 'Vanguard Systems', 'Enterprise Software', 'https://vanguard.example.com', 'careers@vanguard.com', 'Hyderabad'),
    (3, 'Zenith Corp', 'Analytics', 'https://zenithcorp.example.com', 'talent@zenithcorp.com', 'Pune'),
    (4, 'Nexus Industries', 'Product Engineering', 'https://nexusind.example.com', 'hiring@nexusind.com', 'Gurugram'),
    (5, 'Optima Solutions', 'Cloud Services', 'https://optimasol.example.com', 'jobs@optimasol.com', 'Noida');

-- ------------------------------------------------------------
-- Users (password: password123)
-- ------------------------------------------------------------
INSERT INTO app_user (user_id, email, password_hash, full_name, role, phone) VALUES
    (1, 'meera.iyer@campushire.edu', SHA2('password123', 256), 'Dr. Meera Iyer', 'officer', '9810000001'),
    (2, 'sanjay.rao@campushire.edu', SHA2('password123', 256), 'Sanjay Rao', 'officer', '9810000002'),
    (3, 'hr@apexquantum.com', SHA2('password123', 256), 'Ritu Malhotra', 'recruiter', '9810000003'),
    (4, 'careers@vanguard.com', SHA2('password123', 256), 'Sameer Kulkarni', 'recruiter', '9810000004'),
    (5, 'talent@zenithcorp.com', SHA2('password123', 256), 'Neha Bansal', 'recruiter', '9810000005'),
    (6, 'hiring@nexusind.com', SHA2('password123', 256), 'Aakash Bhatia', 'recruiter', '9810000006'),
    (7, 'jobs@optimasol.com', SHA2('password123', 256), 'Pooja Menon', 'recruiter', '9810000007'),
    (8, 'student1@campus.edu', SHA2('password123', 256), 'Aarav Sharma', 'student', '9820000001'),
    (9, 'student2@campus.edu', SHA2('password123', 256), 'Priya Patel', 'student', '9820000002'),
    (10, 'student3@campus.edu', SHA2('password123', 256), 'Karan Singh', 'student', '9820000003'),
    (11, 'student4@campus.edu', SHA2('password123', 256), 'Simran Kaur', 'student', '9820000004'),
    (12, 'student5@campus.edu', SHA2('password123', 256), 'Rohit Das', 'student', '9820000005'),
    (13, 'student6@campus.edu', SHA2('password123', 256), 'Ananya Roy', 'student', '9820000006'),
    (14, 'student7@campus.edu', SHA2('password123', 256), 'Vikram Malhotra', 'student', '9820000007'),
    (15, 'student8@campus.edu', SHA2('password123', 256), 'Nisha Gupta', 'student', '9820000008'),
    (16, 'student9@campus.edu', SHA2('password123', 256), 'Arjun Mehta', 'student', '9820000009'),
    (17, 'student10@campus.edu', SHA2('password123', 256), 'Divya Singh', 'student', '9820000010'),
    (18, 'student11@campus.edu', SHA2('password123', 256), 'Rohan Verma', 'student', '9820000011'),
    (19, 'student12@campus.edu', SHA2('password123', 256), 'Sneha Reddy', 'student', '9820000012'),
    (20, 'student13@campus.edu', SHA2('password123', 256), 'Aditya Kulkarni', 'student', '9820000013'),
    (21, 'student14@campus.edu', SHA2('password123', 256), 'Ishita Bose', 'student', '9820000014'),
    (22, 'student15@campus.edu', SHA2('password123', 256), 'Manav Joshi', 'student', '9820000015'),
    (23, 'student16@campus.edu', SHA2('password123', 256), 'Tanvi Shah', 'student', '9820000016'),
    (24, 'student17@campus.edu', SHA2('password123', 256), 'Farhan Ali', 'student', '9820000017'),
    (25, 'student18@campus.edu', SHA2('password123', 256), 'Kavya Nair', 'student', '9820000018'),
    (26, 'student19@campus.edu', SHA2('password123', 256), 'Dev Chatterjee', 'student', '9820000019'),
    (27, 'student20@campus.edu', SHA2('password123', 256), 'Riya Kapoor', 'student', '9820000020');

INSERT INTO placement_officer (officer_id, user_id, department) VALUES
    (1, 1, 'Training and Placement Cell'),
    (2, 2, 'Training and Placement Cell');

INSERT INTO recruiter (recruiter_id, user_id, company_id, designation) VALUES
    (1, 3, 1, 'Talent Acquisition Lead'),
    (2, 4, 2, 'HR Manager'),
    (3, 5, 3, 'Campus Recruiter'),
    (4, 6, 4, 'Hiring Manager'),
    (5, 7, 5, 'People Operations');

-- ------------------------------------------------------------
-- Students
-- ------------------------------------------------------------
INSERT INTO student (student_id, user_id, roll_no, branch_id, batch_year, cgpa, backlogs) VALUES
    (1, 8, 'CS2027001', 1, 2027, 9.10, 0),
    (2, 9, 'CS2027002', 1, 2027, 8.80, 0),
    (3, 10, 'IT2027003', 2, 2027, 8.20, 0),
    (4, 11, 'EC2027004', 3, 2027, 7.90, 1),
    (5, 12, 'CS2027005', 1, 2027, 7.40, 0),
    (6, 13, 'IT2027006', 2, 2027, 9.30, 0),
    (7, 14, 'ME2027007', 4, 2027, 7.10, 2),
    (8, 15, 'EC2027008', 3, 2027, 8.60, 0),
    (9, 16, 'CS2027009', 1, 2027, 6.90, 0),
    (10, 17, 'CE2027010', 5, 2027, 7.70, 0),
    (11, 18, 'IT2027011', 2, 2027, 8.40, 0),
    (12, 19, 'CS2027012', 1, 2027, 9.00, 0),
    (13, 20, 'EC2027013', 3, 2027, 7.30, 1),
    (14, 21, 'ME2027014', 4, 2027, 8.00, 0),
    (15, 22, 'CS2027015', 1, 2027, 7.80, 0),
    (16, 23, 'IT2027016', 2, 2027, 8.10, 0),
    (17, 24, 'CE2027017', 5, 2027, 6.60, 2),
    (18, 25, 'EC2027018', 3, 2027, 8.90, 0),
    (19, 26, 'ME2027019', 4, 2027, 7.60, 0),
    (20, 27, 'CS2027020', 1, 2027, 8.50, 0);

INSERT INTO student_skill (student_id, skill_id, proficiency) VALUES
    (1, 1, 'Advanced'), (1, 4, 'Advanced'), (1, 9, 'Intermediate'), (1, 15, 'Intermediate'),
    (2, 1, 'Advanced'), (2, 4, 'Intermediate'), (2, 8, 'Intermediate'), (2, 9, 'Advanced'),
    (3, 2, 'Advanced'), (3, 4, 'Intermediate'), (3, 13, 'Intermediate'), (3, 15, 'Intermediate'),
    (4, 4, 'Intermediate'), (4, 5, 'Advanced'), (4, 6, 'Advanced'), (4, 14, 'Advanced'),
    (5, 2, 'Intermediate'), (5, 4, 'Intermediate'), (5, 12, 'Intermediate'), (5, 15, 'Advanced'),
    (6, 1, 'Advanced'), (6, 4, 'Advanced'), (6, 8, 'Advanced'), (6, 9, 'Advanced'),
    (7, 5, 'Intermediate'), (7, 6, 'Intermediate'), (7, 14, 'Advanced'),
    (8, 2, 'Intermediate'), (8, 4, 'Intermediate'), (8, 11, 'Intermediate'), (8, 12, 'Advanced'),
    (9, 1, 'Intermediate'), (9, 4, 'Intermediate'), (9, 15, 'Intermediate'),
    (10, 4, 'Advanced'), (10, 14, 'Intermediate'), (10, 16, 'Advanced'),
    (11, 2, 'Advanced'), (11, 4, 'Intermediate'), (11, 12, 'Intermediate'), (11, 13, 'Advanced'),
    (12, 1, 'Advanced'), (12, 4, 'Advanced'), (12, 8, 'Intermediate'), (12, 9, 'Advanced'),
    (13, 4, 'Intermediate'), (13, 5, 'Advanced'), (13, 6, 'Advanced'), (13, 7, 'Intermediate'),
    (14, 5, 'Advanced'), (14, 6, 'Advanced'), (14, 11, 'Intermediate'), (14, 12, 'Intermediate'),
    (15, 1, 'Intermediate'), (15, 4, 'Intermediate'), (15, 9, 'Intermediate'),
    (16, 2, 'Advanced'), (16, 4, 'Intermediate'), (16, 13, 'Intermediate'), (16, 15, 'Advanced'),
    (17, 4, 'Intermediate'), (17, 14, 'Intermediate'), (17, 16, 'Advanced'),
    (18, 5, 'Advanced'), (18, 6, 'Advanced'), (18, 8, 'Intermediate'), (18, 11, 'Intermediate'),
    (19, 4, 'Intermediate'), (19, 11, 'Intermediate'), (19, 12, 'Advanced'), (19, 15, 'Intermediate'),
    (20, 1, 'Advanced'), (20, 4, 'Intermediate'), (20, 8, 'Intermediate'), (20, 9, 'Advanced');

-- ------------------------------------------------------------
-- Jobs and requirements
-- ------------------------------------------------------------
INSERT INTO job (job_id, company_id, job_title, job_description, job_type, location,
                 ctc, min_cgpa, max_backlogs, openings, application_deadline, status, created_by) VALUES
    (1, 1, 'Software Engineer', 'Design and ship scalable backend services in Python.', 'Full-time', 'Bengaluru', 24.00, 7.50, 0, 10, '2026-12-31', 'active', 1),
    (2, 2, 'Backend Developer', 'Java and Spring Boot microservices for enterprise clients.', 'Full-time', 'Hyderabad', 14.50, 7.00, 0, 8, '2026-12-15', 'active', 2),
    (3, 3, 'Data Analyst', 'SQL heavy analytics role building dashboards for retail clients.', 'Full-time', 'Pune', 12.00, 6.50, 1, 6, '2026-12-20', 'active', 3),
    (4, 4, 'Full Stack Developer', 'React and Node.js product engineering for SaaS platform.', 'Full-time', 'Gurugram', 18.50, 7.20, 1, 6, '2027-01-15', 'active', 4),
    (5, 5, 'DevOps Engineer', 'Docker and cloud operations for managed services.', 'Full-time', 'Noida', 16.00, 7.00, 0, 4, '2026-12-10', 'active', 5),
    (6, 1, 'ML Intern', 'Six month applied machine learning internship with PPO potential.', 'Internship', 'Remote', 8.00, 6.50, 2, 5, '2026-12-05', 'active', 1);

INSERT INTO job_skill (job_id, skill_id, is_mandatory) VALUES
    (1, 1, 1), (1, 4, 1), (1, 9, 0), (1, 17, 0),
    (2, 2, 1), (2, 4, 0), (2, 13, 0),
    (3, 4, 1), (3, 1, 0), (3, 8, 0),
    (4, 5, 1), (4, 6, 0), (4, 7, 0), (4, 4, 0),
    (5, 12, 1), (5, 11, 0), (5, 15, 0),
    (6, 1, 1), (6, 8, 0);

-- ------------------------------------------------------------
-- Applications (eligibility trigger validates every row)
-- ------------------------------------------------------------
INSERT INTO application (application_id, job_id, student_id, status, applied_at) VALUES
    (1, 1, 1, 'shortlisted', '2026-10-20 10:00:00'),
    (2, 1, 2, 'interview', '2026-10-20 11:00:00'),
    (3, 1, 6, 'interview', '2026-10-21 09:30:00'),
    (4, 1, 12, 'interview', '2026-10-21 10:15:00'),
    (5, 1, 15, 'rejected', '2026-10-22 12:00:00'),
    (6, 1, 20, 'applied', '2026-10-23 14:00:00'),
    (7, 2, 3, 'interview', '2026-10-24 09:00:00'),
    (8, 2, 5, 'shortlisted', '2026-10-24 10:00:00'),
    (9, 2, 11, 'applied', '2026-10-25 11:00:00'),
    (10, 2, 16, 'rejected', '2026-10-25 12:00:00'),
    (11, 3, 9, 'applied', '2026-10-26 09:00:00'),
    (12, 3, 10, 'interview', '2026-10-26 10:00:00'),
    (13, 3, 20, 'rejected', '2026-10-27 11:00:00'),
    (14, 4, 4, 'interview', '2026-10-28 09:00:00'),
    (15, 4, 13, 'shortlisted', '2026-10-28 10:00:00'),
    (16, 4, 14, 'applied', '2026-10-29 11:00:00'),
    (17, 4, 18, 'interview', '2026-10-29 12:00:00'),
    (18, 5, 8, 'interview', '2026-10-30 09:00:00'),
    (19, 5, 19, 'shortlisted', '2026-10-30 10:00:00'),
    (20, 6, 6, 'applied', '2026-11-01 09:00:00'),
    (21, 6, 12, 'applied', '2026-11-01 10:00:00'),
    (22, 6, 20, 'withdrawn', '2026-11-02 11:00:00');

-- ------------------------------------------------------------
-- Interviews (trigger requires shortlisted/interview stage)
-- ------------------------------------------------------------
INSERT INTO interview (interview_id, application_id, round_no, interview_type, scheduled_at, mode, meeting_link, result, feedback) VALUES
    (1, 2, 1, 'Technical', '2026-11-05 10:00:00', 'Online', 'https://meet.example.com/apex-r1-priya', 'selected', 'Strong Python and SQL fundamentals'),
    (2, 2, 2, 'HR', '2026-11-06 11:00:00', 'Online', 'https://meet.example.com/apex-hr-priya', 'selected', 'Excellent communication'),
    (3, 3, 1, 'Technical', '2026-11-05 14:00:00', 'Online', 'https://meet.example.com/apex-r1-ananya', 'selected', 'Great problem solving'),
    (4, 4, 1, 'Technical', '2026-11-06 09:00:00', 'Offline', NULL, 'selected', 'Cleared coding round comfortably'),
    (5, 7, 1, 'Aptitude', '2026-11-07 10:00:00', 'Online', 'https://meet.example.com/van-apt-karan', 'selected', 'Top score in aptitude'),
    (6, 7, 2, 'Technical', '2026-11-08 10:00:00', 'Online', 'https://meet.example.com/van-tech-karan', 'selected', 'Good Spring Boot knowledge'),
    (7, 12, 1, 'Technical', '2026-11-09 10:30:00', 'Online', 'https://meet.example.com/zen-tech-divya', 'selected', 'Solid SQL joins and aggregation'),
    (8, 14, 1, 'Technical', '2026-11-09 14:00:00', 'Offline', NULL, 'selected', 'Strong React portfolio'),
    (9, 17, 1, 'Technical', '2026-11-10 11:00:00', 'Online', 'https://meet.example.com/nex-tech-kavya', 'pending', NULL),
    (10, 18, 1, 'Technical', '2026-11-10 15:00:00', 'Online', 'https://meet.example.com/opt-tech-nisha', 'selected', 'Hands on Docker experience');

-- ------------------------------------------------------------
-- Offers released (pending) then responded to (triggers create placements)
-- ------------------------------------------------------------
INSERT INTO offer (offer_id, application_id, ctc, joining_date, offer_date, status) VALUES
    (1, 2, 24.00, '2027-07-01', '2026-11-10', 'pending'),
    (2, 3, 22.00, '2027-07-01', '2026-11-10', 'pending'),
    (3, 4, 23.00, '2027-07-01', '2026-11-10', 'pending'),
    (4, 7, 14.50, '2027-06-15', '2026-11-10', 'pending'),
    (5, 12, 12.00, '2027-07-01', '2026-11-11', 'pending'),
    (6, 14, 18.50, '2027-06-01', '2026-11-11', 'pending'),
    (7, 18, 16.00, '2027-07-15', '2026-11-11', 'pending');

UPDATE application
   SET status = 'offered'
 WHERE application_id IN (2, 3, 4, 7, 12, 14, 18);

-- Accepting an offer fires trg_offer_after_update -> placement -> application 'placed'
UPDATE offer
   SET status = 'accepted'
 WHERE offer_id IN (1, 3, 4, 5, 6, 7);
