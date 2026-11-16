-- ============================================================
-- CampusHire - stored functions (business rules in SQL)
-- ============================================================
USE campushire;
DELIMITER $$

DROP FUNCTION IF EXISTS fn_check_eligibility$$
CREATE FUNCTION fn_check_eligibility(p_job_id INT, p_student_id INT)
RETURNS TINYINT
READS SQL DATA
BEGIN
    DECLARE v_min_cgpa DECIMAL(4,2);
    DECLARE v_max_backlogs INT;
    DECLARE v_deadline DATE;
    DECLARE v_job_status VARCHAR(10);
    DECLARE v_cgpa DECIMAL(4,2);
    DECLARE v_backlogs INT;
    DECLARE v_missing_skills INT DEFAULT 0;
    DECLARE v_already_placed INT DEFAULT 0;

    SELECT min_cgpa, max_backlogs, application_deadline, status
      INTO v_min_cgpa, v_max_backlogs, v_deadline, v_job_status
      FROM job
     WHERE job_id = p_job_id;

    IF v_job_status IS NULL THEN
        RETURN 0;
    END IF;

    SELECT cgpa, backlogs INTO v_cgpa, v_backlogs
      FROM student
     WHERE student_id = p_student_id;

    IF v_cgpa IS NULL THEN
        RETURN 0;
    END IF;

    IF v_job_status <> 'active' OR v_deadline < CURDATE() THEN
        RETURN 0;
    END IF;

    IF v_cgpa < v_min_cgpa OR v_backlogs > v_max_backlogs THEN
        RETURN 0;
    END IF;

    SELECT COUNT(*)
      INTO v_missing_skills
      FROM job_skill js
     WHERE js.job_id = p_job_id
       AND js.is_mandatory = 1
       AND NOT EXISTS (
            SELECT 1
              FROM student_skill ss
             WHERE ss.student_id = p_student_id
               AND ss.skill_id = js.skill_id
       );

    IF v_missing_skills > 0 THEN
        RETURN 0;
    END IF;

    SELECT COUNT(*)
      INTO v_already_placed
      FROM placement
     WHERE student_id = p_student_id
       AND is_active = 1;

    IF v_already_placed > 0 THEN
        RETURN 0;
    END IF;

    RETURN 1;
END$$

DROP FUNCTION IF EXISTS fn_student_skill_match$$
CREATE FUNCTION fn_student_skill_match(p_job_id INT, p_student_id INT)
RETURNS DECIMAL(5,2)
READS SQL DATA
BEGIN
    DECLARE v_total INT DEFAULT 0;
    DECLARE v_matched INT DEFAULT 0;

    SELECT COUNT(*) INTO v_total FROM job_skill WHERE job_id = p_job_id;

    IF v_total = 0 THEN
        RETURN 100.00;
    END IF;

    SELECT COUNT(*)
      INTO v_matched
      FROM job_skill js
      JOIN student_skill ss
        ON ss.skill_id = js.skill_id
       AND ss.student_id = p_student_id
     WHERE js.job_id = p_job_id;

    RETURN ROUND(v_matched * 100.0 / v_total, 2);
END$$

DROP FUNCTION IF EXISTS fn_company_avg_ctc$$
CREATE FUNCTION fn_company_avg_ctc(p_company_id INT)
RETURNS DECIMAL(12,2)
READS SQL DATA
BEGIN
    DECLARE v_avg DECIMAL(12,2);

    SELECT ROUND(AVG(o.ctc), 2)
      INTO v_avg
      FROM offer o
      JOIN application a ON a.application_id = o.application_id
      JOIN job j ON j.job_id = a.job_id
     WHERE j.company_id = p_company_id
       AND o.status = 'accepted';

    RETURN COALESCE(v_avg, 0);
END$$

DROP FUNCTION IF EXISTS fn_branch_placement_rate$$
CREATE FUNCTION fn_branch_placement_rate(p_branch_id INT, p_batch_year SMALLINT)
RETURNS DECIMAL(5,2)
READS SQL DATA
BEGIN
    DECLARE v_total INT DEFAULT 0;
    DECLARE v_placed INT DEFAULT 0;

    SELECT COUNT(*)
      INTO v_total
      FROM student
     WHERE branch_id = p_branch_id
       AND batch_year = p_batch_year;

    IF v_total = 0 THEN
        RETURN 0;
    END IF;

    SELECT COUNT(DISTINCT p.student_id)
      INTO v_placed
      FROM placement p
      JOIN student s ON s.student_id = p.student_id
     WHERE s.branch_id = p_branch_id
       AND s.batch_year = p_batch_year
       AND p.is_active = 1;

    RETURN ROUND(v_placed * 100.0 / v_total, 2);
END$$

DROP FUNCTION IF EXISTS fn_student_status$$
CREATE FUNCTION fn_student_status(p_student_id INT)
RETURNS VARCHAR(120)
READS SQL DATA
BEGIN
    DECLARE v_company VARCHAR(100);
    DECLARE v_ctc DECIMAL(12,2);

    SELECT c.company_name, o.ctc
      INTO v_company, v_ctc
      FROM placement p
      JOIN offer o ON o.offer_id = p.offer_id
      JOIN application a ON a.application_id = o.application_id
      JOIN job j ON j.job_id = a.job_id
      JOIN company c ON c.company_id = j.company_id
     WHERE p.student_id = p_student_id
       AND p.is_active = 1
     LIMIT 1;

    IF v_company IS NULL THEN
        RETURN 'Not Placed';
    END IF;

    RETURN CONCAT('Placed at ', v_company, ' (', v_ctc, ' LPA)');
END$$

DROP FUNCTION IF EXISTS fn_round_passed$$
CREATE FUNCTION fn_round_passed(p_application_id INT)
RETURNS TINYINT
READS SQL DATA
BEGIN
    DECLARE v_failed INT DEFAULT 0;
    DECLARE v_selected INT DEFAULT 0;

    SELECT COUNT(*) INTO v_failed
      FROM interview
     WHERE application_id = p_application_id
       AND result = 'rejected';

    IF v_failed > 0 THEN
        RETURN 0;
    END IF;

    SELECT COUNT(*) INTO v_selected
      FROM interview
     WHERE application_id = p_application_id
       AND result = 'selected';

    IF v_selected > 0 THEN
        RETURN 1;
    END IF;

    RETURN 0;
END$$

DELIMITER ;
