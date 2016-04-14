1. The PostgreSQL account where your database on our server resides. (This should be the same database that you used for Part 2, but we need you to confirm that we should check that database.)
- mw3061

2. The URL of your web application.
- http://137.117.50.223:8111/

3. A description of the parts of your original proposal in Part 1 that you implemented, the parts you did not (which hopefully is nothing or something very small), and possibly new features that were not included in the proposal and that you implemented anyway. If you did not implement some part of the proposal in Part 1, explain why.
 - I implemented all design in the proposal.

3. Briefly describe two of the web pages that require (what you consider) the most interesting database operations in terms of what the pages are used for, how the page is related to the database operations (e.g., inputs on the page are used in such and such way to produce database operations that do such and such), and why you think they are interesting.

a. team_edit.html: This page allows student to form teams with other students. I firstly select all students who enroll the course and then put them in a drop-down menu for the student to choose. If the current team is already in maximum size OR the team has been approved/confirmed by the professor, the student is not allowed to edit the team information.


b. remove_course.html: This page allows professors to remove a course. It is not easy because course id is the foreign key of many other relations. A cascaded deletion is performed here.