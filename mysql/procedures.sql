-- ============================================================
-- CampusHire - stored procedures (all workflow logic lives here)
-- Every procedure returns a message starting with SUCCESS or ERROR.
-- ============================================================
USE campushire;
DELIMITER $$

-- ------------------------------------------------------------
-- Authentication
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_verify_login$$
CREATE PROCEDURE sp_verify_login(
    IN p_email VARCHAR(120),
    IN p_password VARCHAR(255),
    OUT p_user_id INT,
    OUT p_role VARCHAR(20),
    OUT p_full_name VARCHAR(100),
    OUT p_message VARCHAR(255)
)
BEGIN
    SET p_user_id = NULL;
    SET p_role = NULL;
    SET p_full_name = NULL;

    SELECT user_id, role, full_name
      INTO p_user_id, p_role, p_full_name
      FROM app_user
     WHERE email = LOWER(TRIM(p_email))
       AND password_hash = SHA2(p_password, 256)
       AND is_active = 1
     LIMIT 1;

    IF p_user_id IS NULL THEN
        SET p_message = 'ERROR: Invalid email or password';
    ELSE
        SET p_message = 'SUCCESS';
    END IF;
END$$

-- ------------------------------------------------------------
-- Student management
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_register_student$$
CREATE PROCEDURE sp_register_student(
    IN p_email VARCHAR(120),
    IN p_password VARCHAR(255),
    IN p_full_name VARCHAR(100),
    IN p_phone VARCHAR(15),
    IN p_roll_no VARCHAR(20),
    IN p_branch_id INT,
    IN p_batch_year SMALLINT,
    IN p_cgpa DECIMAL(4,2),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_user_id INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_message = CONCAT('ERROR: ', @err_msg);
    END;

    START TRANSACTION;

    INSERT INTO app_user (email, password_hash, full_name, role, phone)
    VALUES (LOWER(TRIM(p_email)), SHA2(p_password, 256), p_full_name, 'student', p_phone);

    SET v_user_id = LAST_INSERT_ID();

    INSERT INTO student (user_id, roll_no, branch_id, batch_year, cgpa, backlogs)
    VALUES (v_user_id, UPPER(TRIM(p_roll_no)), p_branch_id, p_batch_year, p_cgpa, 0);

    COMMIT;
    SET p_message = CONCAT('SUCCESS: Student registered with id ', LAST_INSERT_ID());
END$$

DROP PROCEDURE IF EXISTS sp_update_student_profile$$
CREATE PROCEDURE sp_update_student_profile(
    IN p_student_id INT,
    IN p_phone VARCHAR(15),
    IN p_cgpa DECIMAL(4,2),
    IN p_backlogs INT,
    IN p_resume_url VARCHAR(255),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_user_id INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_message = CONCAT('ERROR: ', @err_msg);
    END;

    START TRANSACTION;

    SELECT user_id INTO v_user_id FROM student WHERE student_id = p_student_id;
    IF v_user_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student not found';
    END IF;

    UPDATE app_user SET phone = p_phone WHERE user_id = v_user_id;
    UPDATE student
       SET cgpa = p_cgpa,
           backlogs = p_backlogs,
           resume_url = p_resume_url
     WHERE student_id = p_student_id;

    COMMIT;
    SET p_message = 'SUCCESS: Profile updated';
END$$

DROP PROCEDURE IF EXISTS sp_add_student_skill$$
CREATE PROCEDURE sp_add_student_skill(
    IN p_student_id INT,
    IN p_skill_name VARCHAR(60),
    IN p_proficiency VARCHAR(20),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_skill_id INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_message = CONCAT('ERROR: ', @err_msg);
    END;

    IF TRIM(p_skill_name) = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Skill name cannot be empty';
    END IF;

    START TRANSACTION;

    INSERT INTO skill (skill_name)
    VALUES (TRIM(p_skill_name))
    ON DUPLICATE KEY UPDATE skill_id = LAST_INSERT_ID(skill_id);

    SET v_skill_id = LAST_INSERT_ID();

    INSERT INTO student_skill (student_id, skill_id, proficiency)
    VALUES (p_student_id, v_skill_id, p_proficiency)
    ON DUPLICATE KEY UPDATE proficiency = p_proficiency;

    COMMIT;
    SET p_message = CONCAT('SUCCESS: Skill "', TRIM(p_skill_name), '" saved');
END$$

-- ------------------------------------------------------------
-- Job browsing and applications
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_apply_for_job$$
CREATE PROCEDURE sp_apply_for_job(
    IN p_student_id INT,
    IN p_job_id INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_message = CONCAT('ERROR: ', @err_msg);
    END;

    START TRANSACTION;

    IF fn_check_eligibility(p_job_id, p_student_id) = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'You are not eligible for this job (check CGPA, backlogs or mandatory skills)';
    END IF;

    IF EXISTS (
        SELECT 1 FROM application
         WHERE job_id = p_job_id AND student_id = p_student_id
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'You have already applied to this job';
    END IF;

    INSERT INTO application (job_id, student_id, status)
    VALUES (p_job_id, p_student_id, 'applied');

    COMMIT;
    SET p_message = CONCAT('SUCCESS: Application #', LAST_INSERT_ID(), ' submitted');
END$$

DROP PROCEDURE IF EXISTS sp_withdraw_application$$
CREATE PROCEDURE sp_withdraw_application(
    IN p_application_id INT,
    IN p_student_id INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    UPDATE application
       SET status = 'withdrawn'
     WHERE application_id = p_application_id
       AND student_id = p_student_id
       AND status IN ('applied', 'shortlisted', 'interview');

    IF ROW_COUNT() = 0 THEN
        SET p_message = 'ERROR: Application cannot be withdrawn at this stage';
    ELSE
        SET p_message = 'SUCCESS: Application withdrawn';
    END IF;
END$$

DROP PROCEDURE IF EXISTS sp_get_student_dashboard$$
CREATE PROCEDURE sp_get_student_dashboard(IN p_student_id INT)
BEGIN
    SELECT s.student_id,
           u.full_name,
           s.roll_no,
           b.branch_name,
           s.cgpa,
           s.backlogs,
           fn_student_status(s.student_id) AS placement_status,
           (SELECT COUNT(*) FROM application a WHERE a.student_id = s.student_id) AS applications,
           (SELECT COUNT(*) FROM application a
             WHERE a.student_id = s.student_id
               AND a.status IN ('shortlisted', 'interview')) AS in_progress,
           (SELECT COUNT(*) FROM interview i
              JOIN application a ON a.application_id = i.application_id
             WHERE a.student_id = s.student_id) AS interviews,
           (SELECT COUNT(*) FROM offer o
              JOIN application a ON a.application_id = o.application_id
             WHERE a.student_id = s.student_id
               AND o.status = 'pending') AS pending_offers,
           (SELECT COUNT(*) FROM job j
             JOIN student st ON st.student_id = s.student_id
             WHERE j.status = 'active'
               AND j.application_deadline >= CURDATE()
               AND j.min_cgpa <= st.cgpa
               AND j.max_backlogs >= st.backlogs
               AND fn_check_eligibility(j.job_id, st.student_id) = 1) AS eligible_jobs
      FROM student s
      JOIN app_user u ON u.user_id = s.user_id
      JOIN branch b ON b.branch_id = s.branch_id
     WHERE s.student_id = p_student_id;
END$$

-- ------------------------------------------------------------
-- Recruiter workflow
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_update_company$$
CREATE PROCEDURE sp_update_company(
    IN p_company_id INT,
    IN p_company_name VARCHAR(100),
    IN p_industry VARCHAR(80),
    IN p_website VARCHAR(150),
    IN p_hr_contact VARCHAR(100),
    IN p_location VARCHAR(100),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        SET p_message = CONCAT('ERROR: ', @err_msg);
    END;

    UPDATE company
       SET company_name = p_company_name,
           industry = p_industry,
           website = p_website,
           hr_contact = p_hr_contact,
           location = p_location
     WHERE company_id = p_company_id;

    SET p_message = 'SUCCESS: Company profile updated';
END$$

DROP PROCEDURE IF EXISTS sp_post_job$$
CREATE PROCEDURE sp_post_job(
    IN p_recruiter_id INT,
    IN p_title VARCHAR(100),
    IN p_description TEXT,
    IN p_job_type VARCHAR(30),
    IN p_location VARCHAR(100),
    IN p_ctc DECIMAL(12,2),
    IN p_min_cgpa DECIMAL(4,2),
    IN p_max_backlogs INT,
    IN p_openings INT,
    IN p_deadline DATE,
    IN p_skills TEXT,
    OUT p_job_id INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_company_id INT;
    DECLARE v_json JSON;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_job_id = NULL;
        SET p_message = CONCAT('ERROR: ', @err_msg);
    END;

    START TRANSACTION;

    SELECT company_id INTO v_company_id
      FROM recruiter
     WHERE recruiter_id = p_recruiter_id;

    IF v_company_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Recruiter profile not found';
    END IF;

    IF p_deadline < CURDATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Application deadline must be today or later';
    END IF;

    INSERT INTO job (company_id, job_title, job_description, job_type, location,
                     ctc, min_cgpa, max_backlogs, openings, application_deadline,
                     status, created_by)
    VALUES (v_company_id, p_title, p_description, p_job_type, p_location,
            p_ctc, p_min_cgpa, p_max_backlogs, p_openings, p_deadline,
            'active', p_recruiter_id);

    SET p_job_id = LAST_INSERT_ID();

    IF p_skills IS NOT NULL AND TRIM(p_skills) <> '' THEN
        SET v_json = CAST(
            CONCAT('["',
                   REPLACE(REPLACE(TRIM(p_skills), ', ', ','), ',', '","'),
                   '"]') AS JSON
        );

        INSERT IGNORE INTO skill (skill_name)
        SELECT DISTINCT TRIM(jt.skill_name)
          FROM JSON_TABLE(v_json, '$[*]' COLUMNS (skill_name VARCHAR(60) PATH '$')) jt
         WHERE TRIM(jt.skill_name) <> '';

        INSERT IGNORE INTO job_skill (job_id, skill_id, is_mandatory)
        SELECT p_job_id, s.skill_id, 1
          FROM JSON_TABLE(v_json, '$[*]' COLUMNS (skill_name VARCHAR(60) PATH '$')) jt
          JOIN skill s ON s.skill_name = TRIM(jt.skill_name)
         WHERE TRIM(jt.skill_name) <> '';
    END IF;

    COMMIT;
    SET p_message = CONCAT('SUCCESS: Job #', p_job_id, ' posted');
END$$

DROP PROCEDURE IF EXISTS sp_close_job$$
CREATE PROCEDURE sp_close_job(
    IN p_job_id INT,
    IN p_recruiter_id INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    UPDATE job j
      JOIN recruiter r ON r.company_id = j.company_id
       SET j.status = 'closed'
     WHERE j.job_id = p_job_id
       AND r.recruiter_id = p_recruiter_id;

    IF ROW_COUNT() = 0 THEN
        SET p_message = 'ERROR: Job not found or already closed';
    ELSE
        SET p_message = 'SUCCESS: Job closed';
    END IF;
END$$

DROP PROCEDURE IF EXISTS sp_shortlist_applicant$$
CREATE PROCEDURE sp_shortlist_applicant(
    IN p_application_id INT,
    IN p_recruiter_id INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    UPDATE application a
      JOIN job j ON j.job_id = a.job_id
      JOIN recruiter r ON r.company_id = j.company_id
       SET a.status = 'shortlisted'
     WHERE a.application_id = p_application_id
       AND r.recruiter_id = p_recruiter_id
       AND a.status = 'applied';

    IF ROW_COUNT() = 0 THEN
        SET p_message = 'ERROR: Only applications in "applied" state can be shortlisted';
    ELSE
        SET p_message = 'SUCCESS: Candidate shortlisted';
    END IF;
END$$

DROP PROCEDURE IF EXISTS sp_reject_applicant$$
CREATE PROCEDURE sp_reject_applicant(
    IN p_application_id INT,
    IN p_recruiter_id INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    UPDATE application a
      JOIN job j ON j.job_id = a.job_id
      JOIN recruiter r ON r.company_id = j.company_id
       SET a.status = 'rejected'
     WHERE a.application_id = p_application_id
       AND r.recruiter_id = p_recruiter_id
       AND a.status IN ('applied', 'shortlisted', 'interview');

    IF ROW_COUNT() = 0 THEN
        SET p_message = 'ERROR: Application cannot be rejected at this stage';
    ELSE
        SET p_message = 'SUCCESS: Application rejected';
    END IF;
END$$

DROP PROCEDURE IF EXISTS sp_schedule_interview$$
CREATE PROCEDURE sp_schedule_interview(
    IN p_application_id INT,
    IN p_recruiter_id INT,
    IN p_round_no INT,
    IN p_type VARCHAR(30),
    IN p_scheduled_at DATETIME,
    IN p_mode VARCHAR(10),
    IN p_link VARCHAR(255),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_message = CONCAT('ERROR: ', @err_msg);
    END;

    START TRANSACTION;

    SELECT a.status
      INTO v_status
      FROM application a
      JOIN job j ON j.job_id = a.job_id
      JOIN recruiter r ON r.company_id = j.company_id
     WHERE a.application_id = p_application_id
       AND r.recruiter_id = p_recruiter_id;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Application not found for your company';
    END IF;

    IF v_status NOT IN ('shortlisted', 'interview') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Shortlist the candidate before scheduling interviews';
    END IF;

    IF p_scheduled_at < NOW() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Interview must be scheduled in the future';
    END IF;

    INSERT INTO interview (application_id, round_no, interview_type, scheduled_at, mode, meeting_link)
    VALUES (p_application_id, p_round_no, p_type, p_scheduled_at, p_mode, p_link);

    UPDATE application
       SET status = 'interview'
     WHERE application_id = p_application_id;

    COMMIT;
    SET p_message = CONCAT('SUCCESS: Interview round ', p_round_no, ' scheduled');
END$$

DROP PROCEDURE IF EXISTS sp_update_interview_result$$
CREATE PROCEDURE sp_update_interview_result(
    IN p_interview_id INT,
    IN p_recruiter_id INT,
    IN p_result VARCHAR(20),
    IN p_feedback TEXT,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_application_id INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_message = CONCAT('ERROR: ', @err_msg);
    END;

    START TRANSACTION;

    SELECT i.application_id
      INTO v_application_id
      FROM interview i
      JOIN application a ON a.application_id = i.application_id
      JOIN job j ON j.job_id = a.job_id
      JOIN recruiter r ON r.company_id = j.company_id
     WHERE i.interview_id = p_interview_id
       AND r.recruiter_id = p_recruiter_id;

    IF v_application_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Interview not found for your company';
    END IF;

    UPDATE interview
       SET result = p_result,
           feedback = p_feedback
     WHERE interview_id = p_interview_id;

    IF p_result = 'rejected' THEN
        UPDATE application SET status = 'rejected' WHERE application_id = v_application_id;
    END IF;

    COMMIT;
    SET p_message = CONCAT('SUCCESS: Interview result saved as ', p_result);
END$$

DROP PROCEDURE IF EXISTS sp_make_offer$$
CREATE PROCEDURE sp_make_offer(
    IN p_application_id INT,
    IN p_recruiter_id INT,
    IN p_ctc DECIMAL(12,2),
    IN p_joining_date DATE,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_message = CONCAT('ERROR: ', @err_msg);
    END;

    START TRANSACTION;

    SELECT a.status
      INTO v_status
      FROM application a
      JOIN job j ON j.job_id = a.job_id
      JOIN recruiter r ON r.company_id = j.company_id
     WHERE a.application_id = p_application_id
       AND r.recruiter_id = p_recruiter_id;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Application not found for your company';
    END IF;

    IF v_status <> 'interview' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Offer can only be made during the interview stage';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM interview
         WHERE application_id = p_application_id
           AND result = 'selected'
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Candidate has no selected interview round yet';
    END IF;

    IF EXISTS (SELECT 1 FROM offer WHERE application_id = p_application_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'An offer already exists for this application';
    END IF;

    INSERT INTO offer (application_id, ctc, joining_date, offer_date, status)
    VALUES (p_application_id, p_ctc, p_joining_date, CURDATE(), 'pending');

    UPDATE application
       SET status = 'offered'
     WHERE application_id = p_application_id;

    COMMIT;
    SET p_message = CONCAT('SUCCESS: Offer #', LAST_INSERT_ID(), ' released');
END$$

-- Uses a CURSOR to release offers for every selected candidate of a job.
DROP PROCEDURE IF EXISTS sp_auto_offer_selected$$
CREATE PROCEDURE sp_auto_offer_selected(
    IN p_job_id INT,
    IN p_ctc DECIMAL(12,2),
    IN p_joining_date DATE,
    OUT p_offer_count INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE v_application_id INT;
    DECLARE v_student_id INT;

    DECLARE cur CURSOR FOR
        SELECT a.application_id, a.student_id
          FROM application a
         WHERE a.job_id = p_job_id
           AND a.status = 'interview'
           AND EXISTS (
                SELECT 1 FROM interview i
                 WHERE i.application_id = a.application_id
                   AND i.result = 'selected'
           )
           AND NOT EXISTS (
                SELECT 1 FROM offer o
                 WHERE o.application_id = a.application_id
           );

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_message = CONCAT('ERROR: ', @err_msg);
    END;

    SET p_offer_count = 0;
    START TRANSACTION;

    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO v_application_id, v_student_id;
        IF done = 1 THEN
            LEAVE read_loop;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM placement
             WHERE student_id = v_student_id AND is_active = 1
        ) THEN
            INSERT INTO offer (application_id, ctc, joining_date, offer_date, status)
            VALUES (v_application_id, p_ctc, p_joining_date, CURDATE(), 'pending');

            UPDATE application
               SET status = 'offered'
             WHERE application_id = v_application_id;

            SET p_offer_count = p_offer_count + 1;
        END IF;
    END LOOP;

    CLOSE cur;
    COMMIT;

    SET p_message = CONCAT('SUCCESS: ', p_offer_count, ' offer(s) generated');
END$$

-- ------------------------------------------------------------
-- Offer response (student side)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_respond_to_offer$$
CREATE PROCEDURE sp_respond_to_offer(
    IN p_offer_id INT,
    IN p_student_id INT,
    IN p_accept TINYINT,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_student_id INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_message = CONCAT('ERROR: ', @err_msg);
    END;

    START TRANSACTION;

    SELECT o.status, a.student_id
      INTO v_status, v_student_id
      FROM offer o
      JOIN application a ON a.application_id = o.application_id
     WHERE o.offer_id = p_offer_id;

    IF v_student_id IS NULL OR v_student_id <> p_student_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Offer not found for this student';
    END IF;

    IF v_status <> 'pending' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This offer has already been responded to';
    END IF;

    UPDATE offer
       SET status = IF(p_accept = 1, 'accepted', 'declined')
     WHERE offer_id = p_offer_id;

    COMMIT;
    SET p_message = IF(p_accept = 1,
                       'SUCCESS: Offer accepted, placement recorded',
                       'SUCCESS: Offer declined');
END$$

-- ------------------------------------------------------------
-- Placement reporting
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_get_placement_stats$$
CREATE PROCEDURE sp_get_placement_stats()
BEGIN
    SELECT (SELECT COUNT(*) FROM student) AS total_students,
           (SELECT COUNT(*) FROM placement WHERE is_active = 1) AS total_placed,
           (SELECT ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM student), 0), 2)
              FROM placement WHERE is_active = 1) AS placement_rate,
           (SELECT ROUND(AVG(ctc), 2) FROM offer WHERE status = 'accepted') AS avg_ctc,
           (SELECT MAX(ctc) FROM offer WHERE status = 'accepted') AS max_ctc,
           (SELECT COUNT(*) FROM company) AS total_companies,
           (SELECT COUNT(*) FROM job WHERE status = 'active') AS active_jobs,
           (SELECT COUNT(*) FROM application) AS total_applications,
           (SELECT COUNT(*) FROM offer WHERE status = 'pending') AS pending_offers;
END$$

-- Uses a CURSOR to build a per-branch report for a batch year.
DROP PROCEDURE IF EXISTS sp_generate_branch_report$$
CREATE PROCEDURE sp_generate_branch_report(IN p_batch_year SMALLINT)
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE v_branch_id INT;
    DECLARE v_total INT DEFAULT 0;
    DECLARE v_placed INT DEFAULT 0;
    DECLARE v_avg DECIMAL(12,2) DEFAULT 0;

    DECLARE cur CURSOR FOR
        SELECT branch_id FROM branch ORDER BY branch_id;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    DELETE FROM placement_report_cache WHERE batch_year = p_batch_year;

    OPEN cur;

    report_loop: LOOP
        FETCH cur INTO v_branch_id;
        IF done = 1 THEN
            LEAVE report_loop;
        END IF;

        SELECT COUNT(*)
          INTO v_total
          FROM student
         WHERE branch_id = v_branch_id
           AND batch_year = p_batch_year;

        SELECT COUNT(DISTINCT p.student_id)
          INTO v_placed
          FROM placement p
          JOIN student s ON s.student_id = p.student_id
         WHERE s.branch_id = v_branch_id
           AND s.batch_year = p_batch_year
           AND p.is_active = 1;

        SELECT COALESCE(ROUND(AVG(o.ctc), 2), 0)
          INTO v_avg
          FROM placement p
          JOIN offer o ON o.offer_id = p.offer_id
          JOIN student s ON s.student_id = p.student_id
         WHERE s.branch_id = v_branch_id
           AND s.batch_year = p_batch_year
           AND p.is_active = 1;

        INSERT INTO placement_report_cache
            (batch_year, branch_id, total_students, placed_students, placement_rate, avg_ctc)
        VALUES
            (p_batch_year, v_branch_id, v_total, v_placed,
             IF(v_total = 0, 0, ROUND(v_placed * 100.0 / v_total, 2)),
             v_avg);
    END LOOP;

    CLOSE cur;

    SELECT c.batch_year,
           b.branch_name,
           c.total_students,
           c.placed_students,
           c.placement_rate,
           c.avg_ctc
      FROM placement_report_cache c
      JOIN branch b ON b.branch_id = c.branch_id
     WHERE c.batch_year = p_batch_year
     ORDER BY c.placement_rate DESC;
END$$

-- ------------------------------------------------------------
-- Read models for the Streamlit layer.
-- This project does not use views: every multi-table read below is a
-- stored procedure built from JOINs, subqueries, GROUP BY and the
-- aggregate / scalar functions allowed by the course syllabus.
-- ------------------------------------------------------------

-- Student profile (single student, or a filtered list for the officer).
DROP PROCEDURE IF EXISTS sp_list_student_profiles$$
CREATE PROCEDURE sp_list_student_profiles(
    IN p_branch_name VARCHAR(60),
    IN p_batch_year SMALLINT,
    IN p_student_id INT
)
BEGIN
    SELECT s.student_id,
           s.user_id,
           u.full_name,
           u.email,
           u.phone,
           s.roll_no,
           b.branch_id,
           b.branch_name,
           s.batch_year,
           s.cgpa,
           s.backlogs,
           s.resume_url,
           (SELECT COUNT(*) FROM student_skill ss
             WHERE ss.student_id = s.student_id) AS skill_count,
           fn_student_status(s.student_id) AS placement_status
      FROM student s
      JOIN app_user u ON u.user_id = s.user_id
      JOIN branch b ON b.branch_id = s.branch_id
     WHERE (p_branch_name IS NULL OR b.branch_name = p_branch_name)
       AND (p_batch_year IS NULL OR s.batch_year = p_batch_year)
       AND (p_student_id IS NULL OR s.student_id = p_student_id)
     ORDER BY s.cgpa DESC;
END$$

-- Job details with per-job application counters (recruiter and officer).
DROP PROCEDURE IF EXISTS sp_list_job_details$$
CREATE PROCEDURE sp_list_job_details(
    IN p_company_id INT,
    IN p_job_id INT
)
BEGIN
    SELECT j.job_id,
           j.company_id,
           c.company_name,
           j.job_title,
           j.job_type,
           j.location,
           j.ctc,
           j.min_cgpa,
           j.max_backlogs,
           j.openings,
           j.application_deadline,
           j.status,
           c.industry,
           (SELECT COUNT(*) FROM application a
             WHERE a.job_id = j.job_id) AS application_count,
           (SELECT COUNT(*) FROM application a
             WHERE a.job_id = j.job_id
               AND a.status IN ('shortlisted', 'interview', 'offered', 'placed')) AS shortlisted_count,
           (SELECT COUNT(*) FROM job_skill js
             WHERE js.job_id = j.job_id) AS required_skill_count
      FROM job j
      JOIN company c ON c.company_id = j.company_id
     WHERE (p_company_id IS NULL OR j.company_id = p_company_id)
       AND (p_job_id IS NULL OR j.job_id = p_job_id)
     ORDER BY j.job_id DESC;
END$$

-- Open jobs for one student, with eligibility and skill match from SQL functions.
DROP PROCEDURE IF EXISTS sp_list_open_jobs$$
CREATE PROCEDURE sp_list_open_jobs(IN p_student_id INT)
BEGIN
    SELECT j.job_id,
           j.company_id,
           c.company_name,
           j.job_title,
           j.job_type,
           j.location,
           j.ctc,
           j.min_cgpa,
           j.max_backlogs,
           j.openings,
           j.application_deadline,
           j.status,
           (SELECT COUNT(*) FROM application a
             WHERE a.job_id = j.job_id) AS application_count,
           fn_check_eligibility(j.job_id, p_student_id) AS is_eligible,
           fn_student_skill_match(j.job_id, p_student_id) AS skill_match
      FROM job j
      JOIN company c ON c.company_id = j.company_id
     WHERE j.status = 'active'
       AND j.application_deadline >= CURDATE()
     ORDER BY j.ctc DESC;
END$$

-- Application details with student, company, interview count and skill match.
DROP PROCEDURE IF EXISTS sp_list_applications$$
CREATE PROCEDURE sp_list_applications(
    IN p_application_id INT,
    IN p_student_id INT,
    IN p_status VARCHAR(20),
    IN p_branch_name VARCHAR(60),
    IN p_batch_year SMALLINT
)
BEGIN
    SELECT a.application_id,
           a.job_id,
           a.student_id,
           a.status,
           a.applied_at,
           a.updated_at,
           j.job_title,
           j.ctc AS job_ctc,
           j.company_id,
           c.company_name,
           u.full_name AS student_name,
           s.roll_no,
           b.branch_name,
           s.cgpa,
           s.batch_year,
           (SELECT COUNT(*) FROM interview i
             WHERE i.application_id = a.application_id) AS interview_count,
           fn_student_skill_match(a.job_id, a.student_id) AS skill_match
      FROM application a
      JOIN job j ON j.job_id = a.job_id
      JOIN company c ON c.company_id = j.company_id
      JOIN student s ON s.student_id = a.student_id
      JOIN app_user u ON u.user_id = s.user_id
      JOIN branch b ON b.branch_id = s.branch_id
     WHERE (p_application_id IS NULL OR a.application_id = p_application_id)
       AND (p_student_id IS NULL OR a.student_id = p_student_id)
       AND (p_status IS NULL OR a.status = p_status)
       AND (p_branch_name IS NULL OR b.branch_name = p_branch_name)
       AND (p_batch_year IS NULL OR s.batch_year = p_batch_year)
     ORDER BY a.applied_at DESC;
END$$

-- Branch wise placement analytics: joins + conditional aggregation + GROUP BY.
DROP PROCEDURE IF EXISTS sp_branch_placement_analytics$$
CREATE PROCEDURE sp_branch_placement_analytics(IN p_batch_year SMALLINT)
BEGIN
    SELECT s.batch_year,
           b.branch_id,
           b.branch_name,
           COUNT(*) AS total_students,
           SUM(CASE WHEN p.placement_id IS NULL THEN 0 ELSE 1 END) AS placed_students,
           ROUND(SUM(CASE WHEN p.placement_id IS NULL THEN 0 ELSE 1 END)
                 * 100.0 / COUNT(*), 2) AS placement_rate,
           COALESCE(ROUND(AVG(CASE WHEN p.placement_id IS NULL THEN NULL ELSE o.ctc END), 2), 0) AS avg_ctc
      FROM student s
      JOIN branch b ON b.branch_id = s.branch_id
      LEFT JOIN placement p
        ON p.student_id = s.student_id
       AND p.is_active = 1
      LEFT JOIN offer o ON o.offer_id = p.offer_id
     WHERE (p_batch_year IS NULL OR s.batch_year = p_batch_year)
     GROUP BY s.batch_year, b.branch_id, b.branch_name
     ORDER BY placement_rate DESC;
END$$

-- Company hiring summary: multi-table LEFT JOINs + GROUP BY.
DROP PROCEDURE IF EXISTS sp_company_hiring_stats$$
CREATE PROCEDURE sp_company_hiring_stats()
BEGIN
    SELECT c.company_id,
           c.company_name,
           c.industry,
           c.location,
           COUNT(DISTINCT j.job_id) AS total_jobs,
           COUNT(DISTINCT a.application_id) AS total_applications,
           COUNT(DISTINCT CASE WHEN a.status = 'placed' THEN a.application_id END) AS placed_count,
           COALESCE(ROUND(AVG(CASE WHEN o.status = 'accepted' THEN o.ctc END), 2), 0) AS avg_ctc
      FROM company c
      LEFT JOIN job j ON j.company_id = c.company_id
      LEFT JOIN application a ON a.job_id = j.job_id
      LEFT JOIN offer o ON o.application_id = a.application_id
     GROUP BY c.company_id, c.company_name, c.industry, c.location
     ORDER BY placed_count DESC, avg_ctc DESC;
END$$

DELIMITER ;
