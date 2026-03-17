import logger
from fastapi import UploadFile, HTTPException
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select, func, distinct
from math import ceil

from config.core import DbSession

import pandas as pd
from pathlib import Path
import tempfile
import zipfile
import os
from config.core import engine
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

from v1.uploaded.service_extension import start_validation, start_submit_assignment
from v1.uploaded.classes.validation_messages_class import ValidationMessages
from v1.auth.service_extension import CurrentMember, StudentMember, CurrentEnrollment

from v1.marker_result.model import MarkerResult

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


async def upload_zip(
        member: StudentMember,
        file: UploadFile,
        db: DbSession = None # type: ignore
    ):
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

        validation_result = await start_validation(index_path)

        return validation_result


async def submit_assignment(
        member: StudentMember,
        enrollment: CurrentEnrollment,
        file: UploadFile,
        db: DbSession = None # type: ignore
    ):
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

        submission_output = await start_submit_assignment(index_path)
        
        existing_enrollment = db.query(MarkerResult).filter(
                                     MarkerResult.enrollment_id == enrollment.id
                              ).first()
        
        now = datetime.now(ZoneInfo("Pacific/Auckland"))
        filename = f"submission_{now.strftime('%m_%Y')}.zip"

        if existing_enrollment:
            existing_enrollment.result = submission_output
            existing_enrollment.file_name = filename

            db.commit()
            db.refresh(existing_enrollment)
        else:
            marker_result = MarkerResult(
                enrollment_id=enrollment.id,
                upi=member.upi,
                file_name=filename,
                status="Submitted",
                result=submission_output
            )

            db.add(marker_result)
            db.commit()
            db.refresh(marker_result)

        course_name = enrollment.course.name  # adjust if different
        upi = member.upi

        safe_course_name = course_name.replace(" ", "_")  # basic sanitization
        target_dir = Path(f"/marchir/uploads/{safe_course_name}/{upi}")

        target_dir.mkdir(parents=True, exist_ok=True)

        destination = target_dir / filename

        shutil.copy(zip_path, destination)

        return True

async def test_me():
    validation_messages_dataframe = ValidationMessages()

    print(validation_messages_dataframe.find_message_by_code("TEST"))

    return "hello there"