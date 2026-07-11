from fastapi import APIRouter

router = APIRouter(prefix="/login")

@router.post("/web")
async def login_web():
    pass