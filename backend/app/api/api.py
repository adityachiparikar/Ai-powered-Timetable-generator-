from fastapi import APIRouter
from app.api.endpoints import login, teachers, courses, student_groups, solver, ai, rooms, breaks, imports

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(teachers.router, prefix="/teachers", tags=["teachers"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(student_groups.router, prefix="/student-groups", tags=["student-groups"])
api_router.include_router(solver.router, prefix="/solver", tags=["solver"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(breaks.router, prefix="/breaks", tags=["breaks"])
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
