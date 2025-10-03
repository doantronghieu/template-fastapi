from fastapi import APIRouter, Request

from app.core.templates import templates

router = APIRouter()


@router.get("/", include_in_schema=False)
async def home(request: Request):
    """Render home page."""
    return templates.TemplateResponse("index.html", {"request": request})
