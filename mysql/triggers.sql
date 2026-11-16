-- ============================================================
-- CampusHire - triggers (integrity + workflow automation)
-- ============================================================
USE campushire;
DELIMITER $$

-- ------------------------------------------------------------
-- Job validation
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_job_before_insert$$
CREATE TRIGGER trg_job_before_insert
BEFORE INSERT ON job
FOR EACH ROW
BEGIN
    IF NEW.application_deadline < CURDATE() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Application deadline must be today or later';
    END IF;
END$$

-- ------------------------------------------------------------
-- Eligibility enforced at database level for every INSERT path
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_application_before_insert$$
CREATE TRIGGER trg_application_before_insert
BEFORE INSERT ON application
FOR EACH ROW
BEGIN
    IF fn_check_eligibility(NEW.job_id, NEW.student_id) = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Student is not eligible for this job';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_application_after_update$$
CREATE TRIGGER trg_application_after_update
AFTER UPDATE ON application
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO audit_log (table_name, action_type, record_id, changed_by, details)
        VALUES ('application', 'UPDATE', NEW.application_id, CURRENT_USER(),
                CONCAT('Status ', OLD.status, ' -> ', NEW.status));
    END IF;
END$$

-- ------------------------------------------------------------
-- Interview integrity
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_interview_before_insert$$
CREATE TRIGGER trg_interview_before_insert
BEFORE INSERT ON interview
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(20);

    SELECT status INTO v_status
      FROM application
     WHERE application_id = NEW.application_id;

    IF v_status IS NULL OR v_status NOT IN ('shortlisted', 'interview') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Interviews require a shortlisted application';
    END IF;
END$$

-- ------------------------------------------------------------
-- Offer integrity
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_offer_before_insert$$
CREATE TRIGGER trg_offer_before_insert
BEFORE INSERT ON offer
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_student_id INT;
    DECLARE v_selected INT DEFAULT 0;
    DECLARE v_placed INT DEFAULT 0;

    SELECT status, student_id
      INTO v_status, v_student_id
      FROM application
     WHERE application_id = NEW.application_id;

    IF v_status IS NULL OR v_status <> 'interview' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Offers require an application in the interview stage';
    END IF;

    SELECT COUNT(*) INTO v_selected
      FROM interview
     WHERE application_id = NEW.application_id
       AND result = 'selected';

    IF v_selected = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Candidate has no selected interview round';
    END IF;

    SELECT COUNT(*) INTO v_placed
      FROM placement
     WHERE student_id = v_student_id
       AND is_active = 1;

    IF v_placed > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Student is already placed';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_offer_before_update$$
CREATE TRIGGER trg_offer_before_update
BEFORE UPDATE ON offer
FOR EACH ROW
BEGIN
    IF OLD.status <> 'pending' AND NEW.status <> OLD.status THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only pending offers can be accepted or declined';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_offer_after_insert$$
CREATE TRIGGER trg_offer_after_insert
AFTER INSERT ON offer
FOR EACH ROW
BEGIN
    DECLARE v_student_id INT;

    IF NEW.status = 'accepted' THEN
        SELECT student_id INTO v_student_id
          FROM application
         WHERE application_id = NEW.application_id;

        IF NOT EXISTS (
            SELECT 1 FROM placement
             WHERE student_id = v_student_id AND is_active = 1
        ) THEN
            INSERT INTO placement (student_id, offer_id)
            VALUES (v_student_id, NEW.offer_id);
        END IF;
    END IF;

    INSERT INTO audit_log (table_name, action_type, record_id, changed_by, details)
    VALUES ('offer', 'INSERT', NEW.offer_id, CURRENT_USER(),
            CONCAT('Offer created with status ', NEW.status));
END$$

DROP TRIGGER IF EXISTS trg_offer_after_update$$
CREATE TRIGGER trg_offer_after_update
AFTER UPDATE ON offer
FOR EACH ROW
BEGIN
    DECLARE v_student_id INT;

    IF NEW.status = 'accepted' AND OLD.status <> 'accepted' THEN
        SELECT student_id INTO v_student_id
          FROM application
         WHERE application_id = NEW.application_id;

        IF NOT EXISTS (
            SELECT 1 FROM placement
             WHERE student_id = v_student_id AND is_active = 1
        ) THEN
            INSERT INTO placement (student_id, offer_id)
            VALUES (v_student_id, NEW.offer_id);
        END IF;

    ELSEIF NEW.status = 'declined' AND OLD.status <> 'declined' THEN
        UPDATE application
           SET status = 'rejected'
         WHERE application_id = NEW.application_id
           AND status = 'offered';
    END IF;

    INSERT INTO audit_log (table_name, action_type, record_id, changed_by, details)
    VALUES ('offer', 'UPDATE', NEW.offer_id, CURRENT_USER(),
            CONCAT('Offer status ', OLD.status, ' -> ', NEW.status));
END$$

-- ------------------------------------------------------------
-- Placement automation
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_placement_after_insert$$
CREATE TRIGGER trg_placement_after_insert
AFTER INSERT ON placement
FOR EACH ROW
BEGIN
    UPDATE application a
      JOIN offer o ON o.offer_id = NEW.offer_id
       SET a.status = 'placed'
     WHERE a.application_id = o.application_id;

    UPDATE job j
       SET j.status = 'closed'
     WHERE j.job_id = (SELECT a.job_id
                         FROM application a
                         JOIN offer o ON o.application_id = a.application_id
                        WHERE o.offer_id = NEW.offer_id)
       AND (SELECT COUNT(*)
              FROM placement p
              JOIN offer o2 ON o2.offer_id = p.offer_id
              JOIN application a2 ON a2.application_id = o2.application_id
             WHERE a2.job_id = j.job_id
               AND p.is_active = 1) >= j.openings;

    INSERT INTO audit_log (table_name, action_type, record_id, changed_by, details)
    VALUES ('placement', 'INSERT', NEW.placement_id, CURRENT_USER(),
            CONCAT('Student ', NEW.student_id, ' placed through offer ', NEW.offer_id));
END$$

DELIMITER ;
