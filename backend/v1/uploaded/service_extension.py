
from fastapi import HTTPException
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError


async def find_form_element(page: Page, form_id: str = "form-ct") -> Optional[Locator]:
    xpath = f'//div[@id="{form_id}"]//form'
    locator = page.locator(f"xpath={xpath}")

    # "exists" check: count() hits the DOM and returns 0 if not found
    if await locator.count() == 0:
        return None

    # If you specifically want the first matching form
    return locator.first


async def start_validation(index_path: Path) -> bool:
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


