

async def run_validator(page):

    print('Selector validation starting')

    el = await page.query_selector("#test")
    found = el is not None

    if found:
        print("Helllsdkfsdlfkjsdfklj")

    return f"Hellow there!!!! from selector_validator"