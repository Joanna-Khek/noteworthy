import asyncio
import os
from pathlib import Path
import sys

import pandas as pd
import yaml
from dotenv import load_dotenv
import omegaconf
import hydra

import settings
from data_extractor import DataExtractor
from data_manager import DataProcessor
from model_async import Model
from model_main_async import async_main, process_batch
from loguru import logger



def extract_assignments(from_assignment, to_assignment: int = 0):

    data_processor = DataProcessor(
        gitlab_url="https://gitlab.aisingapore.net",
        private_token=os.getenv("GITLAB_TOKEN"),
        data_path=Path("data/raw"),
    )

    data_processor.extract_all_files(from_assignment, to_assignment)

@hydra.main(version_base=None, config_path=str(settings.CONFIG_DIR), config_name="config.yaml")
def main(config):

    load_dotenv()

    # with open(settings.CONFIG_DIR / "config.yaml") as stream:
    #     config = yaml.safe_load(stream)

    # logging configuration
    logger.add(
        settings.LOG_DIR / "main.log", rotation="10 MB", level=config["log_level"]
    )
    logger.add(
        sys.stderr, format="{time} {level} {message}", level=config["log_level"]
    )

    # # 1. Gitlab pipeline
    logger.info("Extracting assignments from Gitlab")
    extract_assignments(
        from_assignment=config["start_assignment"],
        to_assignment=config["end_assignment"],
    )

    # # 2. Data extraction pipeline
    assignment_names = [
        f"assignment{n}"
        for n in range(config["start_assignment"], config["end_assignment"] + 1)
    ]

    logger.info("Extracting content from notebooks")
    de = DataExtractor()
    de.extract_content(assignment_names=assignment_names)

    # 3. LLM output pipeline
    # instantiate LLM
    logger.info("Instantiating LLM")
    llm = Model(
        model_name=os.getenv("MODEL_NAME"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_version=os.getenv("OPENAI_API_VERSION"),
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        top_p=config["top_p"],
    )

    # get all directories in processed_data_dir using pathlib
    input_csv_list = [
        x / "input_llm.csv" for x in settings.PROCESSED_DATA_DIR.iterdir() if x.is_dir() and x.name in assignment_names
    ]
    questions_df = pd.read_csv(settings.CONFIG_DIR / "questions_data.csv")

    # filter questions_df assignments to only those in the range
    questions_df = questions_df[questions_df["Assignment"].isin(assignment_names)]

    logger.info("Processing LLM output")
    for input_csv in input_csv_list:
        input_df = pd.read_csv(input_csv)

        logger.debug(input_df.head())
        asyncio.run(
            async_main(
                questions_df,
                llm,
                input_df,
                batch_size=config["batch_size"],
                delay=config["delay"],
            )
        )


if __name__ == "__main__":
    main()
