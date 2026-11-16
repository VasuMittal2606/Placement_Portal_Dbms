-- ============================================================
-- CampusHire - SQL concept reference (run manually, read only)
-- Demonstrates each topic from the DBMS lab syllabus.
-- Requires MySQL 8.0.31+ for INTERSECT / EXCEPT.
-- ============================================================
USE campushire;

-- ------------------------------------------------------------
-- 1. DQL: WHERE, ORDER BY, logical operators, scalar functions
-- ------------------------------------------------------------
SELECT s.roll_no,
       u.full_name,
       b.branch_name,
       s.cgpa,
       ROUND(s.cgpa * 10, 1) AS cgpa_percentage,
       UPPER(b.branch_name) AS branch_code,
       CONCAT(u.full_name, ' (', s.roll_no, ')') AS display_name
  FROM student s
  JOIN app_user u ON u.user_id = s.user_id
  JOIN branch b ON b.branch_id = s.branch_id
 WHERE s.cgpa >= 8.0
   AND s.backlogs = 0
   AND b.branch_name IN ('CSE', 'IT')
 ORDER BY s.cgpa DESC, u.full_name ASC;

-- ------------------------------------------------------------
-- 2. Aggregate functions + GROUP BY + HAVING
-- ------------------------------------------------------------
SELECT c.company_name,
       COUNT(DISTINCT j.job_id) AS jobs_posted,
       COUNT(DISTINCT a.application_id) AS applications,
       ROUND(AVG(j.ctc), 2) AS avg_ctc,
       MAX(j.ctc) AS highest_ctc
  FROM company c
  JOIN job j ON j.company_id = c.company_id
  LEFT JOIN application a ON a.job_id = j.job_id
 GROUP BY c.company_name
HAVING COUNT(DISTINCT a.application_id) > 0
 ORDER BY avg_ctc DESC;

-- ------------------------------------------------------------
-- 3. Multi-table join with conditional aggregation
-- ------------------------------------------------------------
SELECT b.branch_name,
       COUNT(DISTINCT s.student_id) AS students,
       COUNT(DISTINCT p.student_id) AS placed,
       ROUND(COUNT(DISTINCT p.student_id) * 100.0 / COUNT(DISTINCT s.student_id), 2) AS placement_rate,
       COALESCE(ROUND(AVG(o.ctc), 2), 0) AS avg_package
  FROM branch b
  JOIN student s ON s.branch_id = b.branch_id
  LEFT JOIN placement p ON p.student_id = s.student_id AND p.is_active = 1
  LEFT JOIN offer o ON o.offer_id = p.offer_id
 GROUP BY b.branch_name
 ORDER BY placement_rate DESC;

-- ------------------------------------------------------------
-- 4. Subqueries
-- ------------------------------------------------------------
-- 4a. Students with CGPA above the college average
SELECT u.full_name, s.cgpa
  FROM student s
  JOIN app_user u ON u.user_id = s.user_id
 WHERE s.cgpa > (SELECT AVG(cgpa) FROM student)
 ORDER BY s.cgpa DESC;

-- 4b. Jobs paying above the average CTC for their own company
SELECT j.job_title, c.company_name, j.ctc
  FROM job j
  JOIN company c ON c.company_id = j.company_id
 WHERE j.ctc > (
        SELECT AVG(j2.ctc)
          FROM job j2
         WHERE j2.company_id = j.company_id
       )
 ORDER BY j.ctc DESC;

-- 4c. ANY / ALL
SELECT u.full_name, s.cgpa
  FROM student s
  JOIN app_user u ON u.user_id = s.user_id
 WHERE s.cgpa >= ALL (SELECT cgpa FROM student WHERE branch_id = 1);
-- (>= ALL is equivalent to >= the maximum CGPA in branch 1)

SELECT DISTINCT c.company_name
  FROM company c
  JOIN job j ON j.company_id = c.company_id
 WHERE j.ctc > ANY (SELECT ctc FROM job WHERE company_id = 2);

-- 4d. EXISTS / NOT EXISTS
SELECT u.full_name
  FROM student s
  JOIN app_user u ON u.user_id = s.user_id
 WHERE NOT EXISTS (
        SELECT 1 FROM application a WHERE a.student_id = s.student_id
       );

SELECT c.company_name
  FROM company c
 WHERE EXISTS (
        SELECT 1 FROM job j WHERE j.company_id = c.company_id
       );

-- ------------------------------------------------------------
-- 5. UNION / INTERSECT / EXCEPT
-- ------------------------------------------------------------
-- UNION: everyone who applied to Apex Quantum or Vanguard Systems
SELECT u.full_name, 'Applied' AS activity
  FROM application a
  JOIN student s ON s.student_id = a.student_id
  JOIN app_user u ON u.user_id = s.user_id
  JOIN job j ON j.job_id = a.job_id
 WHERE j.company_id = 1
UNION
SELECT u.full_name, 'Applied' AS activity
  FROM application a
  JOIN student s ON s.student_id = a.student_id
  JOIN app_user u ON u.user_id = s.user_id
  JOIN job j ON j.job_id = a.job_id
 WHERE j.company_id = 2;

-- INTERSECT (8.0.31+): students who applied to both company 1 and company 2
SELECT s.student_id
  FROM application a
  JOIN job j ON j.job_id = a.job_id
 WHERE j.company_id = 1
INTERSECT
SELECT s.student_id
  FROM application a
  JOIN job j ON j.job_id = a.job_id
 WHERE j.company_id = 2;

-- EXCEPT (8.0.31+): students who applied to Apex but never to Zenith
SELECT s.student_id
  FROM application a
  JOIN job j ON j.job_id = a.job_id
 WHERE j.company_id = 1
EXCEPT
SELECT s.student_id
  FROM application a
  JOIN job j ON j.job_id = a.job_id
 WHERE j.company_id = 3;

-- ------------------------------------------------------------
-- 6. Nested query + aggregate function
-- ------------------------------------------------------------
SELECT c.company_name,
       (SELECT COUNT(*) FROM job j WHERE j.company_id = c.company_id) AS open_jobs,
       fn_company_avg_ctc(c.company_id) AS avg_accepted_ctc
  FROM company c
 ORDER BY fn_company_avg_ctc(c.company_id) DESC;

-- ------------------------------------------------------------
-- 7. Correlated subquery ranking (no window functions)
-- ------------------------------------------------------------
SELECT b.branch_name,
       u.full_name,
       s.cgpa,
       (SELECT COUNT(*) + 1
          FROM student s2
         WHERE s2.branch_id = s.branch_id
           AND s2.cgpa > s.cgpa) AS rank_in_branch
  FROM student s
  JOIN app_user u ON u.user_id = s.user_id
  JOIN branch b ON b.branch_id = s.branch_id
 ORDER BY b.branch_name, rank_in_branch;
