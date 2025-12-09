"""Salesforce API endpoints for testing and direct access."""

from fastapi import APIRouter
from fastapi.responses import Response

from .schemas.api import (
    FileResponse,
    LibraryFilesResponse,
    LibraryResponse,
)
from .service import FilesServiceDep, LibrariesServiceDep

router = APIRouter(prefix="/salesforce", tags=["Salesforce"])


@router.get("/libraries", response_model=list[LibraryResponse])
def list_libraries(libraries_service: LibrariesServiceDep) -> list[LibraryResponse]:
    """List all Salesforce Content Libraries."""
    libraries = libraries_service.list_libraries()
    return [LibraryResponse.model_validate(lib) for lib in libraries]


@router.get("/libraries/{library_name}/files", response_model=LibraryFilesResponse)
def list_library_files(
    library_name: str,
    files_service: FilesServiceDep,
) -> LibraryFilesResponse:
    """List all files in a specific library."""
    files = files_service.list_files_in_library(library_name)
    return LibraryFilesResponse(
        library_name=library_name,
        total_files=len(files),
        files=[FileResponse.model_validate(f) for f in files],
    )


@router.get("/libraries/{library_name}/files/{file_name}/download")
def download_file_by_name(
    library_name: str,
    file_name: str,
    files_service: FilesServiceDep,
) -> Response:
    """Download a file by library and file name."""
    result = files_service.download_by_name(library_name, file_name)
    if not result:
        return Response(content="File not found", status_code=404)

    file_bytes, filename = result
    return Response(
        content=file_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
