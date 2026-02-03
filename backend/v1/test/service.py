import logger
from fastapi import UploadFile, HTTPException
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select, func, distinct
from math import ceil

from pathlib import Path
import tempfile
import zipfile
import os

from typing import Optional
from playwright.async_api import async_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError

from v1.test import model as test_models
from . import schema

def get_test_module(
    db: Session    
):
    data = db.query(test_models.TestTable).all()

    return data

def add_test(
        db: Session, 
        add_test_request: schema.AddTestRequest,
    ) -> test_models.TestTable:
    try:
        create_test_model = test_models.TestTable(
            name = add_test_request.name,
            value = add_test_request.value
        )
        db.add(create_test_model)
        db.commit()

        db.refresh(create_test_model)

        return create_test_model
        
    except Exception as e:
        logger.logging.error(
            f"Failed to add item: {add_test_request.name}. Error: {str(e)}"
        )
        db.rollback()
        raise

MAX_ZIP_BYTES = 50 * 1024 * 1024 

def _is_within_directory(base_dir: Path, target: Path) -> bool:
    """Prevent zip-slip: ensure target path stays within base_dir."""
    try:
        base_dir_resolved = base_dir.resolve()
        target_resolved = target.resolve()
        return str(target_resolved).startswith(str(base_dir_resolved) + os.sep)
    except Exception:
        return False


def safe_extract_zip(zip_path: Path, extract_to: Path) -> None:
    """Extract zip while protecting against Zip Slip."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # Disallow absolute paths
            if member.filename.startswith("/") or member.filename.startswith("\\"):
                raise HTTPException(status_code=400, detail="Invalid zip: absolute paths not allowed")

            dest = extract_to / member.filename
            if not _is_within_directory(extract_to, dest):
                raise HTTPException(status_code=400, detail="Invalid zip: path traversal detected")

        zf.extractall(extract_to)

async def find_form_element(page: Page, form_id: str = "form-ct") -> Optional[Locator]:
    xpath = f'//div[@id="{form_id}"]//form'
    locator = page.locator(f"xpath={xpath}")

    # "exists" check: count() hits the DOM and returns 0 if not found
    if await locator.count() == 0:
        return None

    # If you specifically want the first matching form
    return locator.first

async def check_index_for_test_id(index_path: Path) -> bool:
    """
    Open index.html with Playwright and check if #test exists.
    Uses file:// URL so relative assets (css/images) load from extracted folder.
    """
    if not index_path.exists():
        raise HTTPException(status_code=400, detail="index.html not found in zip")

    file_url = index_path.resolve().as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = await browser.new_page()

        # Wait until network is mostly idle to give assets time to load.
        await page.goto(file_url, wait_until="networkidle")

        # Check for element with id="test"
        el = await page.query_selector("#test")
        found = el is not None

        await browser.close()
        return found

async def upload_zip(file: UploadFile):
    # Basic content-type check (not fully reliable, but helpful)
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Please upload a .zip file")

    # Put everything in a temp directory so it auto-cleans easily
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        zip_path = tmp_dir / "upload.zip"
        extract_dir = tmp_dir / "site"

        extract_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded zip to disk with a size cap
        total = 0
        with zip_path.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_ZIP_BYTES:
                    raise HTTPException(status_code=413, detail="Zip file too large")
                f.write(chunk)

        # Validate it's a zip
        if not zipfile.is_zipfile(zip_path):
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid zip")

        # Extract safely
        safe_extract_zip(zip_path, extract_dir)

        # Find index.html (common patterns)
        # - index.html at root
        # - or inside a single top folder (like dist/index.html)
        candidates = [
            extract_dir / "index.html",
        ]

        # If not at root, search for the first index.html (you can tighten this rule)
        if not candidates[0].exists():
            candidates = list(extract_dir.rglob("index.html"))

        if not candidates:
            raise HTTPException(status_code=400, detail="index.html not found in extracted zip")

        # If multiple, pick the shallowest (closest to root)
        index_path = sorted(candidates, key=lambda p: len(p.parts))[0]

        found = await check_index_for_test_id(index_path)

        return "hello" if found else "not found"