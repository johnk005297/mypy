##
##

import os
import sys
import yaml


def check_service_validation(services):
    """ Internal script check spelling name of the services in dictionary_of_services dictionary. """

    validation:list = [service for service in services.keys() if service[-1] != ':']
    if validation:
        print(validation)

    return True if not validation else False

def get_docker_compose_file():

    yml_file = input("Enter the name of the .yml file: ")
    if not yml_file:
        yml_file:str = 'docker-compose.deploy-local.effective.yml'
    else:
        yml_file += '.yml' if yml_file[-4:] != '.yml' else ''
    if not os.path.isfile(f"{os.getcwd()}/{yml_file}"):     # check if the file exists
        sys.exit("No .yml file has been found. Exit!")
    return yml_file

def read_docker_compose_file(filename, services):
    """ Read .yml text file in yml_file var. All open ports will be excluded. """
    
    d_compose:list = []  # Creating a list of .yml file in format ['first string', 'second string', etc]
    array_to_exclude: list = ['ports:']    # Generating list for checking the elements in the yml_file

    for value in services.values():
        if isinstance(value, list):
            for x in value:
                array_to_exclude.append(x)
        else:
            array_to_exclude.append(value)
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                l = line.strip()

                # If the line is empty/just whitespaces or contain any open ports - don't add in the yml_file
                skip_line = False
                for value in array_to_exclude:
                    if value in l:
                        skip_line = True
                        break
                if not l or skip_line:
                    continue
                else:
                    d_compose.append(line)
        d_compose += ['\n'*2]  # Add two more empty elements to stay in the list range during future checks of the next lines. Precaution measure.
        return d_compose
    except Exception as err:
            print("Error: ", err)
            return False

def read_docker_ports_file(filename):
    """ Function reads the .yml text file with ports, and returns an actual list of bim services in dictionary format. """

    services = dict()
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)['services']
    except Exception as err:
        print("Error: ", err)
        return False

    for key, values in data.items():
        for k,v in values.items():
            if k != 'ports':
                continue
            if len(v) == 1:
                services[key + ':'] = ''.join(v).split(':', 1)[1]
            else:
                services[key + ':'] = []
                for x in v:
                    services[key + ':'].append(''.join(x).split(':', 1)[1])
    return services

def detect_service_block(yml_file):
    """ Function counts amount of whitespaces in needed lines. """

    for num, line in enumerate(yml_file):
        if line.strip() == 'services:':
            spaces_before_service_name = len(yml_file[num+1]) - len(yml_file[num+1].lstrip())  # calculate amount of whitespaces to the left of the service
            break
    try:
        spaces_before_service_name
    except NameError as err:
        print(f"Can't find 'service:' block. Check {yml_file} file! Exit.")
        return False
    return spaces_before_service_name

def insert_ports(services, compose_file):
    """ Funtion inserts ports into docker-compose file. If port not in the services dictionary, it stays closed. """

    ports:str = 'ports:\n'
    for index in range(len(compose_file)):
        current_str = compose_file[index].strip()
        if services.get(current_str) and spaces == ( len(compose_file[index]) - len(compose_file[index].lstrip()) ):        # calculating the exact spaces for the service block to identify it
            if isinstance(services.get(current_str), list):
                for x in range(len(services.get(current_str)), 0, -1):
                    compose_file.insert(index+1, " "*(spaces+2) + f"- \"0.0.0.0:{services.get(current_str)[x-1]}\"\n")
                compose_file.insert(index+1, " "*(spaces+2) + ports)    # line will be insterted in line+1, so it will be constructed in proper order. "ports:, - 0.0.0.0, etc."
            else:
                compose_file.insert(index+1, " "*(spaces+2) + ports + " "*(spaces+2) + f"- \"0.0.0.0:{services.get(current_str)}\"\n")
    return compose_file

def add_ssl_certificate(docker_compose):
    """ Fill ssl_certificate value. """

    count = 0
    for index in range(len(docker_compose)):
        if count == 2:
            break
        line = docker_compose[index].strip().split(":")[0]
        if line == 'SSL_CERTIFICATE':
            spaces = len(docker_compose[index]) - len(docker_compose[index].lstrip())
            docker_compose[index] = " "*spaces + "SSL_CERTIFICATE: '/etc/nginx/ssl/bimeister.io.crt'\n"
            count += 1
        if line == 'SSL_CERTIFICATE_KEY':
            spaces = len(docker_compose[index]) - len(docker_compose[index].lstrip())
            docker_compose[index] = " "*spaces + "SSL_CERTIFICATE_KEY: '/etc/nginx/ssl/bimeister.io.key'\n"
            count += 1
    return docker_compose

def turn_on_swagger(docker_compose):
    """ Turn on swagger API. """

    for index in range(len(docker_compose)):
        line = docker_compose[index].strip()
        spaces_to_the_left:str = " "*( len(docker_compose[index]) - len(docker_compose[index].lstrip()) )
        if line == "ASPNETCORE_ENVIRONMENT: Production":
            docker_compose[index] = spaces_to_the_left + "ASPNETCORE_ENVIRONMENT: Development\n"

def write_to_file(filename, docker_compose):
    """ Write yml result list to a text file. """

    compose_file_open_ports = filename[:-4] + '_open_ports.yml'
    with open(compose_file_open_ports, 'w', encoding='utf-8') as file:
        for line in docker_compose:
            file.write(line)

    print(f'\nFile "{compose_file_open_ports}" is ready.')
    if sys.platform == 'win32':
        os.system('pause')


if __name__ == "__main__":
    services = read_docker_ports_file('docker-compose.ports.yml')
    filename = get_docker_compose_file()
    docker_compose = read_docker_compose_file(filename, services)
    spaces = detect_service_block(docker_compose)
    insert_ports(services, docker_compose)
    add_ssl_certificate(docker_compose)
    turn_on_swagger(docker_compose)
    write_to_file(filename, docker_compose)

