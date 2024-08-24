import pandas as pd


def get_llm_output(assignment_option: str, notebook_option: str, section_option: str):
    """Filter the LLM output csv to extract markdown response
    and code response.

    Args:
        assignment_option (str): name of assignment according to output.csv
        notebook_option (str): name of notebook according to output.csv
        section_option (str): name of section according to output.csv
    """
    # Clean the assignment option to match the processed folder name
    clean_assignment_option = assignment_option.replace("_", "").lower()

    # Read the from processed folder
    df_llm = pd.read_csv(f"data/processed/{clean_assignment_option}/output.csv")

    # Filter relevant section
    result = df_llm.query(
        f""" Notebook_name == "{notebook_option}" and Question == "{section_option}" """
    )

    # Output
    if len(result) != 0:
        markdown_response = result.LLM_Markdown_Output.item()
        code_response = result.LLM_Code_Output.item()
    else:
        markdown_response = ""
        code_response = ""

    return markdown_response, code_response
