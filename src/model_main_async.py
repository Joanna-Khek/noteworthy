import asyncio
import pandas as pd
import settings
import openai
from loguru import logger


async def process_question(llm, input_df, question, semaphore):
    async with semaphore:
        try:
            code_output = await llm.run_invoke(input_df, question, prompt_type="codes")
            logger.debug(f"Code output for {question}: {code_output}")
            markdown_output = await llm.run_invoke(
                input_df, question, prompt_type="markdown"
            )
            logger.debug(f"Markdown output for {question}: {markdown_output}")
            return {
                "Question": question,
                "LLM_Code_Output": code_output,  # Extract the single result from the list
                "LLM_Markdown_Output": markdown_output,  # Extract the single result from the list
            }
        except openai.error.RateLimitError:
            logger.error(
                f"Rate limit exceeded for question '{question}'. Retrying after delay..."
            )
            await asyncio.sleep(60)  # Wait for 60 seconds before retrying
            return await process_question(llm, input_df, question, semaphore)
        except Exception as e:
            logger.error(f"Error processing question {question}: {e}")
            return None


async def process_batch(llm, input_df, questions, semaphore):
    tasks = [
        process_question(llm, input_df, question, semaphore) for question in questions
    ]
    results = await asyncio.gather(*tasks)
    return [result for result in results if result is not None]


async def async_main(questions_df, llm, input_df, batch_size, delay):
    output_rows = []
    tasks = []

    rows = questions_df.shape[0]
    semaphore = asyncio.Semaphore(5)  # Define the maximum number of concurrent tasks

    for i in range(0, rows, batch_size):
        batch_questions = [
            r"{}".format(questions_df.iloc[j]["Questions"])
            for j in range(i, min(i + batch_size, rows))
        ]
        logger.info(f"Processing batch starting at question {i}")
        logger.debug(batch_questions)

        tasks.append(process_batch(llm, input_df, batch_questions, semaphore))

        # Wait for the current batch to complete before starting the next one
        batch_results = await asyncio.gather(*tasks)
        logger.debug(f"Batch results: {batch_results}")
        logger.debug(f"Batch results type: {type(batch_results)}")
        for batch in batch_results:
            output_rows.extend(batch)

        # Clear tasks for the next batch
        tasks.clear()

        # Introduce a delay between batches
        await asyncio.sleep(delay)

    output_df = pd.DataFrame(output_rows)

    # join input_df[['Assignment_Name','Notebook_name','Question']] with output, key on 'Question'
    output_df = pd.merge(
        input_df[["Assignment_Name", "Notebook_name", "Question"]],
        output_df,
        on="Question",
        how="inner",
    )

    output_df.drop_duplicates(subset=["Question"], inplace=True)
    assignment_name = input_df["Assignment_Name"].unique()[0]
    output_df.to_csv(
        settings.PROCESSED_DATA_DIR / f"{assignment_name}/output.csv", index=False
    )
