import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Use caching to avoid re-reading and processing data on every rerun
@st.cache_data
def load_and_process_data():
    """Load CSV and perform all data processing once"""
    df = pd.read_csv("turni.csv")
    
    # --- Expand date ranges (vectorized approach) ---
    expanded_rows = []
    for _, row in df.iterrows():
        periodo = row["periodo"]
        if "-" in periodo:
            start, end = periodo.split("-")
            dates = pd.date_range(
                pd.to_datetime(start, dayfirst=True),
                pd.to_datetime(end, dayfirst=True)
            )
        else:
            dates = [pd.to_datetime(periodo, dayfirst=True)]
        
        for date in dates:
            expanded_rows.append({
                "collaboratore": row["collaboratore"],
                "reparto": row["reparto"],
                "data": date,
                "turno": row["turno"]
            })
    
    expanded_df = pd.DataFrame(expanded_rows)
    
    # --- Add weekday info ---
    expanded_df["weekday"] = expanded_df["data"].dt.day_name()
    
    # --- Determine usual reparto ---
    usual_reparto = (
        expanded_df.groupby("collaboratore")["reparto"]
        .agg(lambda x: x.mode()[0] if not x.mode().empty else None)
    )
    
    # --- Fill Sunday reparto if missing ---
    is_sunday = expanded_df["weekday"] == "Sunday"
    expanded_df.loc[is_sunday & expanded_df["reparto"].isna(), "reparto"] = \
        expanded_df.loc[is_sunday, "collaboratore"].map(usual_reparto)
    
    return df, expanded_df, usual_reparto

@st.cache_data
def calculate_domeniche(expanded_df):
    """Calculate Sunday shifts count"""
    sundays = expanded_df[expanded_df["weekday"] == "Sunday"]
    domeniche = (
        sundays.groupby(["collaboratore", "reparto", "turno"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["mattina", "pomeriggio", "sera"], fill_value=0)
    )
    return domeniche

@st.cache_data
def create_pivot_table(expanded_df):
    """Create pivot table for calendar view"""
    pivot = expanded_df.pivot_table(
        index=["collaboratore", "reparto"],
        columns="data",
        values="turno",
        aggfunc="first"
    )
    
    full_range = pd.date_range(expanded_df["data"].min(), expanded_df["data"].max())
    pivot = pivot.reindex(columns=full_range, fill_value=None)
    pivot.columns = [d.strftime("%d/%m/%Y") for d in pivot.columns]
    
    return pivot

# --- Load data once ---
df, expanded_df, usual_reparto = load_and_process_data()

# --- Display original data ---
st.dataframe(df)

# --- Calculate and display domeniche ---
domeniche = calculate_domeniche(expanded_df)
st.dataframe(domeniche)

# --- Display pivot table ---
st.title("📅 Ecco il calendario creato")
pivot = create_pivot_table(expanded_df)
st.dataframe(pivot)

# --- Collaborator selection section ---
st.title("Turni Collaboratori")

collaboratori = sorted(expanded_df["collaboratore"].unique())
selected = st.selectbox("Seleziona collaboratore", collaboratori)

if st.button("Conferma"):
    # Filter data for selected collaborator
    filtered = expanded_df[expanded_df["collaboratore"] == selected].copy()
    
    st.write(f"### Turni per {selected}")
    st.dataframe(filtered)
    
    # --- Excel download ---
    @st.cache_data
    def to_excel(df_filtered, collaborator_name):
        """Generate Excel file"""
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_filtered.to_excel(writer, index=False)
        return output.getvalue()
    
    excel_data = to_excel(filtered, selected)
    st.download_button(
        label="📥 Scarica Excel",
        data=excel_data,
        file_name=f"{selected}_turni.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # --- PDF download ---
    @st.cache_data
    def to_pdf(df_filtered, collaborator_name):
        """Generate PDF file"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = [Paragraph(f"Turni di {collaborator_name}", styles["Heading1"])]
        
        data = [df_filtered.columns.tolist()] + df_filtered.astype(str).values.tolist()
        table = Table(data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        elements.append(table)
        doc.build(elements)
        return buffer.getvalue()
    
    pdf_data = to_pdf(filtered, selected)
    st.download_button(
        label="📄 Scarica PDF",
        data=pdf_data,
        file_name=f"{selected}_turni.pdf",
        mime="application/pdf"
    )



    