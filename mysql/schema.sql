-- ============================================================
-- CampusHire - relational schema (DDL)
-- Run order: schema -> functions -> procedures -> triggers -> sample_data
-- Requires MySQL 8.0.16+ (CHECK constraints) and 8.0.19+ (JSON_TABLE)
-- ============================================================

DROP DATABASE IF EXISTS campushire;
CREATE DATABASE campushire CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE campushire;

-- ------------------------------------------------------------
-- Lookup / master tables
-- ------------------------------------------------------------
CREATE TABLE branch (
    branch_id INT AUTO_INCREMENT,
    branch_name VARCHAR(60) NOT NULL,
    CONSTRAINT pk_branch PRIMARY KEY (branch_id),
    CONSTRAINT uq_branch_name UNIQUE (branch_name)
) ENGINE = InnoDB;

CREATE TABLE company (
    company_id INT AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry VARCHAR(80) NULL,
    website VARCHAR(150) NULL,
    hr_contact VARCHAR(100) NULL,
    location VARCHAR(100) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_company PRIMARY KEY (company_id),
    CONSTRAINT uq_company_name UNIQUE (company_name)
) ENGINE = InnoDB;

CREATE TABLE skill (
    skill_id INT AUTO_INCREMENT,
    skill_name VARCHAR(60) NOT NULL,
    CONSTRAINT pk_skill PRIMARY KEY (skill_id),
    CONSTRAINT uq_skill_name UNIQUE (skill_name)
) ENGINE = InnoDB;

-- ------------------------------------------------------------
-- Users and role profiles
-- ------------------------------------------------------------
CREATE TABLE app_user (
    user_id INT AUTO_INCREMENT,
    email VARCHAR(120) NOT NULL,
    password_hash CHAR(64) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('student', 'recruiter', 'officer', 'admin') NOT NULL,
    phone VARCHAR(15) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_app_user PRIMARY KEY (user_id),
    CONSTRAINT uq_app_user_email UNIQUE (email),
    CONSTRAINT chk_app_user_email CHECK (email LIKE '%@%')
) ENGINE = InnoDB;

CREATE TABLE student (
    student_id INT AUTO_INCREMENT,
    user_id INT NOT NULL,
    roll_no VARCHAR(20) NOT NULL,
    branch_id INT NOT NULL,
    batch_year SMALLINT NOT NULL,
    cgpa DECIMAL(4,2) NOT NULL,
    backlogs INT NOT NULL DEFAULT 0,
    resume_url VARCHAR(255) NULL,
    CONSTRAINT pk_student PRIMARY KEY (student_id),
    CONSTRAINT uq_student_user UNIQUE (user_id),
    CONSTRAINT uq_student_roll UNIQUE (roll_no),
    CONSTRAINT chk_student_cgpa CHECK (cgpa BETWEEN 0 AND 10),
    CONSTRAINT chk_student_backlogs CHECK (backlogs >= 0),
    CONSTRAINT chk_student_batch CHECK (batch_year BETWEEN 2000 AND 2100),
    CONSTRAINT fk_student_user FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_student_branch FOREIGN KEY (branch_id)
        REFERENCES branch (branch_id)
) ENGINE = InnoDB;

CREATE TABLE recruiter (
    recruiter_id INT AUTO_INCREMENT,
    user_id INT NOT NULL,
    company_id INT NOT NULL,
    designation VARCHAR(80) NULL,
    CONSTRAINT pk_recruiter PRIMARY KEY (recruiter_id),
    CONSTRAINT uq_recruiter_user UNIQUE (user_id),
    CONSTRAINT fk_recruiter_user FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_recruiter_company FOREIGN KEY (company_id)
        REFERENCES company (company_id) ON DELETE CASCADE
) ENGINE = InnoDB;

CREATE TABLE placement_officer (
    officer_id INT AUTO_INCREMENT,
    user_id INT NOT NULL,
    department VARCHAR(80) NULL,
    CONSTRAINT pk_officer PRIMARY KEY (officer_id),
    CONSTRAINT uq_officer_user UNIQUE (user_id),
    CONSTRAINT fk_officer_user FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE CASCADE
) ENGINE = InnoDB;

CREATE TABLE student_skill (
    student_id INT NOT NULL,
    skill_id INT NOT NULL,
    proficiency ENUM('Beginner', 'Intermediate', 'Advanced') NOT NULL DEFAULT 'Intermediate',
    CONSTRAINT pk_student_skill PRIMARY KEY (student_id, skill_id),
    CONSTRAINT fk_student_skill_student FOREIGN KEY (student_id)
        REFERENCES student (student_id) ON DELETE CASCADE,
    CONSTRAINT fk_student_skill_skill FOREIGN KEY (skill_id)
        REFERENCES skill (skill_id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- ------------------------------------------------------------
-- Jobs and requirements
-- ------------------------------------------------------------
CREATE TABLE job (
    job_id INT AUTO_INCREMENT,
    company_id INT NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    job_description TEXT NULL,
    job_type ENUM('Full-time', 'Internship', 'Internship + PPO') NOT NULL DEFAULT 'Full-time',
    location VARCHAR(100) NULL,
    ctc DECIMAL(12,2) NOT NULL,
    min_cgpa DECIMAL(4,2) NOT NULL DEFAULT 0,
    max_backlogs INT NOT NULL DEFAULT 0,
    openings INT NOT NULL DEFAULT 1,
    application_deadline DATE NOT NULL,
    status ENUM('draft', 'active', 'closed') NOT NULL DEFAULT 'draft',
    created_by INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_job PRIMARY KEY (job_id),
    CONSTRAINT chk_job_ctc CHECK (ctc > 0),
    CONSTRAINT chk_job_cgpa CHECK (min_cgpa BETWEEN 0 AND 10),
    CONSTRAINT chk_job_backlogs CHECK (max_backlogs >= 0),
    CONSTRAINT chk_job_openings CHECK (openings >= 1),
    CONSTRAINT fk_job_company FOREIGN KEY (company_id)
        REFERENCES company (company_id) ON DELETE CASCADE,
    CONSTRAINT fk_job_creator FOREIGN KEY (created_by)
        REFERENCES recruiter (recruiter_id) ON DELETE SET NULL
) ENGINE = InnoDB;

CREATE TABLE job_skill (
    job_id INT NOT NULL,
    skill_id INT NOT NULL,
    is_mandatory TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT pk_job_skill PRIMARY KEY (job_id, skill_id),
    CONSTRAINT fk_job_skill_job FOREIGN KEY (job_id)
        REFERENCES job (job_id) ON DELETE CASCADE,
    CONSTRAINT fk_job_skill_skill FOREIGN KEY (skill_id)
        REFERENCES skill (skill_id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- ------------------------------------------------------------
-- Recruitment workflow
-- ------------------------------------------------------------
CREATE TABLE application (
    application_id INT AUTO_INCREMENT,
    job_id INT NOT NULL,
    student_id INT NOT NULL,
    status ENUM('applied', 'shortlisted', 'interview', 'offered',
                'placed', 'rejected', 'withdrawn') NOT NULL DEFAULT 'applied',
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_application PRIMARY KEY (application_id),
    CONSTRAINT uq_application_job_student UNIQUE (job_id, student_id),
    CONSTRAINT fk_application_job FOREIGN KEY (job_id)
        REFERENCES job (job_id) ON DELETE CASCADE,
    CONSTRAINT fk_application_student FOREIGN KEY (student_id)
        REFERENCES student (student_id) ON DELETE CASCADE
) ENGINE = InnoDB;

CREATE TABLE interview (
    interview_id INT AUTO_INCREMENT,
    application_id INT NOT NULL,
    round_no INT NOT NULL DEFAULT 1,
    interview_type ENUM('Aptitude', 'Technical', 'HR', 'Group Discussion') NOT NULL,
    scheduled_at DATETIME NOT NULL,
    mode ENUM('Online', 'Offline') NOT NULL DEFAULT 'Online',
    meeting_link VARCHAR(255) NULL,
    result ENUM('pending', 'selected', 'rejected', 'on_hold') NOT NULL DEFAULT 'pending',
    feedback TEXT NULL,
    CONSTRAINT pk_interview PRIMARY KEY (interview_id),
    CONSTRAINT uq_interview_round UNIQUE (application_id, round_no),
    CONSTRAINT chk_interview_round CHECK (round_no >= 1),
    CONSTRAINT fk_interview_application FOREIGN KEY (application_id)
        REFERENCES application (application_id) ON DELETE CASCADE
) ENGINE = InnoDB;

CREATE TABLE offer (
    offer_id INT AUTO_INCREMENT,
    application_id INT NOT NULL,
    ctc DECIMAL(12,2) NOT NULL,
    joining_date DATE NULL,
    offer_date DATE NOT NULL,
    status ENUM('pending', 'accepted', 'declined', 'revoked') NOT NULL DEFAULT 'pending',
    CONSTRAINT pk_offer PRIMARY KEY (offer_id),
    CONSTRAINT uq_offer_application UNIQUE (application_id),
    CONSTRAINT chk_offer_ctc CHECK (ctc > 0),
    CONSTRAINT fk_offer_application FOREIGN KEY (application_id)
        REFERENCES application (application_id) ON DELETE CASCADE
) ENGINE = InnoDB;

CREATE TABLE placement (
    placement_id INT AUTO_INCREMENT,
    student_id INT NOT NULL,
    offer_id INT NOT NULL,
    placed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT pk_placement PRIMARY KEY (placement_id),
    CONSTRAINT uq_placement_student UNIQUE (student_id),
    CONSTRAINT uq_placement_offer UNIQUE (offer_id),
    CONSTRAINT fk_placement_student FOREIGN KEY (student_id)
        REFERENCES student (student_id) ON DELETE CASCADE,
    CONSTRAINT fk_placement_offer FOREIGN KEY (offer_id)
        REFERENCES offer (offer_id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- ------------------------------------------------------------
-- Support tables used by triggers and reporting procedures
-- ------------------------------------------------------------
CREATE TABLE audit_log (
    audit_id BIGINT AUTO_INCREMENT,
    table_name VARCHAR(50) NOT NULL,
    action_type VARCHAR(20) NOT NULL,
    record_id INT NULL,
    changed_by VARCHAR(100) NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details VARCHAR(255) NULL,
    CONSTRAINT pk_audit_log PRIMARY KEY (audit_id)
) ENGINE = InnoDB;

CREATE TABLE placement_report_cache (
    cache_id INT AUTO_INCREMENT,
    batch_year SMALLINT NOT NULL,
    branch_id INT NOT NULL,
    total_students INT NOT NULL DEFAULT 0,
    placed_students INT NOT NULL DEFAULT 0,
    placement_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    avg_ctc DECIMAL(12,2) NOT NULL DEFAULT 0,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_report_cache PRIMARY KEY (cache_id),
    CONSTRAINT uq_report_cache UNIQUE (batch_year, branch_id),
    CONSTRAINT fk_report_cache_branch FOREIGN KEY (branch_id)
        REFERENCES branch (branch_id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- ------------------------------------------------------------
-- Indexes for common lookups
-- ------------------------------------------------------------
CREATE INDEX idx_job_company ON job (company_id);
CREATE INDEX idx_job_status ON job (status);
CREATE INDEX idx_application_student ON application (student_id);
CREATE INDEX idx_application_status ON application (status);
CREATE INDEX idx_interview_scheduled ON interview (scheduled_at);
CREATE INDEX idx_offer_status ON offer (status);
CREATE INDEX idx_offer_date ON offer (offer_date);
CREATE INDEX idx_placement_active ON placement (is_active);
CREATE INDEX idx_audit_record ON audit_log (table_name, record_id);
