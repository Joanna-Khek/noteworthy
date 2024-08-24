from pathlib import Path

import nbformat
import pandas as pd
import re
from loguru import logger


class DataExtractor:

    def __init__(
        self, data_path: Path = Path("data/raw")  # folder containing all the raw files
    ):

        self.data_path = data_path

    def _get_branch_names(self, path: str = r"config/gitlab_branches.csv") -> list:
        """reading in a .csv file containing apprentices' names and branch names
        and returning list of branch names

        Args:
            path (str): path to .csv file containing apprentices and branch names
                default: data/raw/gitlab_branches.csv"
        Returns:
            list: list containing the branch names.
        """

        df = pd.read_csv(path)
        branch_list = df["Gitlab_Branch"].tolist()

        return branch_list

    def _get_notebook_questions(
        self, path: str = r"config/questions_data.csv", notebook_name: str = ""
    ) -> list:
        """reading in a .csv file containing list of questions
        (categorized by assignment and notebook)
        and returning list of questions for the specified notebook

        Args:
            path (str): path to .csv file containing questions
                default: data/raw/questions_data.csv",
            notebook_name (str): name of notebook, including ".ipynb" extension
                default: ""
        Returns:
            pd.DataFrame: contains all questions with their
                corresponding assignments and notebooks
        """

        df = pd.read_csv(path)
        list_of_questions = df.query(
            f"Notebook_Name == '{notebook_name}'"
        ).Questions.to_list()

        return list_of_questions

    def _read_notebook(
        self, branch_name: str = "", assignment_name: str = "", notebook_name: str = ""
    ) -> nbformat.NotebookNode:
        """Reads in .ipynb using nbformat library

        Args:
            data_path (str):
            branch_name (str): name of branch, usually apprentices' name separated by underscores.
            assignment_name (str): name of assignment; assumes format is "assignment{n}",
                with "n" being assignment number.
            notebook_name (str): name of notebook, including .ipynb extension

        Returns:
            notebook (nbformat.NotebookNode): contents of .ipynb notebook
        """

        with open(
            Path(
                self.data_path,
                branch_name,
                assignment_name,
                notebook_name,
            ),
            "r",
            encoding="utf-8",
        ) as file:
            notebook = nbformat.read(file, as_version=2)
        return notebook

    def _extract_code_markdown_cells(self, notebook: nbformat.NotebookNode) -> list:
        """Extract cell type that are 'code' or 'markdown'
        If its 'code' cell type, then extract the 'input' from json as content
        If its 'markdown' cell type, then extract the 'source' from json as content

            Args:
                notebook (nbformat.NotebookNode): .ipynb notebook in json format
            Returns:
                list: list of code and markdown cells
        """

        self.code_and_markdown_cells = [
            {
                "index": i,
                "cell_type": cell["cell_type"],
                "content": (
                    cell.get("input", "")
                    if cell["cell_type"] == "code"
                    else cell.get("source", "")
                ),
            }
            for worksheet in notebook["worksheets"]
            for i, cell in enumerate(worksheet["cells"])
            if cell["cell_type"] in ["code", "markdown"]
        ]
        return self.code_and_markdown_cells

    def _get_relevant_start_cell_index(
        self, list_of_questions: list, notebook: nbformat.NotebookNode
    ) -> tuple:
        """Search through the code and markdown cells to extract
        the start index of a question
        i.e : Locate the index where the question is found so that we know
        which markdowns/codes are relevant to which question

            Args:
                list_of_questions (list): list of questions in a particular
                    notebook
                notebook (nbformat.NotebookNode): .ipynb notebook in json format

            Returns:
                (start_qns_idx, end_qns_idx): lists of start and end question indices
        """
        code_and_markdown_cells = self._extract_code_markdown_cells(notebook)

        # Start index of question
        start_qns_idx = []
        for question in list_of_questions:
            len_cells = len(code_and_markdown_cells)
            for idx, doc in enumerate(code_and_markdown_cells):
                sanitized_question = question.replace("*", "").replace("`", "")
                # sanitized_question = re.sub(r'\b_([^_]+)_\b', r'\1', sanitized_question)
                sanitized_doc_content = doc["content"].replace("*", "").replace("`", "")
                sanitized_doc_content = re.sub(
                    r"\b_([^_]+)_\b", r"\1", sanitized_doc_content
                )
                short_qn = " ".join(
                    sanitized_question.split(
                        " ",
                    )[0:4]
                )  # get the 1st 4 words of the question
                if short_qn in sanitized_doc_content:
                    start_qns_idx.append(idx)
                    break
                if idx == len_cells - 1 and len(start_qns_idx) != 0:
                    start_qns_idx.append(start_qns_idx[-1])

        # End index of question (use the start index of the next question)
        end_qns_idx = start_qns_idx[1:]
        end_qns_idx.append(len(code_and_markdown_cells))

        return start_qns_idx, end_qns_idx

    def _split_into_code_markdown_content(self, df_question: pd.DataFrame):
        """querying the content column for the type of cell, and
        splitting the response for a question (for a particular apprentice's
        notebook) into code & markdown content

        Args:
            df_question (pd.DataFrame): a particular apprentice's response to
              a question in the notebook

        Returns:
            markdown_content, codes_content: markdown & code response for a
                particular apprentice's response to a particular question.
        """
        markdown_content = ". ".join(
            df_question.query("cell_type == 'markdown'").cell_content
        )
        codes_content = " ".join(df_question.query("cell_type == 'code'").cell_content)
        return markdown_content, codes_content

    def _extract_content_for_each_question(
        self,
        list_of_questions: list,
        assignment_name: str,
        notebook_name: str,
        branch_name: str,
        notebook: nbformat.NotebookNode,
    ):
        """Using the extracted json for the entire notebook, we filtered to
        get only cell type that are 'code' or 'markdown'. We then located the starting
        index and end index of the json for each question. Using the start and end index,
        we can now extract the relevant content for each question.

        Args:
            list_of_questions (list): list of questions from the notebook to extract responses
                from
            assignment_name (str): name of assignment, assumed to be in format of "assignment{n}",
                where "n" is the assignment number.
            notebook_name (str): name of notebook, including ".ipynb" extension
            branch_name (str): name of branch, usually apprentices' name separated by underscores.
            notebook (nbformat.NotebookNode): notebook in json format
        """
        # Identify the start and end index of each question
        start_qns_idx, end_qns_idx = self._get_relevant_start_cell_index(
            list_of_questions, notebook=notebook
        )

        # Empty lists to store contents
        all_questions_markdown = []
        all_questions_codes = []

        # For each question, take the start and end index to extract information
        for start_idx, end_idx in zip(start_qns_idx, end_qns_idx):

            question_cell_type = []
            question_content = []

            # For each relevant index of the same question, extract the cell type
            # (markdown/code) and the content of the cell
            for idx in range(start_idx + 1, end_idx):
                question_cell_type.append(
                    self.code_and_markdown_cells[idx]["cell_type"]
                )
                question_content.append(self.code_and_markdown_cells[idx]["content"])

                # For each question's content, split into into code and markdowns
                df_question = pd.DataFrame(
                    {"cell_type": question_cell_type, "cell_content": question_content}
                )

                markdown_content, codes_content = (
                    self._split_into_code_markdown_content(df_question)
                )

            all_questions_markdown.append(markdown_content)
            all_questions_codes.append(codes_content)

        logger.debug(f"notebook_name: {notebook_name}")
        logger.debug(f"questions.length: {len(list_of_questions)}")
        logger.debug(f"all_questions_markdown.length: {len(all_questions_markdown)}")
        logger.debug(f"all_questions_codes.length: {len(all_questions_codes)}")

        # Concatenate all questions markdown and codes into a dataframe
        extracted_content = pd.DataFrame(
            {
                "Assignment_Name": assignment_name,
                "Notebook_name": notebook_name,
                "Source": branch_name,
                "Question": list_of_questions,
                "Markdown_Content": all_questions_markdown,
                "Codes_Content": all_questions_codes,
            }
        )


        return extracted_content

    def extract_content(
        self, assignment_names: list = [], save_to_folder_path: str = r"data/processed"
    ):
        """takes in a list of assignments to extract content from,
        and returns the content of each response from each apprentice's notebook
            - assumes that all notebooks in assignment folders are assignment-related
            (apprentice did not create own notebook)

            Args:
                assignment_names (list, optional): list of assignment names, with format
                    "assignment{n}", with "n" being the assignment no. Defaults to [].
                save_to_folder_path (str, optional): folder path to save the processed
                    content to. Defaults to r"data/processed".

            Returns:
                df_content (pd.DataFrame): content of all notebooks across all apprentices
                    for all assignments provided in the user-specified list.
                    assumes that column names of output are:
                    Assignment_Name, Notebook_name, Source (branch_name), Question, Markdown_Content, Codes_Content
        """
        try:
            list_of_contents = []
            branch_names = self._get_branch_names()
            available_branch_names = [
                f.name for f in self.data_path.iterdir() if f.is_dir()
            ]
            logger.debug(f"available_branch_names: {available_branch_names}")

            for branch_name in branch_names:
                if branch_name in available_branch_names:
                    available_assignment_names = [
                        f.name
                        for f in self.data_path.joinpath(branch_name).iterdir()
                        if f.is_dir()
                    ]
                    logger.debug(f"available_assignment_names: {available_assignment_names}")
                    logger.debug(f"assignment_names: {assignment_names}")

                    for assignment_name in assignment_names:
                        if assignment_name in available_assignment_names:
                            available_notebook_names = [
                                f.name
                                for f in self.data_path.joinpath(branch_name)
                                .joinpath(assignment_name)
                                .iterdir()
                                if f.is_file()
                                and str(f.name).lower().endswith(".ipynb")
                            ]
                            logger.debug(available_notebook_names)

                            for notebook_name in available_notebook_names:
                                logger.debug(f"branch_name: {branch_name}")
                                logger.debug(f"assignment_name: {assignment_name}")
                                logger.debug(f"notebook_name: {notebook_name}")

                                notebook = self._read_notebook(
                                    branch_name=branch_name,
                                    assignment_name=assignment_name,
                                    notebook_name=notebook_name,
                                )

                                questions = self._get_notebook_questions(
                                    notebook_name=notebook_name
                                )

                                content = self._extract_content_for_each_question(
                                    list_of_questions=questions,
                                    assignment_name=assignment_name,
                                    notebook_name=notebook_name,
                                    branch_name=branch_name,
                                    notebook=notebook,
                                )

                                logger.debug(f"content: {content}")

                                list_of_contents.append(content)

            df_content = pd.concat(list_of_contents, ignore_index=True).assign(
                Markdown_Content=lambda df_: "Name of apprentice: "
                + df_.Source
                + ".\n\n"
                + df_.Markdown_Content,
                Codes_Content=lambda df_: "Name of apprentice: "
                + df_.Source
                + ".\n\n"
                + df_.Codes_Content,
            )

            self.df_content = df_content
            self._save_to_csv(self.df_content, save_to_folder_path)
            return self.df_content

        except Exception as e:
            logger.error(f"An error occured while extracting content: Exception: {e}")

    def _save_to_csv(self, df: pd.DataFrame, folder_path: str) -> None:
        """takes in a dataframe containing the contents of each apprentice's notebook
          for the user-specified list of assignments. splits content up by "Assignment_Name"
          column. saves each "assignment_name"'s content under a file named "input_llm.csv",
          under each assignment{n} folder, where n = assignment number.

        Args:
            df (pd.DataFrame): contains the contents of each apprentice's notebook
          for the user-specified list of assignments
            folder_path (str): folder path to save .csv files to in string
        """

        if df is None and self.df_content is not None:
            df = self.df_content

        for assignment_name, group in df.groupby("Assignment_Name"):
            logger.info(f"Saving {assignment_name} to {Path(folder_path) / assignment_name}")
            Path(Path(folder_path) / assignment_name).mkdir(parents=True, exist_ok=True)
            group.to_csv(
                Path(folder_path) / assignment_name / "input_llm.csv", index=False
            )
