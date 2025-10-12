import streamlit as st
import pandas as pd
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_anthropic import ChatAnthropic


import os
import subprocess

os.environ['ANTHROPIC_API_KEY'] = st.secrets["ANTHROPIC_API_KEY"]


with open("turni_prompt.txt", encoding="utf-8") as file:
    final_prompt = file.read()

with open("extracted_info_from_prompt.txt") as file:
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
    print('my_code', my_code)

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
    print('my_code', my_code)
    with open("make_schedule2.py", "w") as f:
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

    print('my_code', new_prompt)

    with open("turni_prompt.txt", "w") as file:
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

    print('extracted_info', extracted_info)

    with open("extracted_info_from_prompt.txt", "w") as file:
        file.write(str(extracted_info))






# if st.button("Ricrea calendario"):
#     rigenera_calendario(text_input)


if st.button("Modifica calendario"):
    effettua_modifica_calendario(text_input)
    result = subprocess.run(["python", "make_schedule2.py"], capture_output=True, text=True)

    


# if st.button("Ricrea dataset"):
#     result = subprocess.run(["python", "make_schedule.py"], capture_output=True, text=True)
#     print(result.stdout)

# if st.button("Esegui le modifiche"):
#     result = subprocess.run(["python", "make_schedule2.py"], capture_output=True, text=True)
#     print(result.stdout)



df = pd.read_csv("turni.csv")

df['data_inizio'] = df['periodo'].map(lambda x: datetime.strptime(x.split("-")[0], "%d/%m/%Y"))
df = df.sort_values(by="data_inizio", ascending=True)

st.title("📅 Ecco il calendario creato")
st.dataframe(df)
