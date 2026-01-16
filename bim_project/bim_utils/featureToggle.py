import logging
import requests
import platform
import os
import sys
from rich.console import Console
from rich.table import Table
from tools import Tools
from atlassian import Confluence
from bs4 import BeautifulSoup


_logger = logging.getLogger(__name__)

class FeatureToggle:

    _api_GetFeatures: str = 'api/Features/GetFeatures'
    _api_Features: str = 'api/Features'
    headers = {'accept': '*/*', 'Content-type': 'application/json; charset=utf-8'}

    def display_features(self, url, enabled=False, disabled=False):
        """ Display list of features in pretty table. """

        try:
            response = requests.get(url=f"{url}/{self._api_GetFeatures}", headers=self.headers, verify=False)
        except Exception as err:
            _logger.error(err)
            print("Error! Couldn't get list of features. Check the logs.")
            return False
        table = Table()
        table.add_column("No.", style="cyan", no_wrap=True)
        table.add_column("Feature", style="magenta")
        table.add_column("Status", justify="center", highlight=False)
        count = Tools.counter()
        if response.status_code == 200:
            _logger.info(f"{self._api_GetFeatures} {response}")
            data: dict = response.json()
            print()
            for key,value in sorted(data.items()):
                if enabled and value:
                    table.add_row(str(count()), key.capitalize(), "[green]on[/green]")
                elif disabled and not value:
                    table.add_row(str(count()), key.capitalize(), "[red]off[/red]")
                elif not enabled and not disabled:
                    table.add_row(str(count()), key.capitalize(), "[green]on[/green]" if value else "[red]off[/red]")
        else:
            print(f"Error {response.status_code} occurred during GetFeatures request. Check the logs.")
            _logger.error(response.text)
            return False
        console = Console()
        console.print(table)

    def get_list_of_features(self, url, return_data=False) -> list:
        """ Function returns a list of features, or return's all data(dict) if return_data is true. """

        try:
            response = requests.get(url=f"{url}/{self._api_GetFeatures}", headers=self.headers, verify=False)
        except Exception as err:
            _logger.error(err)
            print("Error! Couldn't get list of features. Check the logs.")
            return False
        if response.status_code == 200:
            _logger.info(f"{self._api_GetFeatures} {response}")
            data: dict = response.json()
            ft_list: list = [ft for ft in data]
        else:
            print(f"Error {response.status_code} occurred during GetFeatures request. Check the logs.")
            _logger.error(response.text)
            return False
        return data if return_data else ft_list

    def set_feature(self, url, bearerToken, features: list, is_enabled=True):
        """ Function to enable/disable FT. """

        ft_list = self.get_list_of_features(url)
        headers = {'Authorization': f'Bearer {bearerToken}', 'accept': '*/*', 'Content-type':'application/json; charset=utf-8'}
        json_data = is_enabled
        for feature in features:
            if feature.lower() not in ft_list:
                print(f"Incorrect FT name: {feature}")
                continue
            response = requests.put(url=f'{url}/{self._api_Features}/{feature}', json=json_data, headers=headers, verify=False)
            if response.status_code in (200, 201, 204):
                _logger.info(f"{url}/{self._api_Features}/{feature} {response}")
                response = requests.get(url=f'{url}/{self._api_Features}/{feature}', json=json_data, headers=headers, verify=False)
                ft_enabled: bool = response.json()
                print("{0}: {1}".format(feature, 'enabled' if ft_enabled else 'disabled'))
            else:
                _logger.error(response.status_code, '\n', response.text)
                print(f"{feature} wasn't enabled. Check the log. Error: {response.status_code}.")
        return

    def compare_source_and_target(self, ft_conf: list, project_name: str, env: str):
        """ Function compares FT between confluence and current Bimeister settings on a given stand. """

        match project_name:
            case "gazprom-suid":
                url = "https://suid-t.bimeister.io" if env == "test" else "https://suid-p.bimeister.io"
            case "gazprom-dtoir":
                url = "https://dtoir-t.bimeister.io" if env == "test" else "https://dtoir-p.bimeister.io"
            case "gazprom-salavat":
                url = "https://gazprom-salavat-t.bimeister.io"
            case "novatek-murmansk":
                url = "https://novatek-murmansk-p.bimeister.io"
            case "novatek-yamal":
                url = "https://novatek-yamal-t.bimeister.io"
            case "crea-cod":
                url = "https://crea-cod.bimeister.io"
            case _:
                print("No url was found.")
                return None
        all_ft_on_stand = self.get_list_of_features(url, return_data=True)
        if not all_ft_on_stand or not ft_conf:
            return None
        enabled_ft_on_stand = sorted([key.capitalize() for key,value in all_ft_on_stand.items() if value])
        result = {"Add": [ft for ft in ft_conf if ft not in enabled_ft_on_stand], 
                  "Remove": [ft for ft in enabled_ft_on_stand if ft not in ft_conf]}
        add_empty: bool = not result['Add']
        remove_empty: bool = not result['Remove']
        if add_empty and remove_empty:
            print("Total match!")
            return
        if not add_empty:
            print("Add:\n" + "\n".join(f"- {ft}" for ft in result['Add']))
        if not remove_empty:
            print("Remove:\n" + "\n".join(f"- {ft}" for ft in result['Remove']))


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
            _logger.error(err)
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
            _logger.error(err)
            print(f"Incorrect input. Should be a number in range between 1 and {len(projects)}")
            sys.exit()
        return projects[project_number]

    def get_ft_for_project(self, all_ft_data, project_name, save=False, save_pretty=False, no_print=False, env=""):
        """ Save in different formats or print FT for specific project. Function requires data of all projects FT."""

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
        if not no_print:
            console.print(table)
        if save or save_pretty:
            filename: str = f'{project_name}-ft.txt' if save else f'{project_name}-ft.yaml'
            with open(filename, 'w', encoding='utf-8') as file:
                if save:
                    for env, ft in project_data.items():
                        file.write("{0}: {1}\n".format(env, " ".join(map(str, ft))))
                elif save_pretty:
                    for env in project_data:
                        file.write(f"{env}:")
                        env_ft_list = list(filter(None, project_data[env]))
                        if not env_ft_list:
                            file.write("\n")
                            continue
                        for ft in env_ft_list:
                            file.write(f"\n- {ft}")
                        file.write('\n\n')
            sep = "\\" if platform.system == "Windows" else "/"
            print(f"File saved: {os.getcwd()}{sep}{filename}")
        else:
            if env:
                project_data = [x for x in project_data[env] if x]
            return project_data

    def display_projects(self):
        """ Print all the projects which exist. """

        pass