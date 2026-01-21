def generate_report(title: str, analysis: dict):
    lines = []
    lines.append(f"# {title}\n")

    for item in analysis.get("summary", []):
        lines.append(f"- {item}")

    lines.append("\n## Raw Data")
    for k, v in analysis.get("raw_stats", {}).items():
        lines.append(f"- {k}: {v}")

    return "\n".join(lines)
def run(summary=None, raw_stats=None):
    summary = summary or []
    raw_stats = raw_stats or {}

    report = "# Seller Dashboard Report\n\n"
    for s in summary:
        report += f"- {s}\n"

    report += "\n## Raw Data\n"
    for k, v in raw_stats.items():
        report += f"- {k}: {v}\n"

    return report
