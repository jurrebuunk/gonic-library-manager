from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["system"])


@router.get("/tools", include_in_schema=False)
def tools_redirect() -> RedirectResponse:
    return RedirectResponse(url="/tools/downloads", status_code=307)


@router.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}
