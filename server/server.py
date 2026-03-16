# This program will look at Canvas assignments and return their information.

# server/test_get_grade.py
from canvasapi import Canvas
from dotenv import load_dotenv
import os

load_dotenv()  # loads .env in same folder or parent

CANVAS_API_URL = os.getenv("CANVAS_API_URL")
CANVAS_API_TOKEN = os.getenv("CANVAS_API_TOKEN")
COURSE_ID = os.getenv("COURSE_ID")  # the numeric course id

if not CANVAS_API_URL or not CANVAS_API_TOKEN or not COURSE_ID:
    raise SystemExit("Missing CANVAS_API_URL, CANVAS_API_TOKEN, or COURSE_ID in environment.")

canvas = Canvas(CANVAS_API_URL, CANVAS_API_TOKEN)

# this fetches the current user's enrollment in the course and prints the computed current score
course = canvas.get_course(int(COURSE_ID))

# Get the current user's grades via the enrollments endpoint for the current user
# Note: get_enrollments requires appropriate permissions on Canvas side for other students; for own grades this works.
enrollments = course.get_enrollments(user_id='self')  # 'self' fetches current user
for enr in enrollments:
    print("Course:", course.name)
    print("Computed current score:", enr.grades.get('computed_current_score'))
    print("Current grade:", enr.grades.get('current_score'))
    print("Current grade string:", enr.grades.get('current_grade'))

    # OAuth 2.0 -- Research this topic, YouTube topic to develop a better understanding.

