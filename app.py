import streamlit as st
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from streamlit_calendar import calendar
from datetime import timedelta

from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


import os
import subprocess
import sys






os.environ['ANTHROPIC_API_KEY'] = st.secrets["ANTHROPIC_API_KEY"]


with open("turni_prompt.txt", encoding="latin-1") as file:
    final_prompt = file.read()

with open("extracted_info_from_prompt.txt", encoding="latin-1") as file:
    extracted_info_from_prompt = file.read()


st.title("🧹Gestione pulizie Angeli ")

st.write(extracted_info_from_prompt)

st.write("### Se vuoi cambiare qualcosa al calendario delle pulizie, descrivi in questo spazio le modifiche che vuoi fare. Cerca di essere specifico e preciso, facendo riferimento al programma iniziale descritto qui sopra.")

text_input = st.text_area('Scrivi qui le tue modifiche', height = 'content')



def rigenera_calendario(final_prompt):

    python_code_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a code generator. Output ONLY valid Python code with NO explanations, NO markdown formatting, NO code blocks. Just raw Python code. Shouldn't be wrapped in ```python``` "),
            ("human", "{input}"),
        ]
    )




    python_code_model = ChatAnthropic(model="claude-sonnet-4-5-20250929",    max_tokens=5000,
        thinking={"type": "enabled", "budget_tokens": 3000})

    chain = python_code_template | python_code_model

    py_code = chain.invoke({'input': final_prompt})

    my_code = py_code.content[1]['text']
    # print('my_code', my_code)

    with open("make_schedule.py", "w") as f:
        f.write(my_code)




def effettua_modifica_calendario(modifica_richiesta):

    # update python
    with open("make_schedule2.py", "r") as file:
        codice_python_per_csv = file.read()

    prompt_to_modify_python = f'''questo è il codice che era stato usato in precedenza per creare un file .csv con un calendario delle pulizie.
    {codice_python_per_csv}
    Il prompt che era stato assegnato per generare il file Python utilizzato per creare il .csv è questo
    {final_prompt}
    Ora è stato richiesta questa modifica al file.
    {modifica_richiesta}'''
    python_code_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a code generator. Output ONLY valid Python code with NO explanations, NO markdown formatting, NO code blocks. Just raw Python code. Shouldn't be wrapped in ```python``` "),
            ("human", "{input}"),
        ]
    )
    python_code_model = ChatAnthropic(model="claude-sonnet-4-5-20250929",    max_tokens=5000,
        thinking={"type": "enabled", "budget_tokens": 3000})
    chain = python_code_template | python_code_model
    py_code = chain.invoke({'input': prompt_to_modify_python})
    my_code = py_code.content[1]['text']
    # print('my_code', my_code)
    with open("make_schedule2.py", "w", encoding='utf-8') as f:
        f.write(my_code)

    # update prompt
    prompt_to_update_prompt =     f'''Questo è un prompt che era stato usato per generare un file Python per creare un .csv. 
    {final_prompt}
    Sono state richieste queste modifiche.
    {modifica_richiesta}
    Restituisci il prompt iniziale che includa le modifiche richieste. Questo prompt aggiornato verrà poi usato per creare il .csv'''
    python_code_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a good at rewriting prompts that will be sent to an LLM to generate Python code"),
            ("human", "{input}"),
        ]
    )

    rewrite_prompt_model = ChatAnthropic(model="claude-sonnet-4-5-20250929",    max_tokens=4000)
    chain = python_code_template | rewrite_prompt_model
    new_prompt = chain.invoke({'input': prompt_to_update_prompt})

    try:
        new_prompt = new_prompt.content
    except:
        pass

    # print('my_code', new_prompt)

    with open("turni_prompt.txt", "w", encoding="latin-1") as file:
        file.write(str(new_prompt))


    # crea un nuovo prompt più leggibile

    prompt_to_extract_info_from_prompt =     f'''Riscrivi il prompt tale e quale però togli ogni riferimento a Python o .csv. Inoltre, invece di spiegare come se fosse un'istruzione, indica come se fosse una desrizione di cosa fa il programma. Eg invece di 'Devi creare i turni della scuola',indica 'Questo programma crea i turni della scuola'. Ecco il prompt {new_prompt}'''
    prompt_to_extract_info_from_prompt_template = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
        ]
    )

    prompt_to_extract_info_from_prompt_model = ChatAnthropic(model="claude-sonnet-4-5-20250929",    max_tokens=4000)
    chain = prompt_to_extract_info_from_prompt_template | prompt_to_extract_info_from_prompt_model
    extracted_info = chain.invoke({'input': prompt_to_extract_info_from_prompt})

    try:
        extracted_info = extracted_info.content
    except:
        pass

    # print('extracted_info', extracted_info)

    with open("extracted_info_from_prompt.txt", "w", encoding="latin-1") as file:
        file.write(str(extracted_info))



# if st.button("Ricrea calendario"):
#     rigenera_calendario(text_input)


if st.button("Modifica calendario"):
    effettua_modifica_calendario(text_input)
    # result = subprocess.run(["python", "make_schedule2.py"], capture_output=True, text=True)
    subprocess.run([f"{sys.executable}", "make_schedule2.py"])

    


# if st.button("Ricrea dataset"):
#     result = subprocess.run(["python", "make_schedule.py"], capture_output=True, text=True)
#     print(result.stdout)

# if st.button("Esegui le modifiche"):
#     result = subprocess.run(["python", "make_schedule2.py"], capture_output=True, text=True)
#     print(result.stdout)


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




# --- Display pivot table ---
st.title("📅 Ecco il calendario creato")
pivot = create_pivot_table(expanded_df)












# Display in Streamlit
st.dataframe(pivot)








# --- Calculate and display domeniche ---
st.title("🗓️ Turni domeniche")
domeniche = calculate_domeniche(expanded_df)
st.dataframe(domeniche)


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