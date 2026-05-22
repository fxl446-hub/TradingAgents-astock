"""Generate PDF reports from analysis results using fpdf2.

Font strategy follows Chinese financial industry conventions:
- 微软雅黑 (msyh/msyhbd): body text and headings
- Arial-style Latin glyphs are built into 微软雅黑
- Hierarchy: Title 16pt > H1 14pt > H2 13pt > H3 11pt > Body 12pt > Footnote 9pt
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fpdf import FPDF


# Font candidates ordered by preference: bundled Noto Sans SC first (.ttf, reliable metrics),
# then Windows system fonts (compliance-safe), then macOS/Linux paths.
_FONT_REGULAR_CANDIDATES = [
    Path(__file__).parent.parent / "assets" / "NotoSansSC-Regular.ttf",
    "C:/Windows/Fonts/msyh.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf",
    "/usr/share/fonts/noto-cjk/NotoSansCJKsc-Regular.otf",
]
_FONT_BOLD_CANDIDATES = [
    Path(__file__).parent.parent / "assets" / "NotoSansSC-Regular.ttf",
    "C:/Windows/Fonts/msyhbd.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf",
    "/usr/share/fonts/noto-cjk/NotoSansCJKsc-Regular.otf",
]


def _find_font(candidates: list) -> str | None:
    for path in candidates:
        if Path(path).exists():
            return str(path)
    return None


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()


def _strip_md_inline(text: str) -> str:
    """Remove inline markdown formatting."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    return text


# Unicode ranges that CJK fonts typically do not cover (emoji, pictographs)
_RE_STRIP_SYMBOLS = re.compile(
    "[️︎‍⃣"      # variation selectors, ZWJ, keycap
    "☀-⯿"                   # misc symbols + dingbats (⭐ ✅ ❌ etc.)
    "\U0001f300-\U0001ffff"           # emoji & emoticons (supplementary)
    "]"
)


def _sanitize_for_cjk(text: str) -> str:
    """Strip emoji, variation selectors, and other chars not in CJK fonts."""
    return _RE_STRIP_SYMBOLS.sub("", text)


def _signal_color(signal: str) -> tuple[int, int, int]:
    s = signal.upper()
    if "BUY" in s:
        return (34, 197, 94)
    if "SELL" in s:
        return (239, 68, 68)
    return (251, 191, 36)


_REPORT_SECTIONS = [
    ("market_report", "技术分析报告"),
    ("sentiment_report", "市场情绪报告"),
    ("news_report", "新闻舆情报告"),
    ("fundamentals_report", "基本面报告"),
    ("policy_report", "政策分析报告"),
    ("hot_money_report", "游资追踪报告"),
    ("lockup_report", "解禁/减持报告"),
]

# ---- Brand color: orange-red (中信/华泰 style accent) ----
_BRAND_R = 255
_BRAND_G = 90
_BRAND_B = 31


class _ReportPDF(FPDF):
    """A-stock research report PDF, styled per Chinese financial industry norms."""

    def __init__(self, ticker: str, trade_date: str, signal: str) -> None:
        super().__init__()
        self.ticker = ticker
        self.trade_date = trade_date
        self.signal = signal
        self._has_cjk = False

        regular_path = _find_font(_FONT_REGULAR_CANDIDATES)
        if regular_path:
            self.add_font("CJK", "", regular_path)
            bold_path = _find_font(_FONT_BOLD_CANDIDATES)
            self.add_font("CJK", "B", bold_path or regular_path)
            self._has_cjk = True

    # -- font helpers ----------------------------------------------------------

    def _zh(self, style: str = "", size: int = 12) -> None:
        """Set CJK font at given size, or fall back to Helvetica."""
        if self._has_cjk:
            self.set_font("CJK", style, size)
        else:
            self.set_font("Helvetica", style, size)

    # -- page chrome -----------------------------------------------------------

    def header(self) -> None:
        self._zh("", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, f"A股多Agent投研分析  |  {self.ticker}  |  {self.trade_date}", align="C")
        self.ln(8)
        self.set_x(self.l_margin)
        self.set_draw_color(200, 200, 200)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)
        self.set_x(self.l_margin)

    def footer(self) -> None:
        self.set_y(-20)
        self._zh("", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, f"Page {self.page_no()}/{{nb}}", align="C",
                  new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(180, 180, 180)
        self.cell(0, 5, "本报告由AI自动生成，仅供学习研究，不构成投资建议", align="C",
                  new_x="LMARGIN", new_y="NEXT")

    # -- cover page ------------------------------------------------------------

    def add_cover(self) -> None:
        self.add_page()
        self.ln(50)

        # Report type label
        self._zh("B", 16)
        self.set_text_color(_BRAND_R, _BRAND_G, _BRAND_B)
        self.cell(0, 10, "A股多Agent投研分析报告", align="C")
        self.set_x(self.l_margin)
        self.ln(18)

        # Ticker code (large)
        self._zh("B", 36)
        self.set_text_color(30, 30, 30)
        self.cell(0, 18, self.ticker, align="C")
        self.set_x(self.l_margin)
        self.ln(14)

        # Meta line
        self._zh("", 14)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f"分析日期: {self.trade_date}", align="C")
        self.set_x(self.l_margin)
        self.ln(6)
        self.cell(0, 10, f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")
        self.set_x(self.l_margin)
        self.ln(22)

        # Signal badge (large colored text)
        r, g, b = _signal_color(self.signal)
        self._zh("B", 40)
        self.set_text_color(r, g, b)
        self.cell(0, 20, self.signal.upper(), align="C")
        self.set_x(self.l_margin)
        self.ln(28)

        # Disclaimer block
        self._zh("", 9)
        self.set_text_color(120, 120, 120)
        self.multi_cell(
            0, 7,
            "免责声明: 本报告由 AI 多 Agent 系统自动生成, 仅供学习研究与技术演示, "
            "不构成任何投资建议。投资决策请咨询持牌专业机构。",
            align="C",
        )
        self.set_x(self.l_margin)
        self.ln(4)
        self.multi_cell(
            0, 7,
            "Analyst reports are auto-generated. For reference only. "
            "Consult licensed professionals before making investment decisions.",
            align="C",
        )
        self.set_x(self.l_margin)

    # -- section pages ---------------------------------------------------------

    def add_section(self, title: str, content: str) -> None:
        self.add_page()
        self._zh("B", 14)
        self.set_text_color(_BRAND_R, _BRAND_G, _BRAND_B)
        self.cell(0, 10, _sanitize_for_cjk(title))
        self.set_x(self.l_margin)
        self.ln(14)

        cleaned = _strip_think(content)
        self._render_markdown(_sanitize_for_cjk(cleaned))

    # -- markdown renderer -----------------------------------------------------

    def _render_markdown(self, text: str) -> None:
        lines = text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Empty line
            if not stripped:
                self.ln(4)
                i += 1
                continue

            # Headings: ### → 11pt, ## → 13pt, # → 14pt (all bold 黑体)
            if stripped.startswith("###"):
                self._zh("B", 11)
                self.set_text_color(60, 60, 60)
                self.cell(0, 8, stripped.lstrip("#").strip())
                self.set_x(self.l_margin)
                self.ln(10)
                i += 1
                continue
            if stripped.startswith("##"):
                self._zh("B", 13)
                self.set_text_color(40, 40, 40)
                self.cell(0, 9, stripped.lstrip("#").strip())
                self.set_x(self.l_margin)
                self.ln(11)
                i += 1
                continue
            if stripped.startswith("#"):
                self._zh("B", 14)
                self.set_text_color(_BRAND_R, _BRAND_G, _BRAND_B)
                self.cell(0, 10, stripped.lstrip("#").strip())
                self.set_x(self.l_margin)
                self.ln(12)
                i += 1
                continue

            # Horizontal rule
            if stripped in ("---", "***", "___"):
                self.set_draw_color(200, 200, 200)
                y = self.get_y() + 2
                self.line(self.l_margin, y, self.w - self.r_margin, y)
                self.ln(6)
                i += 1
                continue

            # Bullet / numbered list items (use "- " instead of "•" for font safety)
            if re.match(r"^[-*]\s", stripped) or re.match(r"^\d+[.)]\s", stripped):
                self._zh("", 12)
                self.set_text_color(50, 50, 50)
                if re.match(r"^[-*]\s", stripped):
                    label = "  —  "
                    body = stripped[2:].strip()
                else:
                    m = re.match(r"^(\d+[.)])\s*(.*)", stripped)
                    label = f"  {m.group(1)} "
                    body = m.group(2)
                body = _strip_md_inline(body)
                self.multi_cell(0, 8, label + body)
                self.set_x(self.l_margin)
                i += 1
                continue

            # Table rows
            if stripped.startswith("|") and stripped.endswith("|"):
                if re.match(r"^\|[-:\s|]+\|$", stripped):
                    i += 1
                    continue
                self._zh("", 9)
                self.set_text_color(70, 70, 70)
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                row_text = "    ".join(_strip_md_inline(c) for c in cells)
                self.multi_cell(0, 6.5, row_text)
                self.set_x(self.l_margin)
                i += 1
                continue

            # Regular paragraph — collect consecutive non-special lines
            para_lines = []
            while i < len(lines):
                ln = lines[i].strip()
                if (not ln or ln.startswith("#") or ln.startswith("|")
                        or re.match(r"^[-*]\s", ln)
                        or re.match(r"^\d+[.)]\s", ln)
                        or ln in ("---", "***", "___")):
                    break
                para_lines.append(ln)
                i += 1

            if para_lines:
                self._zh("", 12)
                self.set_text_color(50, 50, 50)
                para = " ".join(para_lines)
                para = _strip_md_inline(para)
                self.multi_cell(0, 8, para)
                self.set_x(self.l_margin)
                self.ln(3)
                continue

            i += 1


# ---- public API -------------------------------------------------------------


def generate_pdf(
    final_state: dict[str, Any], ticker: str, trade_date: str, signal: str
) -> bytes:
    """Generate a Chinese financial research report as PDF bytes."""
    pdf = _ReportPDF(ticker, trade_date, signal)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=22)

    pdf.add_cover()

    for key, title in _REPORT_SECTIONS:
        content = final_state.get(key, "")
        if content:
            pdf.add_section(title, str(content))

    debate = final_state.get("investment_debate_state")
    if debate and isinstance(debate, dict):
        parts = []
        if debate.get("bull_history"):
            parts.append(f"=== 多方论点 ===\n{debate['bull_history']}")
        if debate.get("bear_history"):
            parts.append(f"\n=== 空方论点 ===\n{debate['bear_history']}")
        if debate.get("judge_decision"):
            parts.append(f"\n=== 研究经理决策 ===\n{debate['judge_decision']}")
        if parts:
            pdf.add_section("多空辩论", "\n".join(parts))

    trader_decision = final_state.get("trader_investment_decision", "")
    if trader_decision:
        pdf.add_section("交易员决策", _strip_think(str(trader_decision)))

    inv_plan = final_state.get("investment_plan", "")
    if inv_plan:
        pdf.add_section("最终投资建议", _strip_think(str(inv_plan)))

    risk = final_state.get("risk_debate_state")
    if risk and isinstance(risk, dict):
        parts = []
        for key_name, label in [
            ("aggressive_history", "激进观点"),
            ("conservative_history", "保守观点"),
            ("neutral_history", "中性观点"),
        ]:
            if risk.get(key_name):
                parts.append(f"=== {label} ===\n{risk[key_name]}")
        if risk.get("judge_decision"):
            parts.append(f"\n=== 风控决策 ===\n{risk['judge_decision']}")
        if parts:
            pdf.add_section("风控评估", "\n".join(parts))

    final_decision = final_state.get("final_trade_decision", "")
    if final_decision:
        pdf.add_section("最终决策", _strip_think(str(final_decision)))

    return bytes(pdf.output())
