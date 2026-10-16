"""Shared naming contract for Lanternwood House.

Keep these values consistent across Python producers, consumers, HTML, tests and workflows.
"""

NAME = "Lanternwood House"
DISPLAY_NAME = "Lanternwood House"
OWNER = "hvitis"
REPO_SLUG = "lanternwood-house"
REPO_URL = f"https://github.com/{OWNER}/{REPO_SLUG}"
CLONE_URL = f"{REPO_URL}.git"
PAGES_URL = f"https://{OWNER}.github.io/{REPO_SLUG}/"
LATEST_RELEASE_URL = f"{REPO_URL}/releases/latest"

PREFIX = "Lanternwood-House"
CAD_STEM = "LanternwoodHouse"
CAD_DOCUMENT = f"{CAD_STEM}.FCStd"
NPM_PACKAGE = "lanternwood-house-viewer-checks"
HEADLESS_ENV = "LANTERNWOOD_HEADLESS"
EXPORT_MARKER = ".lanternwood-viewer-export"
STORAGE_KEY_ASSEMBLY = "lanternwood-house:assembly:v1"
STORAGE_KEY_LANG = "lanternwood-house:instructions:lang"

FONT_REGULAR = "LanternwoodSans"
FONT_BOLD = "LanternwoodSans-Bold"

PDF_KEY_PAGE_ROLE = "/LanternwoodPageRole"
PDF_KEY_SHEET_ID = "/LanternwoodSheetID"
PDF_KEY_OPERATION = "/LanternwoodOperation"

FAMILY_COLLECTION_LABEL_EN = "The Rowan family"
FAMILY_COLLECTION_LABEL_PL = "Rodzina Rowan"

# Deliverable filenames
KIT_ZIP = f"{PREFIX}-Build-Kit.zip"
SUPPLIER_CUT_DXF = f"{PREFIX}-Supplier-Cut.dxf"
PDF_COMPLETE = f"{PREFIX}-Complete.pdf"
PDF_INSTRUCTIONS = f"{PREFIX}-Instructions.pdf"
PDF_CUTTING_TEMPLATES = f"{PREFIX}-Cutting-Templates.pdf"
PDF_3MM_HAND_TEMPLATES = f"{PREFIX}-3mm-Hand-Templates.pdf"
PDF_DIMENSIONED_PARTS = f"{PREFIX}-Dimensioned-Parts.pdf"
PDF_DECOR = f"{PREFIX}-Decor.pdf"
PDF_CLAY_FAMILY = f"{PREFIX}-Clay-Family.pdf"
PDF_SUPPLIER = f"{PREFIX}-Supplier.pdf"
PDF_SUPPLIER_SUMMARY = f"{PREFIX}-Supplier-Summary.pdf"
