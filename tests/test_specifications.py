"""Documentation specifications must track the current model in both languages."""

import copy

import pytest
import specifications


def test_committed_specifications_match_the_current_model(data):
    assert specifications.update(data, check=True) == [], "Run make specs"


def test_specs_read_wall_thickness_and_derived_levels(data):
    changed = copy.deepcopy(data)
    changed["config"]["thickness"]["wall"] = 6
    changed["derived"]["floor_tops"][0] += 1
    assert "6 mm walls" in specifications.tower_description(changed["config"])
    values = dict(specifications.rows(changed))
    assert values["Tower diameter / wall plywood"].endswith("/ 6 mm")
    assert f"Z{changed['derived']['floor_tops'][0]:g}" in values["Floor plywood / floor tops"]


def test_book_specs_use_material_thickness_and_actual_deck_placement(data):
    values = dict(specifications.book_rows(data, 300, "right", "left"))
    assert f"{data['config']['thickness']['wall']:g} mm walls" in values["Tower"]
    deck = next(i for i in data["instances"] if i["design_part"] == "E03")
    top = deck["origin"][2] + deck["w"][2] * data["parts"][deck["part"]]["thickness"]
    assert f"deck top Z{top:g}" in values["Veranda"]


def test_book_dimension_rows_fit_the_printed_column(data):
    from reportlab.pdfbase.pdfmetrics import stringWidth

    rows = specifications.book_rows(data, 260, "W01, W02 and W03", "W10, W01 and W12")
    for name, value in rows:
        assert stringWidth(value, "Helvetica", 8) <= 423, name


def test_block_updates_preserve_surrounding_text():
    text = (
        "user introduction\n"
        + specifications.START
        + "\nstale\n"
        + specifications.END
        + "\nuser notes"
    )
    assert specifications.replace_block(text, "new") == text.replace("stale", "new")
    for invalid in ("missing markers", specifications.END + specifications.START, text + text):
        with pytest.raises(ValueError, match="marker"):
            specifications.replace_block(invalid, "new")
