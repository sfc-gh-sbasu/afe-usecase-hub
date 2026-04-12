#!/usr/bin/env python3
"""Generate the DE Field Use Case Intelligence Hub documentation PDF."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os

OUTPUT_DIR = "/Users/sbasu/Downloads/Work Items/Value_Adds"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "DE_Field_Use_Case_Intelligence_Hub_Guide.pdf")

SNOWFLAKE_BLUE = HexColor("#29B5E8")
SNOWFLAKE_DARK = HexColor("#1B2A4A")
ACCENT_GREEN = HexColor("#2ECC71")
LIGHT_GRAY = HexColor("#F5F7FA")
MEDIUM_GRAY = HexColor("#7F8C8D")
WHITE = HexColor("#FFFFFF")
BLACK = HexColor("#000000")

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "DocTitle", parent=styles["Title"],
    fontSize=28, leading=34, textColor=SNOWFLAKE_DARK,
    spaceAfter=6, alignment=TA_CENTER
)
subtitle_style = ParagraphStyle(
    "DocSubtitle", parent=styles["Normal"],
    fontSize=14, leading=18, textColor=MEDIUM_GRAY,
    spaceAfter=24, alignment=TA_CENTER
)
h1_style = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontSize=20, leading=26, textColor=SNOWFLAKE_DARK,
    spaceBefore=18, spaceAfter=10
)
h2_style = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontSize=15, leading=20, textColor=SNOWFLAKE_DARK,
    spaceBefore=14, spaceAfter=8
)
body_style = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontSize=10.5, leading=15, textColor=BLACK,
    spaceAfter=8, alignment=TA_JUSTIFY
)
bullet_style = ParagraphStyle(
    "Bullet", parent=body_style,
    leftIndent=20, bulletIndent=8
)
caption_style = ParagraphStyle(
    "Caption", parent=styles["Normal"],
    fontSize=9, leading=12, textColor=MEDIUM_GRAY,
    spaceAfter=4
)
code_style = ParagraphStyle(
    "Code", parent=styles["Normal"],
    fontName="Courier", fontSize=9, leading=12,
    textColor=HexColor("#2C3E50"), backColor=LIGHT_GRAY,
    leftIndent=12, rightIndent=12, spaceBefore=4, spaceAfter=8,
    borderWidth=0.5, borderColor=HexColor("#DDE1E6"), borderPadding=6
)
table_header_style = ParagraphStyle(
    "TableHeader", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=9.5, leading=13,
    textColor=WHITE
)
table_cell_style = ParagraphStyle(
    "TableCell", parent=styles["Normal"],
    fontSize=9.5, leading=13, textColor=BLACK
)


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_FILE, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch
    )
    story = []

    # ---- COVER / TITLE ----
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("DE Field Use Case<br/>Intelligence Hub", title_style))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="60%", thickness=2, color=SNOWFLAKE_BLUE, spaceAfter=12))
    story.append(Paragraph("Real-time visibility into AFE/PSS use cases, contacts, tech stack, product usage metrics, and opportunities", subtitle_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("User Guide, Architecture, and Deployment Reference", ParagraphStyle(
        "SubRef", parent=body_style, fontSize=11, alignment=TA_CENTER, textColor=MEDIUM_GRAY)))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Author: Subhajit Basu", ParagraphStyle(
        "Author", parent=body_style, fontSize=11, alignment=TA_CENTER, textColor=SNOWFLAKE_DARK)))
    story.append(Paragraph("Applied Field Engineering - Data Engineering", ParagraphStyle(
        "Team", parent=body_style, fontSize=10, alignment=TA_CENTER, textColor=MEDIUM_GRAY)))
    story.append(Spacer(1, 6))
    story.append(Paragraph("April 2026", ParagraphStyle(
        "Date", parent=body_style, fontSize=10, alignment=TA_CENTER, textColor=MEDIUM_GRAY)))
    story.append(PageBreak())

    # ---- TABLE OF CONTENTS ----
    story.append(Paragraph("Table of Contents", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=12))
    toc_items = [
        "1. What is this Dashboard?",
        "2. Key Features and Pages",
        "3. How to Use It",
        "4. Data Sources and Architecture",
        "5. The Five Core DE AFE/PSS Services",
        "6. Opportunity Detection Methodology",
        "7. Access Control and Identity",
        "8. GitHub Repository",
        "9. Deployment Details",
        "10. FAQ and Troubleshooting",
    ]
    for item in toc_items:
        story.append(Paragraph(item, ParagraphStyle(
            "TOC", parent=body_style, fontSize=11, leading=18, leftIndent=20)))
    story.append(PageBreak())

    # ---- SECTION 1: WHAT IS THIS DASHBOARD ----
    story.append(Paragraph("1. What is this Dashboard?", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=10))
    story.append(Paragraph(
        "The <b>DE Field Use Case Intelligence Hub</b> is a Streamlit-based analytics "
        "dashboard that provides real-time visibility into all active AFE (Applied Field Engineering) "
        "and PSS (Platform Specialist Solutions) use cases across the Snowflake field organization.", body_style))
    story.append(Paragraph(
        "It pulls data <b>live</b> from Snowflake's internal data warehouse (Snowhouse) - specifically "
        "the curated <b>MDM.MDM_INTERFACES.DIM_USE_CASE</b> table (87,000+ use cases, 169 columns) "
        "maintained by the MDM team. This means the data is always current with no ETL lag.", body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Who is it for?</b>", h2_style))
    items = [
        "Individual SEs - see your own use cases, contacts, tech stack, and product opportunities",
        "SE Managers - view your team's entire portfolio across all direct reports",
        "Directors and VPs - full regional/territory visibility with roll-up metrics",
        "AFE/PSS Specialists - identify product expansion and displacement opportunities",
    ]
    for item in items:
        story.append(Paragraph(u"\u2022  " + item, bullet_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Key Value Propositions:</b>", h2_style))
    values = [
        "Single pane of glass for all use case data - no more switching between SFDC tabs",
        "Live product telemetry from Snowhouse (Openflow, Iceberg, SSV2) showing real adoption",
        "AI-identified product opportunities with confidence scoring and signal-level detail",
        "Automatic identity-based access control - you only see what you should see",
        "Competitive intelligence: incumbent vendors, displacement opportunities, partner context",
    ]
    for v in values:
        story.append(Paragraph(u"\u2022  " + v, bullet_style))
    story.append(PageBreak())

    # ---- SECTION 2: KEY FEATURES AND PAGES ----
    story.append(Paragraph("2. Key Features and Pages", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=10))

    pages_data = [
        [Paragraph("<b>Page</b>", table_header_style),
         Paragraph("<b>Description</b>", table_header_style)],
        [Paragraph("Use Cases", table_cell_style),
         Paragraph("Lifecycle view of all use cases with status chevrons (Discovery through Closed-Won), "
                    "win/loss tracking, Gong meeting intel, product usage telemetry, and expansion recommendations.", table_cell_style)],
        [Paragraph("Tech Stack", table_cell_style),
         Paragraph("Per-customer technology landscape showing deployment model, product focus, "
                    "incumbent vendors, competitors, MEDDPICC pain points, and live telemetry from "
                    "Snowhouse (Openflow connectors, Iceberg tables, SSV2 channels).", table_cell_style)],
        [Paragraph("Contacts", table_cell_style),
         Paragraph("Full team roster per customer from SFDC team arrays - AEs, Lead SEs, "
                    "Workload FCTOs, Platform Specialists, and all other team members.", table_cell_style)],
        [Paragraph("Opportunities", table_cell_style),
         Paragraph("Cortex AI-powered product expansion opportunities across 5 core services. "
                    "Uses Snowflake Cortex LLM (llama3.1-70b) to analyze SFDC metadata and identify "
                    "opportunities with HIGH/MEDIUM/LOW confidence. Grouped by customer with signal-level detail.", table_cell_style)],
    ]
    t = Table(pages_data, colWidths=[1.5 * inch, 5.2 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SNOWFLAKE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#DDE1E6")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ---- SECTION 3: HOW TO USE IT ----
    story.append(Paragraph("3. How to Use It", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=10))

    story.append(Paragraph("<b>Step 1: Login and Identity</b>", h2_style))
    story.append(Paragraph(
        "When you open the dashboard, it automatically resolves your identity by matching your "
        "Snowhouse login (CURRENT_USER()) to your preferred full name in DIM_EMPLOYEE. "
        "Your role (SE, Manager, Director, VP) is detected automatically based on your SFDC assignments.", body_style))

    story.append(Paragraph("<b>Step 2: Choose a Filter</b>", h2_style))
    story.append(Paragraph(
        "The sidebar offers two filter modes:", body_style))
    items = [
        "<b>My Use Cases</b> - Shows only use cases where you are listed as a team member, "
        "Lead SE, or in the management chain (Manager/Director/VP).",
        "<b>My Region / Territory</b> - Shows all use cases in your assigned regions. "
        "A multi-select dropdown lets you pick specific regions.",
    ]
    for item in items:
        story.append(Paragraph(u"\u2022  " + item, bullet_style))

    story.append(Paragraph("<b>Step 3: Navigate Pages</b>", h2_style))
    story.append(Paragraph(
        "Use the left sidebar navigation to switch between Use Cases, Tech Stack, Contacts, "
        "and Opportunities. Each page respects the active filter.", body_style))

    story.append(Paragraph("<b>Step 4: Search and Sort</b>", h2_style))
    story.append(Paragraph(
        "Every page has a search bar and sort controls. Search works across all visible fields "
        "(customer name, product, role, rationale, etc.). Service-specific filters are available "
        "on Tech Stack and Opportunities pages.", body_style))

    story.append(Paragraph("<b>Step 5: Drill Down</b>", h2_style))
    story.append(Paragraph(
        "Click expanders or cards to see full detail per customer: use case descriptions, "
        "competitive context, MEDDPICC pain, product telemetry, opportunity signals, and "
        "direct SFDC links to open the use case in Salesforce.", body_style))
    story.append(PageBreak())

    # ---- SECTION 4: DATA SOURCES ----
    story.append(Paragraph("4. Data Sources and Architecture", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=10))

    story.append(Paragraph(
        "The Hub queries Snowhouse <b>live</b> - there is no ETL pipeline or staging database. "
        "All data is as fresh as the source systems.", body_style))

    ds_data = [
        [Paragraph("<b>Data Source</b>", table_header_style),
         Paragraph("<b>Table / System</b>", table_header_style),
         Paragraph("<b>What it Provides</b>", table_header_style)],
        [Paragraph("SFDC Use Cases", table_cell_style),
         Paragraph("MDM.MDM_INTERFACES.DIM_USE_CASE", table_cell_style),
         Paragraph("All use case metadata: account, stage, team, MEDDPICC, competitors, tech use case, workloads", table_cell_style)],
        [Paragraph("Employee Identity", table_cell_style),
         Paragraph("MDM.MDM_INTERFACES.DIM_EMPLOYEE", table_cell_style),
         Paragraph("Maps Snowhouse login to preferred name for access control", table_cell_style)],
        [Paragraph("Openflow Telemetry", table_cell_style),
         Paragraph("SNOWSCIENCE.OPENFLOW.OPENFLOW_CONNECTORS", table_cell_style),
         Paragraph("Active connectors, bytes sent, connector names per SFDC account", table_cell_style)],
        [Paragraph("Iceberg Telemetry", table_cell_style),
         Paragraph("SNOWSCIENCE.PRODUCT.ICEBERG_DAILY_ACCOUNT_AGG", table_cell_style),
         Paragraph("Active Iceberg tables, credits, storage bytes (latest day CTE to avoid inflation)", table_cell_style)],
        [Paragraph("SSV2 Telemetry", table_cell_style),
         Paragraph("SNOWSCIENCE.SNOWPIPE.SSV2_CHANNEL_METRICS", table_cell_style),
         Paragraph("Streaming channels, append bytes for Snowpipe Streaming", table_cell_style)],
        [Paragraph("Account Mapping", table_cell_style),
         Paragraph("SNOWSCIENCE.DIMENSIONS.DIM_ACCOUNTS_HISTORY", table_cell_style),
         Paragraph("Maps SFDC Account ID to Snowflake deployment + account ID (needed for Iceberg/SSV2)", table_cell_style)],
        [Paragraph("Gong Meetings", table_cell_style),
         Paragraph("FIVETRAN.SALESFORCE.GONG_GONG_CALL_C", table_cell_style),
         Paragraph("Recent call briefs, key points, and next steps (last 3 months)", table_cell_style)],
    ]
    t2 = Table(ds_data, colWidths=[1.3 * inch, 2.5 * inch, 2.9 * inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SNOWFLAKE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#DDE1E6")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
    ]))
    story.append(t2)
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Architecture:</b> Streamlit app -> snowflake.connector (Snowhouse connection) -> Live SQL queries. "
                           "Results cached with @st.cache_data (5-10 minute TTL). No intermediate database or ETL.", body_style))
    story.append(Paragraph("<b>Note:</b> Dynamic Tables and Snowpark telemetry are NOT yet available in Snowhouse. "
                           "The dashboard shows an info message for these two services.", caption_style))
    story.append(PageBreak())

    # ---- SECTION 5: FIVE CORE SERVICES ----
    story.append(Paragraph("5. The Five Core DE AFE/PSS Services", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=10))
    story.append(Paragraph(
        "The dashboard is organized around five core services that the AFE/PSS team focuses on:", body_style))

    svc_data = [
        [Paragraph("<b>Service</b>", table_header_style),
         Paragraph("<b>Description</b>", table_header_style),
         Paragraph("<b>Telemetry</b>", table_header_style)],
        [Paragraph("Openflow", table_cell_style),
         Paragraph("Data ingestion and replication - CDC, SaaS connectors, database replication", table_cell_style),
         Paragraph("Connectors, bytes sent, connector names", table_cell_style)],
        [Paragraph("SSV2 (Snowpipe Streaming)", table_cell_style),
         Paragraph("Real-time streaming ingestion via Kafka, Kinesis, custom clients", table_cell_style),
         Paragraph("Channel count, append bytes", table_cell_style)],
        [Paragraph("Iceberg / Open Data Lake", table_cell_style),
         Paragraph("Apache Iceberg tables, interoperable storage, lakehouse architecture", table_cell_style),
         Paragraph("Active tables, storage bytes", table_cell_style)],
        [Paragraph("Dynamic Tables", table_cell_style),
         Paragraph("Declarative data pipelines, continuous transformation, incremental processing", table_cell_style),
         Paragraph("Not yet available in Snowhouse", table_cell_style)],
        [Paragraph("Snowpark", table_cell_style),
         Paragraph("Python/Java/Scala compute, Spark migration (Snowpark Connect), UDFs", table_cell_style),
         Paragraph("Not yet available in Snowhouse", table_cell_style)],
    ]
    t3 = Table(svc_data, colWidths=[1.5 * inch, 3 * inch, 2.2 * inch])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SNOWFLAKE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#DDE1E6")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
    ]))
    story.append(t3)
    story.append(PageBreak())

    # ---- SECTION 6: OPPORTUNITY DETECTION ----
    story.append(Paragraph("6. Opportunity Detection Methodology", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=10))
    story.append(Paragraph(
        "The Opportunities page uses <b>Snowflake Cortex AI</b> (llama3.1-70b) to analyze each use case's "
        "SFDC metadata and identify product expansion opportunities. Unlike simple keyword matching, the LLM "
        "understands context, competitive dynamics, and technology patterns.", body_style))

    story.append(Paragraph("<b>How It Works:</b>", h2_style))
    steps = [
        "Each use case's SFDC fields are sent to Cortex COMPLETE (llama3.1-70b) via SQL",
        "The LLM analyzes Technical Use Case, Workloads, Description, Incumbent Vendor, and Competitors",
        "It returns structured JSON with product matches, confidence levels, rationale, and evidence signals",
        "Results are parsed and displayed grouped by customer with signal-level detail",
        "Responses are cached for 10 minutes to avoid repeated LLM calls",
    ]
    for s in steps:
        story.append(Paragraph(u"\u2022  " + s, bullet_style))

    story.append(Paragraph("<b>Fields Analyzed:</b>", h2_style))
    fields = ["TECHNICAL_USE_CASE", "WORKLOADS", "USE_CASE_DESCRIPTION", "INCUMBENT_VENDOR", "COMPETITORS",
              "ACCOUNT_INDUSTRY", "CLOUD_PROVIDER"]
    for f in fields:
        story.append(Paragraph(u"\u2022  " + f, bullet_style))

    story.append(Paragraph("<b>Confidence Levels:</b>", h2_style))
    conf_data = [
        [Paragraph("<b>Level</b>", table_header_style),
         Paragraph("<b>Criteria</b>", table_header_style),
         Paragraph("<b>Example</b>", table_header_style)],
        [Paragraph("HIGH", table_cell_style),
         Paragraph("Strong explicit signals — product mentioned or very direct match", table_cell_style),
         Paragraph("'CDC replication from Oracle' = HIGH for Openflow", table_cell_style)],
        [Paragraph("MEDIUM", table_cell_style),
         Paragraph("Related technology patterns inferred by LLM", table_cell_style),
         Paragraph("'Real-time data pipeline' = MEDIUM for SSV2", table_cell_style)],
        [Paragraph("LOW", table_cell_style),
         Paragraph("Indirect or inferred fit based on broader context", table_cell_style),
         Paragraph("'Data warehouse modernization' = LOW for Dynamic Tables", table_cell_style)],
    ]
    t4 = Table(conf_data, colWidths=[1 * inch, 2.7 * inch, 3 * inch])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SNOWFLAKE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#DDE1E6")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
    ]))
    story.append(t4)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Note:</b> A single use case can generate multiple opportunities across different products. "
        "Each opportunity includes LLM-generated rationale and specific evidence signals. "
        "The LLM also detects displacement opportunities when competing products are mentioned.", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Technical Detail:</b> The Cortex AI call is executed server-side via SQL using "
        "SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', ...) — no data leaves Snowflake. "
        "The system prompt instructs the LLM to return structured JSON with product, confidence, "
        "rationale, and signals for each identified opportunity.", body_style))
    story.append(PageBreak())

    # ---- SECTION 7: ACCESS CONTROL ----
    story.append(Paragraph("7. Access Control and Identity", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=10))
    story.append(Paragraph(
        "The dashboard implements automatic, identity-based access control:", body_style))

    ac_data = [
        [Paragraph("<b>Role</b>", table_header_style),
         Paragraph("<b>What You See</b>", table_header_style)],
        [Paragraph("Individual SE", table_cell_style),
         Paragraph("Use cases where you are listed in USE_CASE_TEAM_NAME_LIST", table_cell_style)],
        [Paragraph("Manager", table_cell_style),
         Paragraph("All use cases for your direct reports + your own team memberships", table_cell_style)],
        [Paragraph("Director", table_cell_style),
         Paragraph("All use cases under your directors + managers + personal team memberships", table_cell_style)],
        [Paragraph("VP / GVP / RVP", table_cell_style),
         Paragraph("Full cascading visibility across the entire hierarchy below you", table_cell_style)],
    ]
    t5 = Table(ac_data, colWidths=[1.5 * inch, 5.2 * inch])
    t5.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SNOWFLAKE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#DDE1E6")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
    ]))
    story.append(t5)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Identity is resolved via <b>CURRENT_USER()</b> matching to "
        "<b>MDM.MDM_INTERFACES.DIM_EMPLOYEE.SNOWHOUSE_LOGIN_NAME</b>, "
        "which returns the employee's PREFERRED_FULL_NAME. This name is then matched against "
        "SFDC team assignment fields (USE_CASE_TEAM_NAME_LIST, ACCOUNT_SE_MANAGER, "
        "ACCOUNT_SE_DIRECTOR, ACCOUNT_SE_VP, etc.).", body_style))
    story.append(PageBreak())

    # ---- SECTION 8: GITHUB ----
    story.append(Paragraph("8. GitHub Repository", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=10))

    story.append(Paragraph("<b>Repository:</b> sfc-gh-sbasu/afe-usecase-hub", body_style))
    story.append(Paragraph("<b>URL:</b> https://github.com/sfc-gh-sbasu/afe-usecase-hub", body_style))
    story.append(Paragraph("<b>Visibility:</b> Public (within Snowflake GitHub org)", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>File Structure:</b>", h2_style))
    file_data = [
        [Paragraph("<b>File</b>", table_header_style),
         Paragraph("<b>Purpose</b>", table_header_style)],
        [Paragraph("streamlit_app.py", table_cell_style),
         Paragraph("Main entry point - page config, Snowhouse connection, identity resolution, "
                    "role-based access control, sidebar filters", table_cell_style)],
        [Paragraph("app_pages/use_cases.py", table_cell_style),
         Paragraph("Use case lifecycle view with product usage, Gong intel, expansion recommendations", table_cell_style)],
        [Paragraph("app_pages/tech_stack.py", table_cell_style),
         Paragraph("Technology landscape with live telemetry, competitive context, MEDDPICC pain", table_cell_style)],
        [Paragraph("app_pages/contacts.py", table_cell_style),
         Paragraph("Team roster from SFDC team arrays (LATERAL FLATTEN)", table_cell_style)],
        [Paragraph("app_pages/opportunities.py", table_cell_style),
         Paragraph("AI-identified product opportunities with confidence scoring", table_cell_style)],
    ]
    t6 = Table(file_data, colWidths=[2.2 * inch, 4.5 * inch])
    t6.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SNOWFLAKE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#DDE1E6")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
    ]))
    story.append(t6)
    story.append(PageBreak())

    # ---- SECTION 9: DEPLOYMENT ----
    story.append(Paragraph("9. Deployment Details", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=10))

    story.append(Paragraph("<b>Current Deployment: Local</b>", h2_style))
    story.append(Paragraph(
        "The app runs locally for development and is deployed centrally on Snowhouse SiS:", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Local Development:</b>", h2_style))
    story.append(Paragraph(
        "SNOWHOUSE_CONNECTION_NAME=snowhouse streamlit run streamlit_app.py --server.port 8502", code_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Central Deployment: Streamlit in Snowflake (SiS)</b>", h2_style))
    story.append(Paragraph("<b>Location:</b> TEMP.SBASU.DE_FIELD_USE_CASE_INTELLIGENCE_HUB", body_style))
    story.append(Paragraph("<b>Account:</b> Snowhouse (SFCOGSOPS-SNOWHOUSE_AWS_US_WEST_2)", body_style))
    story.append(Paragraph("<b>Role:</b> SALES_ENGINEER", body_style))
    story.append(Paragraph("<b>Warehouse:</b> SE_AD_WH", body_style))
    story.append(Paragraph("<b>Runtime:</b> Native (non-container)", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Deploy command:</b>", body_style))
    story.append(Paragraph(
        "cd /Users/sbasu/afe-usecase-hub &amp;&amp; snow streamlit deploy --replace --connection snowhouse", code_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Dual-mode connection handling:</b>", body_style))
    items = [
        "<b>SiS mode:</b> Uses get_active_session() from snowflake.snowpark.context - no credentials needed",
        "<b>Local mode:</b> Falls back to snowflake.connector with Snowhouse connection name",
    ]
    for item in items:
        story.append(Paragraph(u"\u2022  " + item, bullet_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "The SiS app is accessible to all Snowflake employees with SALES_ENGINEER role on Snowhouse. "
        "Identity-based access control ensures users only see their own use cases.", body_style))
    story.append(PageBreak())

    # ---- SECTION 10: FAQ ----
    story.append(Paragraph("10. FAQ and Troubleshooting", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=10))

    faqs = [
        ("Q: I don't see my name in the Contacts page team list.",
         "A: This was a known issue caused by mismatched array lengths between USE_CASE_TEAM_NAME_LIST "
         "and USE_CASE_TEAM_ROLE_LIST in SFDC data. The fix uses LATERAL FLATTEN on names only, with "
         "index-based role lookup (COALESCE for missing roles). If you still don't appear, verify you are "
         "listed in the use case's team in SFDC."),
        ("Q: Why don't I see Dynamic Tables or Snowpark telemetry?",
         "A: These products do not yet have telemetry tables available in Snowhouse. The dashboard will "
         "show an info message for these. Once telemetry becomes available, the code can be extended."),
        ("Q: The dashboard says it could not resolve my identity.",
         "A: Your Snowhouse login must be mapped in MDM.MDM_INTERFACES.DIM_EMPLOYEE. "
         "Check that your SNOWHOUSE_LOGIN_NAME matches CURRENT_USER(). About 95% of employees are mapped."),
        ("Q: Data seems stale or cached.",
         "A: The dashboard uses @st.cache_data with 5-10 minute TTL. Refresh the browser or wait for the "
         "cache to expire. The underlying Snowhouse data is always live."),
        ("Q: How do I run this locally?",
         "A: Clone the repo, ensure you have a 'snowhouse' connection configured in ~/.snowflake/connections.toml, "
         "then run: SNOWHOUSE_CONNECTION_NAME=snowhouse streamlit run streamlit_app.py --server.port 8502"),
    ]
    for q, a in faqs:
        story.append(Paragraph(f"<b>{q}</b>", ParagraphStyle("FAQ_Q", parent=body_style, spaceBefore=10, spaceAfter=2)))
        story.append(Paragraph(a, body_style))

    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=1, color=SNOWFLAKE_BLUE, spaceAfter=8))
    story.append(Paragraph(
        "For questions or contributions, contact Subhajit Basu (subhajit.basu@snowflake.com) "
        "or open an issue on the GitHub repository.", caption_style))

    doc.build(story)
    print(f"PDF generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_pdf()
