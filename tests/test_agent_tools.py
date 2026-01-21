from agents.tools.calculator import calculate
from agents.tools.dashboard_analysis import analyze_dashboard
from agents.tools.report_generator import generate_report
from agents.tools.pdf_exporter import generate_pdf

print("\n--- TOOL TEST SUITE START ---\n")

# ===============================
# 1️⃣ Calculator Tool
# ===============================
print("[1] Calculator Tests")
print("Add:", calculate("add", 5, 3))
print("Subtract:", calculate("subtract", 10, 4))
print("Multiply:", calculate("multiply", 6, 7))
print("Divide:", calculate("divide", 8, 2))
print("Divide by zero:", calculate("divide", 5, 0))

# ===============================
# 2️⃣ Dashboard Analysis Tool
# ===============================
print("\n[2] Dashboard Analysis Test")
dashboard_stats = {
    "total_products": 12,
    "total_orders": 58,
    "pending_orders": 9,
    "low_stock_products": 3,
}

analysis = analyze_dashboard(dashboard_stats)
print(analysis)

# ===============================
# 3️⃣ Report Generator Tool
# ===============================
print("\n[3] Report Generator Test")
report = generate_report(
    title="Seller Dashboard Report",
    analysis=analysis
)
print(report)

# ===============================
# 4️⃣ PDF Export Tool
# ===============================
print("\n[4] PDF Export Test")
pdf_result = generate_pdf(report, "seller_report_test.pdf")
print(pdf_result)

print("\n--- TOOL TEST SUITE END ---")
