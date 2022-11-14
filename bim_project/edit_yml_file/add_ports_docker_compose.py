##
import os
import sys


def alter_yml():
    
    
    yml_file = input("Enter the name of the .yml file: ")
    yml_file += '.yml' if yml_file[-4:] != '.yml' else ''
    # check if the file exists
    if os.path.isfile(f"{os.getcwd()}/{yml_file}"):
        pass
    else:
        print("No .yml file has been found. Exit!")
        sys.exit()

    read_file = os.getcwd() + "\\" + yml_file
    yml_file_open_ports = yml_file[:-4] +'_open_ports.yml'

    # Creating a list of .yml file in format ['first string', 'second string', etc]
    lst: list = []
    p: tuple = ('ports:','80:5000','443:5001','8081:5000','8087:5000','8085:5000','8084:5000','8082:5000','8089:5000','5432:5432','5433:5432','8080:5000','9000:9000','5103:5000',
                '5672:5672','15672:15672','6379:6379','5434:5432','8086:8086','5501:5000','8088:5000','7687:7687','7474:7474','5430:5432','7782:5000','8090:5000',
                '8091:5000','8092:5000','10000:5000','10010:5000','10020:5000','10030:5000','10040:5000','10060:5000','5435:5432','5436:5432','5440:5432','5437:5432','5450:5432')
    
    try:
        with open(read_file, 'r', encoding='utf-8') as file:
            for line in file:
                l = line.strip()
                # If the line is empty/just whitespaces or contain any open ports - don't add in the lst
                if len(l) == 0 or p[0] in l or p[1] in l or p[2] in l or p[3] in l or p[4] in l or p[5] in l or p[6] in l or p[7] in l or p[8] in l or p[9] in l or p[10] in l or p[11] in l or p[12] in l \
                    or p[13] in l or p[14] in l or p[15] in l or p[16] in l or p[17] in l or p[18] in l or p[19] in l or p[20] in l or p[21] in l or p[22] in l or p[23] in l or p[24] in l or p[25] in l \
                    or p[26] in l or p[27] in l or p[28] in l or p[29] in l or p[30] in l or p[31] in l or p[32] in l or p[33] in l or p[34] in l or p[35] in l or p[36] in l \
                    or p[37] in l or p[38] in l:
                    continue
                else:
                    lst.append(line)

    except Exception as err:
            sys.exit("Error: ", err)    
    
    count = 0
    ports = 'ports:\n'
    for index in range(len(lst)):
        if lst[index].rstrip() == 'services:':
            count_spaces_for_service = len(lst[index+1]) - len(lst[index+1].lstrip(' '))
            break
    
    try:
        count_spaces_for_service
    except NameError as err:
        sys.exit(f"Can't find 'service:' block. Corrupted {yml_file}?! Exit.")


    for index in range(len(lst)):
        current_str = lst[index].rstrip()   # current line from the .yml file without whitespaces from the right
        count_spaces_next_line = len(lst[index+1]) - len(lst[index+1].lstrip(' '))    # calculate amount of whitespaces to the right of the next string

        if "environment:" in current_str and count == 0:          # count spaces in environment block only once
            count_spaces_in_environ_block = len(lst[index+1]) - len(lst[index+1].lstrip(' '))
            count += 1        
        
        if "SSL_CERTIFICATE:" in current_str:                             
            lst[index] = (' ')*count_spaces_in_environ_block + "SSL_CERTIFICATE: '/etc/nginx/ssl/bimeister.io.crt'\n"             
        elif "SSL_CERTIFICATE_KEY:" in current_str:            
            lst[index] = (' ')*count_spaces_in_environ_block + "SSL_CERTIFICATE_KEY: '/etc/nginx/ssl/bimeister.io.key'\n"

        if " "*count_spaces_for_service + "auth:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8080:5000\"\n")

        elif " "*count_spaces_for_service +  "authdb:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5433:5432\"\n")

        elif " "*count_spaces_for_service +  "bimeister_frontend:" == current_str:                  
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:80:5000\"\n" + " "*count_spaces_next_line + "- \"0.0.0.0:443:5001\"\n")  
        
        elif " "*count_spaces_for_service +  "collisions:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8092:5000\"\n")
        
        elif " "*count_spaces_for_service +  "db:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5432:5432\"\n")
        
        elif " "*count_spaces_for_service +  "e57service:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8082:5000\"\n")

        elif " "*count_spaces_for_service +  "graphdb:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:7687:7687\"\n" + " "*count_spaces_next_line + "- \"0.0.0.0:7474:7474\"\n")

        elif " "*count_spaces_for_service +  "ifc-geometry-converter:"  == current_str:                        
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8088:5000\"\n")

        elif " "*count_spaces_for_service +  "influxdb:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8086:8086\"\n")

        elif " "*count_spaces_for_service +  "ldapwebapi:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5103:5000\"\n")

        elif " "*count_spaces_for_service +  "license-service:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5501:5000\"\n")
        
        elif " "*count_spaces_for_service +  "mailservice:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8084:5000\"\n")
        
        elif " "*count_spaces_for_service +  "minio:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:9000:9000\"\n")

        elif " "*count_spaces_for_service +  "notification:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8090:5000\"\n")

        elif " "*count_spaces_for_service +  "pdfservice:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8089:5000\"\n")

        elif " "*count_spaces_for_service +  "pointcloudapi:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8085:5000\"\n")

        elif " "*count_spaces_for_service +  "rabbitmq:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5672:5672\"\n" + " "*count_spaces_next_line + "- \"0.0.0.0:15672:15672\"\n")

        elif " "*count_spaces_for_service +  "redis:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:6379:6379\"\n")

        elif " "*count_spaces_for_service +  "spatialdb:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5434:5432\"\n")
        
        elif " "*count_spaces_for_service +  "spatialwebapi:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8087:5000\"\n")

        elif " "*count_spaces_for_service +  "tasksworker:"  == current_str:                   
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8091:5000\"\n")

        elif " "*count_spaces_for_service +  "treesapi:"  == current_str:                   
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:7782:5000\"\n") 

        elif " "*count_spaces_for_service +  "treesdb:"  == current_str:                   
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5430:5432\"\n")

        elif " "*count_spaces_for_service +  "webapi:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8081:5000\"\n")
        
        elif " "*count_spaces_for_service +  "similar:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:10030:5000\"\n")
        
        elif " "*count_spaces_for_service +  "collision_calculator:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:10060:5000\"\n")
        
        elif " "*count_spaces_for_service +  "spatium_api:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:10000:5000\"\n")
        
        elif " "*count_spaces_for_service +  "ifc_converter:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:10040:5000\"\n")
        
        elif " "*count_spaces_for_service +  "filter:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:10020:5000\"\n")

        elif " "*count_spaces_for_service +  "filterdb:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5436:5432\"\n")
        
        elif " "*count_spaces_for_service +  "parser:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:10010:5000\"\n")
        
        elif " "*count_spaces_for_service +  "spatiumdb:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5435:5432\"\n")
        
        elif " "*count_spaces_for_service +  "potential_failure_messages_db:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5440:5432\"\n")
        
        elif " "*count_spaces_for_service +  "hangfiredb:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5437:5432\"\n")
        
        elif " "*count_spaces_for_service +  "timescaledb:"  == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5450:5432\"\n")
        
        else:
            pass

    with open(yml_file_open_ports, 'w', encoding='utf-8') as file:
        for line in lst:
            file.write(line)    
    
    if os.path.isfile(yml_file_open_ports):
        print(f'\nFile "{yml_file_open_ports}" is ready.')
    else:
        print("No file here")
    if sys.platform == 'win32':
        os.system('pause')

if __name__ == "__main__":      
    alter_yml()    
