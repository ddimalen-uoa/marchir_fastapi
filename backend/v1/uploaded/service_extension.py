
from fastapi import HTTPException
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import config_validator as config
import config_marker as config_marker
from v1.uploaded.classes.validation_messages_class import ValidationMessages
import v1.uploaded.modules.marchir as marchir_util
import json

def all_valid(validation_results: dict) -> bool:
    return all(
        item["passed"]
        for results in validation_results.values()
        for item in results
    )

async def validate_page(context, file_url: str):
    validation_messages_dataframe = ValidationMessages()

    page = await context.new_page()
    await page.goto(file_url, wait_until="networkidle")

    validation_results = {}

    for validator_name in config.validator_functions.keys():
        validation_function_results = await config.validator_functions[validator_name](
            page, validation_messages_dataframe
        )

        validation_results[validator_name] = []

        for validation_title in validation_function_results.keys():
            validation_result = validation_function_results[validation_title][0]
            validation_messages = validation_function_results[validation_title][1]

            validation_results[validator_name].append({
                "title": validation_title,
                "passed": validation_result,
                "message": validation_messages,
            })

    is_ok = all_valid(validation_results)

    if is_ok:
        print("Yes you are good to go")
    else:
        print("Something is not right")

    await page.close()

    return {
        "isOk": is_ok,
        "validators": validation_results,
    }

async def mark_assignment(context, file_url: str):

    page = await context.new_page()
    await page.goto(file_url, wait_until="networkidle")

    await page.screenshot(path="/uploads/test.png", full_page=True)

    print("Done Screenshot")

    marker_results = {}
    
    print("Start Marker")

    for marker_name in config_marker.marker_functions.keys():
        marker_function_results = await config_marker.marker_functions[marker_name](page, marker_results)

        for marker_title in marker_function_results.keys():
            marker_result = marker_function_results[marker_title]
            marker_results[marker_title] = marker_result
    
    await page.close()

    return json.dumps(marker_results)


async def start_validation(index_path: Path):
    
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

        results = await validate_page(context, file_url)

        await browser.close()

        return results
    
async def start_submit_assignment(index_path: Path):

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

        results = await mark_assignment(context, file_url)

        await browser.close()

        return results