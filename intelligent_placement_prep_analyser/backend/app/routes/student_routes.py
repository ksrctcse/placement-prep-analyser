
"""
Student Routes - delegates to student_dashboard for full implementation
"""
from fastapi import APIRouter

router = APIRouter(prefix="/student")

# Note: All student endpoints are implemented in student_dashboard.py
# This file is kept for backwards compatibility
# Remove this file if no additional routes are needed here
