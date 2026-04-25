from pathlib import Path
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
)
from reportlab.lib import colors


REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")
MD_PATH = REPO_ROOT / "paper" / "research_summary.md"
PDF_PATH = REPO_ROOT / "paper" / "research_summary.pdf"

FIG_DIR = REPO_ROOT / "figures" / "paper"

FIGURES = [
    (
        FIG_DIR / "figure1_phase5_delta_target_comparison.png",
        "Figure 1. Phase5 hardware vs simulation delta target comparison.",
    ),
    (
        FIG_DIR / "figure3_phase55_chain_ring_parity_divergence.png",
        "Figure 2. Phase5.5 persistent chain-ring parity divergence across noise scales.",
    ),
    (
        FIG_DIR / "figure4_phase55_noise_response_phase_map.png",
        "Figure 3. Phase5.5 noise response phase map.",
    ),
]


def clean_inline(text: str) -> str:
    text = text.replace("**", "")
    text = text.replace("→", "->")
    text = text.replace("Δ", "Delta ")
    text = text.replace("—", "-")
    text = text.replace("–", "-")
    text = text.replace("≤", "<=")
    text = text.replace("≥", ">=")
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text


def md_to_flowables(md_text: str, styles):
    story = []

    lines = md_text.splitlines()
    in_list = False

    for raw in lines:
        line = raw.rstrip()

        if not line.strip():
            story.append(Spacer(1, 4))
            continue

        if line.strip() == "---":
            story.append(Spacer(1, 8))
            continue

        if line.startswith("# "):
            story.append(Paragraph(clean_inline(line[2:].strip()), styles["TitleCustom"]))
            story.append(Spacer(1, 8))
            continue

        if line.startswith("## "):
            story.append(Spacer(1, 6))
            story.append(Paragraph(clean_inline(line[3:].strip()), styles["Heading1Custom"]))
            story.append(Spacer(1, 4))
            continue

        if line.startswith("### "):
            story.append(Spacer(1, 4))
            story.append(Paragraph(clean_inline(line[4:].strip()), styles["Heading2Custom"]))
            story.append(Spacer(1, 3))
            continue

        if re.match(r"^\s*[-*]\s+", line):
            item = re.sub(r"^\s*[-*]\s+", "", line)
            story.append(Paragraph("• " + clean_inline(item), styles["BulletCustom"]))
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            story.append(Paragraph(clean_inline(line.strip()), styles["BulletCustom"]))
            continue

        story.append(Paragraph(clean_inline(line.strip()), styles["BodyCustom"]))

    return story


def add_figures(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("Figures", styles["Heading1Custom"]))
    story.append(Spacer(1, 8))

    for fig_path, caption in FIGURES:
        if not fig_path.exists():
            story.append(Paragraph(f"Missing figure: {fig_path}", styles["BodyCustom"]))
            story.append(Spacer(1, 10))
            continue

        img = Image(str(fig_path))
        max_width = 170 * mm
        max_height = 110 * mm

        scale = min(max_width / img.imageWidth, max_height / img.imageHeight)
        img.drawWidth = img.imageWidth * scale
        img.drawHeight = img.imageHeight * scale

        story.append(img)
        story.append(Spacer(1, 4))
        story.append(Paragraph(clean_inline(caption), styles["CaptionCustom"]))
        story.append(Spacer(1, 14))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(20 * mm, 10 * mm, "SRFM Quantum Protocol Phase 5 - Yoichi Tsujisawa")
    canvas.drawRightString(190 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf():
    if not MD_PATH.exists():
        raise FileNotFoundError(f"Missing markdown file: {MD_PATH}")

    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)

    md_text = MD_PATH.read_text(encoding="utf-8")

    base = getSampleStyleSheet()

    styles = {
        "TitleCustom": ParagraphStyle(
            "TitleCustom",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "Heading1Custom": ParagraphStyle(
            "Heading1Custom",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=colors.HexColor("#222222"),
            spaceBefore=10,
            spaceAfter=5,
        ),
        "Heading2Custom": ParagraphStyle(
            "Heading2Custom",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#333333"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "BodyCustom": ParagraphStyle(
            "BodyCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            spaceAfter=3,
        ),
        "BulletCustom": ParagraphStyle(
            "BulletCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            leftIndent=10,
            firstLineIndent=-6,
            spaceAfter=2,
        ),
        "CaptionCustom": ParagraphStyle(
            "CaptionCustom",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#444444"),
            spaceAfter=8,
        ),
    }

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="SRFM Quantum Protocol Phase 5 Research Summary",
        author="Yoichi Tsujisawa",
    )

    story = []
    story.extend(md_to_flowables(md_text, styles))
    add_figures(story, styles)

    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    print("PDF generated successfully.")
    print(f"Markdown: {MD_PATH}")
    print(f"PDF     : {PDF_PATH}")


if __name__ == "__main__":
    build_pdf()