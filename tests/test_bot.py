from bot.charts import build_audit_chart
from bot.handlers import _format_report, _is_url


def test_is_url_detects_http_links() -> None:
    assert _is_url("https://youtube.com/watch?v=abc") is True
    assert _is_url("plain text") is False


def test_format_report_contains_key_sections(make_audit_response) -> None:
    report = _format_report(make_audit_response())
    assert "ConTelli Audit Report" in report
    assert "Viral Score" in report
    assert "Sentiment" in report
    assert "Engagement Triggers" in report


def test_format_report_escapes_html(make_audit_response) -> None:
    report = _format_report(make_audit_response(content="<script>alert('x')</script>"))
    assert "<script>" not in report
    assert "&lt;script&gt;" in report


async def test_build_audit_chart_returns_png_buffer(make_audit_response) -> None:
    chart = await build_audit_chart(make_audit_response().model_dump())
    data = chart.read(8)
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
