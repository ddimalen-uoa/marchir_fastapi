
from fastapi import HTTPException
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import config_validator as config
from v1.uploaded.classes.validation_messages_class import ValidationMessages

async def validate_page(context, file_url: str) -> bool:

    validation_messages_dataframe = ValidationMessages()

    page = await context.new_page()

    await page.goto(file_url, wait_until="networkidle")

    validation_results = {}
    
    for validator_name in config.validator_functions.keys():
        validation_function_results = await config.validator_functions[validator_name](page, validation_messages_dataframe)
        validation_results[validator_name] = []
        for validation_title in validation_function_results.keys():
            validation_result = validation_function_results[validation_title][0]
            validation_messages = validation_function_results[validation_title][1]

            validation_results[validator_name].append([validation_title, validation_result, validation_messages])

    print("RESULTS DISPLAYED:")

    print(validation_results)

    # el = await page.query_selector("#test")
    # found = el is not None

    await page.close()  # 🔥 Important to prevent memory leaks

    return "DONE"


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