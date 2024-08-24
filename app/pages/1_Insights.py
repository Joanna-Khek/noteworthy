import streamlit as st
import pandas as pd
from app.src import utils

st.set_page_config(
    initial_sidebar_state="collapsed",
    layout="wide",
)
data = pd.read_csv("config/questions_data.csv")

st.page_link("Home.py", label="**Home**", icon="🏠")
with st.expander(label="Instructions", expanded=True):
    st.write(
        """
            Select the assignment, notebook and sections you would like to summarise.
            The LLM will summarise the responses and the codes of all apprentices 
            for that section.
        """
    )
st.subheader("Configurations")

# Assignment Option
assignment_option = st.selectbox(label="Assignment", options=data.Assignment.unique())
filtered_notebook = data.query(f"Assignment == @assignment_option")

# Notebook Option
notebook_option = st.selectbox(
    label="Notebook", options=filtered_notebook.Notebook_Name.unique()
)
filtered_sections = data.query(f"Notebook_Name == @notebook_option")

# Section Option
section_option = st.selectbox(
    label="Section", options=filtered_sections.Questions.unique()
)


if st.button("Get Output!"):
    markdown_response, code_response = utils.get_llm_output(
        assignment_option, notebook_option, section_option
    )
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Markdown Response")
        container = st.container(border=True)
        container.write(markdown_response)

    with col2:
        st.subheader("Code Response")
        container = st.container(border=True)
        container.write(code_response)
