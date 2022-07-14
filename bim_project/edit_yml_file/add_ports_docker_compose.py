##
import os
import sys


def alter_yml():
    
    
    yml_file = input("Enter the name of the .yml file: ")
    yml_file += '.yml' if yml_file[-4:] != '.yml' else yml_file
    
    read_file = os.getcwd() + "\\" + yml_file
    yml_file_open_ports = yml_file[:-4] +'_open_ports.yml'
    
    
    # Creating a list of .yml file in format ['first string', 'second string', etc]    
    lst: list = []
    try:
        with open(read_file, 'r', encoding='utf-8') as file:    
            for line in file:
                if len(line.strip()) == 0:      # If the line is empty/just whitespaces - don't add in the lst
                    continue
                else:
                    lst.append(line)
            
    except Exception as err:
            sys.exit("Error: ", err)    
    
    count = 0
    ports = 'ports:\n'  
    for index in range(len(lst)):
        current_str = lst[index].strip()   # current line from the .yml file without whitespaces from both sides        
        count_spaces_next_line = len(lst[index+1]) - len(lst[index+1].lstrip(' '))    # calculate amount of whitespaces to the right of the next string

        if "environment:" in current_str and count == 0:          # count spaces in environment block only once
            count_spaces_in_environ_block = len(lst[index+1]) - len(lst[index+1].lstrip(' '))
            count += 1        
        
        if "SSL_CERTIFICATE:" in current_str:                             
            lst[index] = (' ')*count_spaces_in_environ_block + "SSL_CERTIFICATE: '/etc/nginx/ssl/bimeister.io.crt'\n"             
        elif "SSL_CERTIFICATE_KEY:" in current_str:            
            lst[index] = (' ')*count_spaces_in_environ_block + "SSL_CERTIFICATE_KEY: '/etc/nginx/ssl/bimeister.io.key'\n"

        if "auth:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5000:80\"\n")

        elif "authdb:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5433:5432\"\n")

        elif "bimeister_frontend:" == current_str:                  
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:80:80\"\n" + " "*count_spaces_next_line + "- \"0.0.0.0:443:443\"\n")  
        
        elif "collisions:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8092:80\"\n")
        
        elif "db:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5432:5432\"\n")
        
        elif "e57service:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8082:8082\"\n")

        elif "graphdb:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:7687:7687\"\n" + " "*count_spaces_next_line + "- \"0.0.0.0:7474:7474\"\n")

        elif "ifc-geometry-converter:" == current_str:                        
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8088:5500\"\n")

        elif "influxdb:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8086:8086\"\n")

        elif "ldapwebapi:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5103:80\"\n")

        elif "license-service:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5501:80\"\n")
        
        elif "mailservice:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8084:80\"\n")
        
        elif "minio:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:9000:9000\"\n")

        elif "notification:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8090:80\"\n")

        elif "pdfservice:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8089:5000\"\n")

        elif "pointcloudapi:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8085:80\"\n")

        elif "rabbitmq:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5672:5672\"\n" + " "*count_spaces_next_line + "- \"0.0.0.0:15672:15672\"\n")

        elif "redis:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:6379:6379\"\n")

        elif "spatialdb:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5434:5432\"\n")
        
        elif "spatialwebapi:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8087:80\"\n")

        elif "tasksworker:" == current_str:                   
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8091:80\"\n")

        elif "treesapi:" == current_str:                   
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:7782:80\"\n") 

        elif "treesdb:" == current_str:                   
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:5430:5432\"\n")

        elif "webapi:" == current_str:
            lst.insert(index+1, " "*count_spaces_next_line + ports + " "*count_spaces_next_line + "- \"0.0.0.0:8081:80\"\n")        
        
        else:
            pass

    with open(yml_file_open_ports, 'w', encoding='utf-8') as file:
        for line in lst:
            file.write(line)    
    
    if os.path.isfile(yml_file_open_ports):
        print(f'\nFile "{yml_file_open_ports}" is ready.')
    else:
        print("No file here")
    os.system('pause')

if __name__ == "__main__":      
    alter_yml()    
    
    


