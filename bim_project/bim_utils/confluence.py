import os
import sys
from log import Logs
from tools import *
from atlassian import Confluence
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table


logger = Logs().f_logger(__name__)

class Conf:

    ft_page_id = "1461357571"
    url = "https://confluence.bimeister.io"
    project_name_suid: str = 'gazprom-suid'
    project_name_dtoir: str = 'gazprom-dtoir'
    project_name_salavat: str = 'gazprom-salavat'
    project_name_murmansk: str = 'novatek-murmansk'
    project_name_yamal: str = 'novatek-yamal'
    project_name_crea_cod: str = 'crea-cod'

    def get_confluence_page(self) -> dict:
        """ Get confluence page with needed table information. """

        # Initialize Confluence client (Server/Data Center)
        personal_access_token: str = os.getenv('CONFLUENCE_TOKEN')
        confluence = Confluence(
            url = self.url, # Base URL
            token = personal_access_token,
            cloud=False  # Critical for Server/Data Center
        )
        if not Tools.is_url_available(self.url):
            print(f"No connection to {self.url}")
            sys.exit()
        try:
            page = confluence.get_page_by_id(self.ft_page_id, expand="body.view")
        except Exception as err:
            logger.error(err)
            print(err)
            sys.exit()
        return page

    def get_ft_data_of_all_projects(self, page: dict) -> dict:
        """ Get projects FT information for of all projects. """

        html_content = page["body"]["view"]["value"]
        soap = BeautifulSoup(html_content, 'html.parser')
        table = soap.find('table', class_='relative-table wrapped confluenceTable')
        if not table:
            print("No table in confluence were found. Exit!")
            sys.exit()

        # create dictionary with all projects and all environments: prod, test, demo
        ft_projects_data = {
             self.project_name_suid: {'prod': [], 'test': [], 'demo': []}
            ,self.project_name_dtoir: {'prod': [], 'test': [], 'demo': []}
            ,self.project_name_salavat: {'prod': [], 'test': [], 'demo': []}
            ,self.project_name_murmansk: {'prod': [], 'test': [], 'demo': []}
            ,self.project_name_yamal: {'prod': [], 'test': [], 'demo': []}
            ,self.project_name_crea_cod: {'prod': [], 'test': [], 'demo': []}
            }

        # ft_projects_data = dict({cell.get_text(strip=True): {'prod': [], 'test': [], 'demo': []} for cell in table.find('tbody').find_all('tr')[2]})
        # ft_colname_idx: int = 4
        # ft_names: list = [row.find_all('td')[ft_colname_idx].get_text(strip=True) for row in table.find('tbody').find_all('tr')[4:]]

        # columns indexes in the ft table
        ft_name_idx: int = 4
        gazprom_salavat_prod_idx, gazprom_salavat_test_idx, gazprom_salavat_demo_idx = 5, 6, 7
        gazprom_suid_prod_idx, gazprom_suid_test_idx, gazprom_suid_demo_idx = 8, 9, 10
        gazprom_dtoir_prod_idx, gazprom_dtoir_test_idx, gazprom_dtoir_demo_idx= 11, 12, 13
        novatek_murmansk_prod_idx, novatek_murmansk_test_idx, novatek_murmansk_demo_idx = 14, 15, 16
        novatek_yamal_prod_idx, novatek_yamal_test_idx, novatek_yamal_demo_idx = 17, 18, 19
        crea_cod_prod_idx, crea_cod_test_idx, crea_cod_demo_idx = 20, 21, 22

        on: str = "✅"
        for row in table.find('tbody').find_all('tr')[4:]:
            ft_name: str = row.find_all('td')[ft_name_idx].get_text(strip=True)

            if row.find_all('td')[gazprom_suid_prod_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_suid]['prod'].append(ft_name.title())
            if row.find_all('td')[gazprom_suid_test_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_suid]['test'].append(ft_name.title())
            if row.find_all('td')[gazprom_suid_demo_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_suid]['demo'].append(ft_name.title())

            if row.find_all('td')[gazprom_dtoir_prod_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_dtoir]['prod'].append(ft_name.title())
            if row.find_all('td')[gazprom_dtoir_test_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_dtoir]['test'].append(ft_name.title())
            if row.find_all('td')[gazprom_dtoir_demo_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_dtoir]['demo'].append(ft_name.title())

            if row.find_all('td')[gazprom_salavat_prod_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_salavat]['prod'].append(ft_name.title())
            if row.find_all('td')[gazprom_salavat_test_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_salavat]['test'].append(ft_name.title())
            if row.find_all('td')[gazprom_salavat_demo_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_salavat]['demo'].append(ft_name.title())

            if row.find_all('td')[novatek_murmansk_prod_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_murmansk]['prod'].append(ft_name.title())
            if row.find_all('td')[novatek_murmansk_test_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_murmansk]['test'].append(ft_name.title())
            if row.find_all('td')[novatek_murmansk_demo_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_murmansk]['demo'].append(ft_name.title())

            if row.find_all('td')[novatek_yamal_prod_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_yamal]['prod'].append(ft_name.title())
            if row.find_all('td')[novatek_yamal_test_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_yamal]['test'].append(ft_name.title())
            if row.find_all('td')[novatek_yamal_demo_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_yamal]['demo'].append(ft_name.title())

            if row.find_all('td')[crea_cod_prod_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_crea_cod]['prod'].append(ft_name.title())
            if row.find_all('td')[crea_cod_test_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_crea_cod]['test'].append(ft_name.title())
            if row.find_all('td')[crea_cod_demo_idx].get_text(strip=True) == on:
                ft_projects_data[self.project_name_crea_cod]['demo'].append(ft_name.title())
        for key in ft_projects_data:
            ft_projects_data[key]['prod'].sort()
            ft_projects_data[key]['test'].sort()
            ft_projects_data[key]['demo'].sort()
        return ft_projects_data
    
    def choose_project(self) -> str:
        """ Prompt user to project if nothing was provided. """

        projects: list = [
             self.project_name_suid
            ,self.project_name_dtoir
            ,self.project_name_salavat
            ,self.project_name_murmansk
            ,self.project_name_yamal
            ,self.project_name_crea_cod
            ]
        try:
            for number, project in enumerate(projects, 1):
                print(f"{number}. {project}")
            project_number = int(input("Choose number of the project: ")) - 1
            if (project_number + 1) < 1 or (project_number + 1) > len(projects):
                print("Incorrect input. Exit!")
                sys.exit()
        except ValueError as err:
            logger.error(err)
            print(f"Incorrect input. Should be a number in range between 1 and {len(projects)}")
            sys.exit()
        return projects[project_number]

    def display_ft_for_project(self, all_ft_data, project_name, save=False, save_pretty=False):
        """ Display FT for specific project. Function requires data of all projects FT."""

        if not all_ft_data or not project_name:
            return None
        project_data = all_ft_data[project_name]
        prod: list = project_data['prod']
        test: list = project_data['test']
        demo: list = project_data['demo']
        table = Table(title=project_name, show_footer=True)
        table.add_column("Prod", justify="left", no_wrap=True, style="#875fff", footer=f"Total: {len(prod)}", max_width=55)
        table.add_column("Test", justify="left", no_wrap=True, style="#875fff", footer=f"Total: {len(test)}", max_width=55)
        table.add_column("Demo", justify="left", no_wrap=True, style="#875fff", footer=f"Total: {len(demo)}", max_width=55)

        max_length: int = max(len(prod), len(test), len(demo))
        prod.extend([''] * (max_length - len(prod)))
        test.extend([''] * (max_length - len(test)))
        demo.extend([''] * (max_length - len(demo)))
        for prod, test, demo in zip(prod, test, demo):
            table.add_row(prod, test, demo)
        console = Console()
        console.print(table)
        if save or save_pretty:
            filename: str = f'{project_name}-ft.txt'
            with open(filename, 'w', encoding='utf-8') as file:
                if save:
                    for env, ft in project_data.items():
                        file.write("{0}: {1}\n".format(env, " ".join(map(str, ft))))
                elif save_pretty:
                    for env in project_data:
                        file.write(env + ':')
                        if not any(project_data[env]):
                            file.write(' None\n')
                            continue
                        for ft in project_data[env]:
                            file.write(f"\n {ft}")
                        file.write('\n\n')
            sep = "\\" if Tools.is_windows() else "/"
            print(f"File saved: {os.getcwd()}{sep}{filename}")

    def display_projects(self):
        """ Print all the projects which exist. """

        pass
