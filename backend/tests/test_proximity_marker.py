import pytest
import pytest_asyncio
from playwright.async_api import async_playwright

import config_marker as config
from v1.uploaded.project_markers import proximity_marker as marker


@pytest_asyncio.fixture
async def page(monkeypatch):
    monkeypatch.setattr(config, "form_sections", ["user-details", "address-details", "contact-details"])
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = await browser.new_page()
        yield page
        await browser.close()


async def layout(page, within=10, between=(50, 50), titles="", hidden_inputs=False, reversed_sections=False):
    sections = []
    y = 0
    for index, name in enumerate(config.form_sections):
        title = titles if index == 0 else ""
        hidden = '<input type="hidden"><input style="display:none">' if hidden_inputs else ""
        sections.append(f'<section id="{name}" style="position:absolute;top:{y}px;width:200px;height:{40 + within}px">{title}{hidden}<input style="top:0"><input style="top:{20 + within}px"></section>')
        if index < len(between):
            y += 40 + within + between[index]
    if reversed_sections:
        sections.reverse()
    await page.set_content('<style>input{position:absolute;left:0;width:100px;height:20px;box-sizing:border-box;padding:0;border:0}</style><div id="form-ct" style="position:relative;width:300px;height:3000px">' + "".join(sections) + '</div>')


@pytest.mark.asyncio
async def test_good_proximity_and_rendered_distances(page):
    await layout(page, hidden_inputs=True, reversed_sections=True)
    previous_results = {"Other marker": 123}
    result = await marker.run_marker(page, previous_results)
    assert result == {
        "Proximity-mark": 2, "proximityPenalties": "", "flags": "",
        "user-details0": 10, "address-details0": 10, "contact-details0": 10,
        "section0": 50, "section1": 50,
    }
    assert previous_results == {"Other marker": 123}


@pytest.mark.asyncio
@pytest.mark.parametrize("within,between,score,penalty", [
    (30, (10, 10), 0, "Average distance between groups"),
    (10, (5, 100), 1, "Minimum distance between groups"),
    (10, (10, 10), 2, ""),
    (0, (0, 0), 0, "Distance within and between groups is 0"),
    (10, (1100, 1100), 1, "Malformed group structure"),
])
async def test_original_scoring_rules(page, within, between, score, penalty):
    await layout(page, within=within, between=between)
    result = await marker.run_marker(page, {})
    assert result["Proximity-mark"] == score
    assert penalty in result["proximityPenalties"]
    assert isinstance(result["flags"], str)


@pytest.mark.asyncio
async def test_section_title_flags_are_visible_and_scoped(page):
    await layout(page, titles='<h2>User Details</h2><h2 hidden>Address Details</h2>')
    await page.locator("body").evaluate("element => element.insertAdjacentHTML('beforeend', '<h2>Contact Details</h2>')")
    result = await marker.run_marker(page, {})
    assert result["Proximity-mark"] == 2
    assert result["flags"] == "The section user-details does not fully rely on proximity."


@pytest.mark.asyncio
async def test_empty_and_missing_sections(page):
    await page.set_content('<div id="form-ct" style="min-height:20px"><section id="user-details" style="min-height:10px"><input type="hidden"></section></div>')
    result = await marker.run_marker(page, {})
    assert result["Proximity-mark"] == 0
    assert "Can't find user-details section elements" in result["proximityPenalties"]
    assert "Can't find address-details section" in result["proximityPenalties"]
    assert "No sections found" in result["proximityPenalties"]
    assert result["flags"] == ""


@pytest.mark.asyncio
async def test_one_section_cannot_measure_between_sections(page, monkeypatch):
    monkeypatch.setattr(config, "form_sections", ["user-details"])
    await page.set_content('<div id="form-ct"><section id="user-details"><input></section></div>')
    result = await marker.run_marker(page, {})
    assert result["Proximity-mark"] == 1
    assert result["proximityPenalties"] == "Only one section in the form"


@pytest.mark.asyncio
async def test_marker_opens_popup_only_when_needed(page):
    await layout(page)
    await page.locator("#form-ct").evaluate("element => element.style.display = 'none'")
    await page.locator("body").evaluate("element => element.insertAdjacentHTML('afterbegin', `<button id='trigger-modal' onclick=\"window.clicks=(window.clicks||0)+1;document.getElementById('form-ct').style.display='block'\">Open</button>`)")
    assert (await marker.run_marker(page, {}))["Proximity-mark"] == 2
    assert (await marker.run_marker(page, {}))["Proximity-mark"] == 2
    assert await page.evaluate("window.clicks") == 1


@pytest.mark.asyncio
async def test_popup_failures_have_zero_marks_and_string_messages(page, monkeypatch):
    async def quick_trigger(page, element_id):
        trigger = page.locator(f"#{element_id}")
        await trigger.wait_for(state="visible", timeout=50)
        return trigger

    monkeypatch.setattr(marker.marchir_util, "wait_for_clickable_element_with_id", quick_trigger)
    await page.set_content("<p>No form</p>")
    result = await marker.run_marker(page, {})
    assert result == {"Proximity-mark": 0, "proximityPenalties": "Can't click element id=trigger-modal", "flags": ""}

    async def quick_form(page, element_id, timeout):
        form = page.locator(f"#{element_id}")
        await form.wait_for(state="visible", timeout=50)
        return form

    monkeypatch.setattr(marker.marchir_util, "wait_for_visible_element_with_id", quick_form)
    await page.set_content('<button id="trigger-modal">Open</button>')
    result = await marker.run_marker(page, {})
    assert result == {"Proximity-mark": 0, "proximityPenalties": "Can't find visible id=form-ct", "flags": ""}
