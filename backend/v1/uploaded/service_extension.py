
from fastapi import HTTPException
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError
import config_validator as config


async def find_form_element(page: Page, form_id: str = "form-ct") -> Optional[Locator]:
    xpath = f'//div[@id="{form_id}"]//form'
    locator = page.locator(f"xpath={xpath}")

    # "exists" check: count() hits the DOM and returns 0 if not found
    if await locator.count() == 0:
        return None

    # If you specifically want the first matching form
    return locator.first



async def validate_page(context, file_url: str) -> bool:
    page = await context.new_page()

    await page.goto(file_url, wait_until="networkidle")



    for validator_name in config.validator_functions.keys():

        validation_function_results = await config.validator_functions[validator_name](page)


    el = await page.query_selector("#test")
    found = el is not None

    await page.close()  # 🔥 Important to prevent memory leaks
    return found


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
            headless=True,  # keep True for server environments
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1920,1080"
            ]
        )

        # 🔥 Disable default viewport so window-size actually applies
        context = await browser.new_context(
            viewport=None
        )

        found = await validate_page(context, file_url)

        await browser.close()
        return found