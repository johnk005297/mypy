##
##

import os
import sys

version = '106'
''''''''''''''''''''''''

def alter_yml():
    
    yml_file = input("Enter the name of the .yml file: ")
    yml_file += '.yml' if yml_file[-4:] != '.yml' else ''
    # check if the file exists
    if not os.path.isfile(f"{os.getcwd()}/{yml_file}"):
        print("No .yml file has been found. Exit!")
        return False

    read_file = os.getcwd() + "\\" + yml_file
    yml_file_open_ports = yml_file[:-4] +'_open_ports.yml'

    yml_file_as_list:list = []  # Creating a list of .yml file in format ['first string', 'second string', etc]
    list_of_presented_services: list = [] # Array to detect current services


    dictionary_of_services: dict = \
    {   
        'bimeister_frontend:': ["80:5000", "443:5001"],
        'webapi:': "8081:5000",
        'spatialwebapi:': "8087:5000",
        'pointcloudapi:': "8085:5000",
        'mailservice:': "8084:5000",
        'e57service:': "8082:5000",
        'pdfservice:': "8089:5000",
        'db:': "5432:5432",
        'authdb:': "5433:5432",
        'auth:': "8080:5000",
        'minio:': "9000:9000",
        'ldapwebapi:': "5103:5000",
        'rabbitmq:': ["5672:5672", "15672:15672"],
        'keydb:': "6379:6379",
        'spatialdb:': "5434:5432",
        'influxdb:': "8086:8086",
        'license-service:': "5501:5000",
        'ifc-geometry-converter:': "8088:5000",
        'graphdb:': ["7687:7687", "7474:7474"],
        'treesdb:': "5430:5432",
        'treesapi:': "7782:5000",
        'notification:': "8090:5000",
        'tasksworker:': "8091:5000",
        'collisions:': "8092:5000",
        'spatium_api:': "10000:5000",
        'parser:': "10010:5000",
        'filter:': "10020:5000",
        'similar:': "10030:5000",
        'ifc_converter:': "10040:5000",
        'collision_calculator:': "10060:5000",
        'spatiumdb:': "5435:5432",
        'hangfiredb:': "5437:5432",                
        'timescaledb:': "5450:5432",        
        'nifi:': "8100:8080",                
        'enterprise_asset_management_db:': "5444:5432"
    }
    
    array_to_exclude: list = ['ports:']    # Generating list for checking the elements in the yml_file_as_list
    for value in dictionary_of_services.values():
        if isinstance(value, list):
            for x in value:
                array_to_exclude.append(x)
        else:
            array_to_exclude.append(value)

    try:
        with open(read_file, 'r', encoding='utf-8') as file:
            for line in file:
                l = line.strip()
                # If the line is empty/just whitespaces or contain any open ports - don't add in the yml_file_as_list
                flag_to_skip = False
                for value in array_to_exclude:
                    if value in l:
                        flag_to_skip = True
                        break

                if not l or flag_to_skip:
                    continue                
                else:
                    yml_file_as_list.append(line)
        yml_file_as_list += ['\n'*2]  # Add two more empty elements to stay in the list range during future checks of the next lines. Precaution measure.

    except Exception as err:
            print("Error: ", err)
            return False

    count:int = 0
    ports:str = 'ports:\n'    
    for num, line in enumerate(yml_file_as_list):
        if line.strip() == 'services:':
            num += 1
            spaces_before_service_name = len(yml_file_as_list[num]) - len(yml_file_as_list[num].lstrip())  # calculate amount of whitespaces to the left of the service
            count_spaces_next_line = len(yml_file_as_list[num+1]) - len(yml_file_as_list[num+1].lstrip())
            while len(yml_file_as_list[num]) - len(yml_file_as_list[num].lstrip()) >= spaces_before_service_name:
                if len(yml_file_as_list[num]) - len(yml_file_as_list[num].lstrip()) == spaces_before_service_name:
                    list_of_presented_services.append(yml_file_as_list[num].rstrip())
                num += 1
            break

    try:
        spaces_before_service_name
    except NameError as err:
        print(f"Can't find 'service:' block. Check {yml_file} file! Exit.")
        return False

    for index in range(len(yml_file_as_list)):
        current_str = yml_file_as_list[index].rstrip()   # current line from the .yml file without whitespaces from the right

        if "environment:" in current_str and count == 0:          # count spaces in environment block only once
            count_spaces_next_line_for_environ_block = len(yml_file_as_list[index+1]) - len(yml_file_as_list[index+1].lstrip(' '))
            count += 1        

        if "SSL_CERTIFICATE:" in current_str:
            yml_file_as_list[index] = (' ')*count_spaces_next_line_for_environ_block + "SSL_CERTIFICATE: '/etc/nginx/ssl/bimeister.io.crt'\n"             
        elif "SSL_CERTIFICATE_KEY:" in current_str:            
            yml_file_as_list[index] = (' ')*count_spaces_next_line_for_environ_block + "SSL_CERTIFICATE_KEY: '/etc/nginx/ssl/bimeister.io.key'\n"


        ''' Main insert block. Needed values goes to the yml_file_as_list array.
            If port isn't in dictionary_of_services, it stays closed.
        '''
        if current_str in list_of_presented_services and dictionary_of_services.get(current_str.lstrip()):
            if isinstance(dictionary_of_services.get(current_str.lstrip()), list):
                for x in range(len(dictionary_of_services.get(current_str.lstrip())), 0, -1):
                    yml_file_as_list.insert(index+1, " "*count_spaces_next_line + f"- \"0.0.0.0:{dictionary_of_services.get(current_str.lstrip())[x-1]}\"\n")
                yml_file_as_list.insert(index+1, " "*count_spaces_next_line + ports)  # line will be insterted in line+1, so it should be constructed in proper order. "ports:, - 0.0.0.0, etc."
            else:
                yml_file_as_list.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + f"- \"0.0.0.0:{dictionary_of_services.get(current_str.lstrip())}\"\n")


    with open(yml_file_open_ports, 'w', encoding='utf-8') as file:
        for line in yml_file_as_list:
            file.write(line)
    
    if os.path.isfile(yml_file_open_ports):
        print(f"sprint-{version}")
        print(f'\nFile "{yml_file_open_ports}" is ready.')
    else:
        print("No file here")
    if sys.platform == 'win32':
        os.system('pause')

if __name__ == "__main__":
    print(f"sprint-{version}")
    alter_yml()
