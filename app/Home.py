import streamlit as st

st.set_page_config(
    initial_sidebar_state="collapsed",
    layout="centered",
)
st.image("app/assets/aisg_logo.png", use_column_width="auto")
st.divider()

st.markdown(f"<h1 style='text-align: center;'>NoteWorthy</h1>", unsafe_allow_html=True)
st.markdown(
    f"<h3 style='text-align: center;'>Elevate Your Learning Experience with Notebook Insights</h3>",
    unsafe_allow_html=True,
)

with st.expander(label="About NoteWorthy", expanded=True):
    st.write(
        """
        In the journey of learning and development at AIAP, individual feedback is crucial, 
        yet often scarce and intimidating to seek. What if you could gain valuable insights 
        by learning from the work of your peers, without the inefficiencies of manual
        notebooks review? 
        
        Unlock the full potential of collaborative learning with NoteWorthy, 
        a tool designed specifically for AIAP apprentices. 
        NoteWorthy simplifies the process of gaining insights from peer notebooks, 
        making it an essential companion for any apprentice eager to enhance their 
        skills and knowledge.
        """
    )
with st.expander(label="How it works", expanded=True):
    st.write(
        """
    **Organised Aggregation:** NoteWorthy collects and organises all markdown and code 
    responses from apprentices, efficiently compiling the data for each question 
    in their notebooks.
    
    **Intelligent Summarisation:** Leveraging advanced Large Language Models (LLMs),
    NoteWorthy summarises the compiled markdown and code responses. 
    This ensures you receive concise and actionable feedback, highlighting key
    insights and areas for improvement.

    **Enhanced Learning Experience:** By reviewing summarised responses and exemplary
    code from your peers, you can easily identify best practices, understand diverse
    approaches, and enhance your own notebooks.
    """
    )

col1, col2, col3 = st.columns(3)

with col1:
    pass
with col2:
    st.page_link(
        "pages/1_Insights.py", label="**Click here to start learning!**", icon="🥳"
    )
with col3:
    pass
