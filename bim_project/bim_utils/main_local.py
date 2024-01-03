#

import argparse
import postgre
import docker

def main_local():

    parser = argparse.ArgumentParser(prog="bim_utils", description="This local version designed for getting logs from the containers.")

    # create sub-parser
    sub_parser = parser.add_subparsers(help='Sub-command help')   

    # create the parser for the 'docker' sub-command
    parser_docker = sub_parser.add_parser('docker', help='Getting available commands for docker containers.')

    # create the sub-parser for the 'docker' sub-command
    docker_sub_parser = parser_docker.add_parser('logs', help='Getting logs from the docker container[s].')
    docker_sub_parser.add_argument('-f', )






    # subcommand = parser.add_mutually_exclusive_group()
    docker.add_argument('-f', '--file', help='save logs in a file', action='store_true')
    docker.add_argument('-ls', '--list', help='display running containers', action='store_true')
    args = parser.parse_args()
    print(args)




# Function isn't ready.
def run_sql():
    
    pg = postgre.DB()
    pg.exec_query_from_file()





