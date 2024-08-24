import os
from pathlib import Path
import csv
import gitlab
from gitlab.exceptions import GitlabAuthenticationError
from loguru import logger


class DataProcessor:
    def __init__(self, gitlab_url, private_token, data_path):
        self.gitlab_url = gitlab_url
        self.private_token = private_token
        self.gl = self._authenticate_gitlab()
        self.data_path = data_path

    def _authenticate_gitlab(self) -> gitlab:
        """Authenticate gitlab account with private token

        Returns:
            gitlab: gitlab object
        """
        gl = gitlab.Gitlab(url=self.gitlab_url, private_token=self.private_token)
        try:
            gl.auth()
            logger.info("GitLab authentication successful!")
        except GitlabAuthenticationError as e:
            logger.error(f"Authentication failed: {e}")

        return gl

    def _get_project_id(self) -> str:
        """Identify id of project based on repo name

        Returns:
            str: id of project
        """
        # Returns all projects in the gitlab url
        projects = self.gl.projects.list(all=True)

        # Filter only AIAP 16 Assignment repo
        for project in projects:
            if (
                project.name == "all-assignments"
                and project.path_with_namespace
                == "aiap/deep-skilling-phase/aiap16/all-assignments"
            ):
                project_id = project.id
                break
        return project_id

    def download_branch_files(
        self, project_id: str, branch_name: str, assignment_name: str
    ) -> None:
        """Download all .ipynb and .py files from apprentice's branch
        to local directory

        Args:
            project_id (str): the id of the project
            branch_name (str): gitlab branch name of apprentice
            assignment_name (str): Name of assignment
        """

        # Get project ID
        # project_id = self._get_project_id()
        project = self.gl.projects.get(project_id)

        # Get all files in apprentice's branch
        branch_folders = project.repository_tree(
            path=assignment_name, ref=branch_name, get_all=True
        )

        if len(branch_folders) == 0:
            raise ValueError(
                f"No files found in the folder: {assignment_name}, in branch: {branch_name}.",
                assignment_name,
                branch_name,
            )

        # Setup download folder for this branch
        download_dir = Path(self.data_path, branch_name, assignment_name)

        # Create download directory to store files
        os.makedirs(download_dir, exist_ok=True)
        logger.debug(f"Created directory: {download_dir}")

        # Loop through each item/folder in the branch and download relevant files
        # Relevant = ".ipynb" and ".py"
        for item in branch_folders:

            # Case 1: Single file
            if item["type"] == "blob":
                if item["name"].endswith(".ipynb") or item["name"].endswith(".py"):

                    # Write file to local path
                    local_path = Path(download_dir, item["name"])

                    with open(local_path, "wb") as f:
                        project.files.raw(
                            file_path=item["path"],
                            ref=branch_name,
                            streamed=True,
                            action=f.write,
                        )
                    logger.debug(f"Downloaded: {item['path']}")

            # Case 2: Files within src folder
            elif item["type"] == "tree":
                if item["name"] == "src":
                    sub_items = project.repository_tree(
                        path=item["path"], ref=branch_name
                    )

                    for file in sub_items:
                        if file["name"].endswith(".ipynb") or file["name"].endswith(
                            ".py"
                        ):
                            # Write file to local path
                            local_path = Path(download_dir, file["name"])

                            with open(local_path, "wb") as f:
                                project.files.raw(
                                    file_path=file["path"],
                                    ref=branch_name,
                                    streamed=True,
                                    action=f.write,
                                )
                            logger.debug(f"Downloaded: {file['path']}")

    def extract_all_files(self, from_assignment: int = 1, to_assignment: int = 0):
        """This method extract all the assignment artifacts from Gitlab repository

        Args:
            from_assignment (int, optional): Extract Gitlab artifact from stated assignment onwards. Defaults to 1.
            to_assignment (int, optional): Extract Gitlab artifact until stated assignment If this parameter is not stated,
                then only extract the assignment stated in from_assignment. Defaults to 0.
        """
        if to_assignment == 0:
            to_assignment = from_assignment

        if to_assignment < from_assignment:
            raise ValueError("from_assignment variable is less than to_assignment")

        # Get project ID
        project_id = self._get_project_id()

        # TODO: Make the path configurable
        with open("config/gitlab_branches.csv") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip the headers
            branches = list(reader)

        # Note: Assignment0 is skip as there wasnt any much Q&A
        # Note: For current configuration only support up to assignment19
        # Note: Currently identify if assignment is not yet release by determine if
        # 5 apprentise dont have the folder yet

        assignment_num = range(from_assignment, to_assignment + 1)

        # To indicate if assignment folder is not yet release.
        counter_of_missing_assignment = 0

        for num in assignment_num:
            for name in branches:
                if counter_of_missing_assignment > 4:
                    logger.info(f"Seems like assignment {num} is not out yet")
                    return

                logger.debug(f"{name}, {num}")
                try:
                    self.download_branch_files(
                        project_id=project_id,
                        branch_name=name[1],
                        assignment_name=f"assignment{num}",
                    )
                except ValueError as err:
                    logger.error(err.args)
                    counter_of_missing_assignment += 1
