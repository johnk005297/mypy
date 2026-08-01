import typer

import sys

from .service import Git


# git_app CLI
git_app = typer.Typer(help="Get info from gitlab. Search branches, tags, commits, product-collection.yaml data.")

class GitContext:
    """Store shared FT parameters"""
    def __init__(self):
        self.git = Git()

# Create a context instance
git_context = GitContext()

@git_app.command(name="search", help="Get table with info about branches, commits, tags, helm charts \[aliases: s]")
@git_app.command(name="s", hidden=True)
def search(
    branches: list[str] = typer.Argument(..., help="Search pattern by it's name"),
    project_id: str = typer.Option("bimeister", "--project", "-p", help="Name of the project in gitlab")
        ):
    """ Get table with info about branches, commits, tags, helm charts. """

    project = git_context.git.project()
    branch = git_context.git.branch()
    project_id = project.get_project_id(project='bimeister')
    if not project_id:
        sys.exit()
    data = branch.search_branches_commits_tags_jobs(project_id, search=branches)
    git_context.git.display_table_with_branches_commits_tags_jobs(data)

@git_app.command(name="build-charts")
@git_app.command(name="build-chart", hidden=True)
def build_charts(commit: str = typer.Argument(..., help="Requires commit to activate job")):
    """ Activate gitlab job: Build Charts. For a given commit. """

    project = git_context.git.project()
    branch = git_context.git.branch()
    job = git_context.git.job()
    project_id = project.get_project_id(project='bimeister')
    branches: list = branch.get_branch_name_using_commit(project_id, commit)
    if isinstance(branches, bool):
        print("No branch was found for provided commit.")
        sys.exit()
    if len(branches) == 1:
        branch_name = branches[0]
    else:
        branch_name = input(f"{commit} commit appears in several branches: {branches}\nSelect branch: ")
    charts_jobs = job.get_specific_jobs(project_id, commit=commit, branch_name=branch_name)
    pipeline_id = charts_jobs['pipeline_id']
    if not pipeline_id:
        print("No pipelines with 'success' status. Can't run the job.")
        sys.exit()
    data = job.run_job(project_id, str(charts_jobs['build_chart']['id']).split())
    if data:
        print(f"Job started successfully                    \
        \nname: {data['name']}                              \
        \npipeline id: {data['pipeline']['id']}             \
        \nref: {data['pipeline']['ref']}                    \
        \nurl: {data['pipeline']['web_url']}")  


@git_app.command()
def commit(
    commit: str = typer.Argument(..., help="Commit for product-collection.yaml info from"),
    project_name: str = typer.Option(None, "--project", "-p", help="Provide project name from the product-collection.yaml without prompt")
        ):
    """ Get info about services and databases from the product-collection.yaml file for a given commit. """

    project = git_context.git.project()
    product_collection = git_context.git.product_collection()
    project_id = project.get_project_id(project='bimeister')
    file_content: dict = product_collection.get_product_collection_file_content(project_id, commit)
    if not file_content:
        sys.exit()
    data = product_collection.parse_product_collection_yaml(file_content, project_name=project_name)
    if not data:
        sys.exit()
    else:
        project_name, services, db = data
    if not services or not db:
        sys.exit()
    product_collection.print_services_and_db(services, db)

@git_app.command()
def compare(
    commits: list[str] = typer.Argument(help="Flag expects two commits to compare differences between them")
        ):
    """ Compare two commits for difference in product-collection.yaml in DBs list and services list """

    project = git_context.git.project()
    product_collection = git_context.git.product_collection()
    project_id = project.get_project_id(project='bimeister')

    if len(commits) != 2:
        print("Need two commits two compare.")
        return None
    first_commit, second_commit = commits[0], commits[1]
    first_commit_data: dict = product_collection.get_product_collection_file_content(project_id, first_commit)
    second_commit_data: dict = product_collection.get_product_collection_file_content(project_id, second_commit)
    if not first_commit_data or not second_commit_data:
        sys.exit()
    data = product_collection.parse_product_collection_yaml(first_commit_data)
    if not data:
        sys.exit()
    first_commit_project_name, first_commit_services, first_commit_db = data
    data = product_collection.parse_product_collection_yaml(second_commit_data, project_name=first_commit_project_name)
    if not data:
        sys.exit()
    second_commit_project_name, second_commit_services, second_commit_db = data
    product_collection.compare_two_commits(first_commit_services, first_commit_db, second_commit_services, second_commit_db)