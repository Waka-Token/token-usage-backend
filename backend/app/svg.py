from html import escape

COLOR_MAP = {
    "blue": "#4568dc",
    "green": "#2da66f",
    "yellow": "#d6a700",
    "orange": "#e07a2f",
    "red": "#d64545",
    "purple": "#8057c8",
    "black": "#172026",
    "gray": "#6b7280",
}


def compact_number(value: int | float) -> str:
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs_value >= 1_000:
        return f"{value / 1_000:.1f}K"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def auto_color(total_tokens: int) -> str:
    if total_tokens >= 1_000_000:
        return "red"
    if total_tokens >= 250_000:
        return "orange"
    if total_tokens >= 50_000:
        return "yellow"
    return "green"


def render_badge(label: str, message: str, color: str = "blue", style: str = "flat") -> str:
    label = escape(label)
    message = escape(message)
    right_color = COLOR_MAP.get(color, color if color.startswith("#") else COLOR_MAP["blue"])
    left_color = "#555"
    font_size = 11 if style != "for-the-badge" else 12
    height = 20 if style != "for-the-badge" else 28
    radius = 0 if style == "flat-square" else 3
    label_width = max(48, len(label) * 7 + 10)
    message_width = max(54, len(message) * 7 + 10)
    total_width = label_width + message_width
    text_y = 14 if style != "for-the-badge" else 18

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}" role="img" aria-label="{label}: {message}">
  <title>{label}: {message}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="{total_width}" height="{height}" rx="{radius}" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="{height}" fill="{left_color}"/>
    <rect x="{label_width}" width="{message_width}" height="{height}" fill="{right_color}"/>
    <rect width="{total_width}" height="{height}" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="{font_size}">
    <text x="{label_width / 2}" y="{text_y}" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width / 2}" y="{text_y - 1}">{label}</text>
    <text x="{label_width + message_width / 2}" y="{text_y}" fill="#010101" fill-opacity=".3">{message}</text>
    <text x="{label_width + message_width / 2}" y="{text_y - 1}">{message}</text>
  </g>
</svg>
"""

