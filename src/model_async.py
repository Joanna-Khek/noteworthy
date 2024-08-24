import os
import pandas as pd
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import asyncio
from concurrent.futures import ThreadPoolExecutor


class Model:
    def __init__(
        self,
        model_name,
        azure_endpoint,
        openai_api_key,
        openai_api_version,
        temperature,
        max_tokens,
        top_p,
    ):
        self.llm = AzureChatOpenAI(
            model_name=model_name,
            azure_endpoint=azure_endpoint,
            openai_api_key=openai_api_key,
            openai_api_version=openai_api_version,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )

        # Prompt template for the code summarization task
        self.code_template = """You are a helpful assistant for question-answering tasks related to AI Singapore's Apprenticeship programme.
        The AI Apprenticeship Programme (AIAP)® was created to meet AI Singapore’s requirements for AI professionals. 
        It grew out of a need for a core group of Singaporean AI talents working in AI Singapore, solving both Singapore’s 
        and Singapore companies’ problem statements with AI.


        I will provide you with a question given to apprentices, along with their code responses. 
        Your task is to summarize common approaches taken by the apprentices and highlight some exemplary solutions.

        Please format your response as follows:

        1. **Question**: {query}

        2. **Summary of Common Approaches**:
        - Describe the general strategies and methods most apprentices are using in their code answers.
        - Highlight any recurring themes, techniques, or patterns observed in the responses.

        3. **Examples of Noteworthy Solutions**:
        - Pick out a few standout examples from the apprentices' code answers. Identify the name of the apprentice.
        - Provide brief descriptions of why these examples are particularly good or insightful.
        - Ensure that the selected examples illustrate diverse approaches or noteworthy practices.

        Here are the details:

        **Question**: {query}

        **Apprentices' Code Answers**: {code_answers}

        Please ensure your response is clear and concise, and focus on providing actionable insights from the apprentices' submissions.

        """

        # Prompt template for the markdown summarization task
        self.markdown_template = """You are a helpful assistant for question-answering tasks related to AI Singapore's Apprenticeship programme.
        The AI Apprenticeship Programme (AIAP)® was created to meet AI Singapore’s requirements for AI professionals. 
        It grew out of a need for a core group of Singaporean AI talents working in AI Singapore, solving both Singapore’s 
        and Singapore companies’ problem statements with AI.


        I will provide you with a question given to apprentices, along with their markdown responses. 
        Your task is to summarize common approaches taken by the apprentices and highlight some exemplary solutions.

        Please format your response as follows:

        1. **Question**: {query}

        2. **Summary of Common Approaches**:
        - Describe the general strategies and methods most apprentices are using in their answers.
        - Highlight any recurring themes, techniques, or patterns observed in the responses.

        3. **Examples of Noteworthy Solutions**:
        - Pick out a few standout examples from the apprentices' code answers. Identify the name of the apprentice.
        - Provide brief descriptions of why these examples are particularly good or insightful.
        - Ensure that the selected examples illustrate diverse approaches or noteworthy practices.

        Here are the details:

        **Question**: {query}

        **Apprentices' Markdown Responses**: {markdown_responses}

        Please ensure your response is clear and concise, and focus on providing actionable insights from the apprentices' submissions.

        """

    # def _extract_answer(
    #     self, df_content: pd.DataFrame, prompt_type: str, question: str
    # ) -> str:
    #     if prompt_type not in ["codes", "markdown"]:
    #         raise ValueError(
    #             "Prompt type must be either 'codes' or 'markdown'. Got: {prompt_type}"
    #         )
    #     query = f"""Question == "{question}" """
    #     full_content = (
    #         f"\n\n======NEXT APPRENTICE {prompt_type.upper()} RESPONSE======\n\n".join(
    #             df_content.query(query)[f"{prompt_type.capitalize()}_Content"]
    #         )
    #     )
    #     return full_content

    def _extract_answer(
        self, df_content: pd.DataFrame, prompt_type: str, question: str
    ) -> str:
        if prompt_type not in ["codes", "markdown"]:
            raise ValueError(
                f"Prompt type must be either 'codes' or 'markdown'. Got: {prompt_type}"
            )
        
        # Filter rows where the Question column matches the question string
        filtered_content = df_content[df_content['Question'].apply(lambda x: x == question)]
        
        # Concatenate the filtered content
        full_content = (
            f"\n\n======NEXT APPRENTICE {prompt_type.upper()} RESPONSE======\n\n".join(
                filtered_content[f"{prompt_type.capitalize()}_Content"]
            )
        )
        return full_content

    def _format_prompt(self, query):
        if self.prompt_type == "codes":
            code_answers = self._extract_answer(
                self.df_content, self.prompt_type, query
            )
            formatted_prompt = self.prompt.format(
                query=query, code_answers=code_answers
            )
        elif self.prompt_type == "markdown":
            markdown_responses = self._extract_answer(
                self.df_content, self.prompt_type, query
            )
            formatted_prompt = self.prompt.format(
                query=query, markdown_responses=markdown_responses
            )
        return formatted_prompt

    async def run_invoke(self, df_content, question, prompt_type):
        self.df_content = df_content
        self.prompt_type = prompt_type
        if prompt_type == "codes":
            self.prompt = PromptTemplate(
                input_variables=["query", "codes_answers"], template=self.code_template
            )
            chain = (
                {
                    "query": RunnablePassthrough(),
                    "code_answers": self._format_prompt,
                }
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
        elif prompt_type == "markdown":
            self.prompt = PromptTemplate(
                input_variables=["query", "markdown_responses"],
                template=self.markdown_template,
            )
            chain = (
                {
                    "query": RunnablePassthrough(),
                    "markdown_responses": self._format_prompt,
                }
                | self.prompt
                | self.llm
                | StrOutputParser()
            )

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, chain.invoke, question)
        return result
