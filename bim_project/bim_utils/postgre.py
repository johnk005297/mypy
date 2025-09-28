import logging
import auth
import sys
import os
import platform
import pandas as pd
import psycopg
import psycopg_infdate
import re
from user import User
from getpass import getpass
from time import perf_counter
from datetime import timedelta
from tools import File
from mlogger import Logs


_logger = logging.getLogger(__name__)


class DB:

    def __init__(self):
        psycopg_infdate.register_inf_date_handler(psycopg)
        self.log = Logs()
        os.environ["PGCLIENTENCODING"] = "utf-8"

    def check_db_connection(self, **kwargs) -> bool:
        """ Function to check connection to db. """

        if not kwargs['password']:
            kwargs['password'] = getpass("Enter db password: ")
        try:
            conn = psycopg.connect(
                dbname=kwargs['db'],
                host=kwargs['host'],
                user=kwargs['user'],
                password=kwargs['password'],
                port=kwargs['port']
                                    )
        except psycopg.OperationalError as err:
            _logger.error(err)
            print(f"Database connection error.\n{err}")
            return False
        except psycopg.Error as err:
            _logger.error(err)
            print(self.log.err_message)
            return False
        else:
            _logger.info(conn)
            conn.close()
            return True

    def get_output_filename(self, filepath) -> str:
        """ Check for result output file name. """

        if not os.path.isfile(filepath):
            print(f"No such file: {os.path.basename(filepath)}")
            return None
        # remove special characters might be in the filename
        filepath = re.sub(r'[^a-zA-Z0-9./]', '_', filepath)
        output_file = os.path.basename(filepath).split('.')[0] + '.csv'
        # remove output file if it exists
        if os.path.isfile(output_file):
            try:
                os.remove(output_file)
            except OSError as err:
                print(f"Error removing file '{output_file}': {err}")
                print(f"Remove the file {output_file} and try again!")
                return None
        return output_file

    def execute_query_from_file(self, conn_string, filepath=None, split_by_delimiter=False, chunk_size=10_000, print_output=False, **kwargs):
        """ Execute query reading from the file. """

        def exec_query(conn, cur, query, header=True):
            if not query:
                return None
            try:
                # because of the PL/pgSQL approach, can't pass variable like in other .sql files
                if kwargs.get('task') and kwargs['task'] == 'drop-matviews':
                    query = query.format(kwargs['name'])
                    cur.execute(query)
                elif kwargs:
                    cur.execute(query, kwargs)
                else:
                    cur.execute(query)
                if cur.rowcount > 0:
                    if not os.path.isfile(output_file):
                        header, mode = True, 'w'
                    for chunk in self.record_batches(cur, chunk_size=chunk_size):
                        chunk.to_csv(output_file, index=False, header=header, mode=mode)
                        header, mode = False, 'a'
            except psycopg.errors.UndefinedTable as err:
                _logger.error(err)
                print(f'Error: {err}')
                return False
            except psycopg.errors.ProgrammingError as err:
                _logger.error(err)
                if cur.rowcount == -1:
                    conn.commit()
                    if not cur.statusmessage:
                        print(f"Updated rows: 0\n{query}")
                    else: print(cur.statusmessage)
                elif cur.rowcount > 0:
                    conn.commit()
                    print(cur.statusmessage)
                else:
                    conn.rollback()
                    _logger.error(err)
                    print(self.log.err_message)
            except psycopg.errors.ReadOnlySqlTransaction as err:
                _logger.error(err)
                print(f"Error: {err}")
                return False
            except psycopg.errors.DatabaseError as err:
                conn.rollback()
                _logger.error(err)
                print(err)
                return False
            except psycopg.errors.InterfaceError as err:
                conn.rollback()
                _logger.error(err)
                print(err)
                return False
            except Exception as err:
                conn.rollback()
                _logger.error(err)
                print(self.log.err_message)
            else:
                print(cur.statusmessage)
                conn.commit()

        output_file: str = self.get_output_filename(filepath)
        if not conn_string or not output_file:
            return None
        delimiter = ';'
        has_delimiter: bool = False
        with psycopg.connect(conn_string) as conn, conn.cursor() as cur:
            start = perf_counter()
            with open(filepath, 'r', encoding='utf-8') as f:
                if split_by_delimiter:
                    sql_buffer: list = []
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('--') or line.startswith('#'):
                            continue # skip empty lines and comments
                        sql_buffer.append(line)
                        if line.endswith(delimiter):
                            has_delimiter = True
                            query: str = ' '.join(sql_buffer).strip()
                        exec_query(conn, cur, query)
                        sql_buffer = [] # clear buffer for the next query
                elif not split_by_delimiter or not has_delimiter:
                    data = f.read()
                    query = '\n'.join([x for x in data.split('\n') if not x.startswith('--') and not x.startswith('#')])
                    exec_query(conn, cur, query)
            end = perf_counter()
        _logger.info(filepath)
        elapsed_time = end - start
        if os.path.isfile(output_file):
            sep = "\\" if platform.system == "Windows" else "/"
            if print_output:
                df = File.read_file(output_file)
                print(df)
                File.remove_file(output_file)
            else:
                print(f"Query result saved: {os.getcwd()}{sep}{output_file}")
        new_line = "\n" if print_output else ""
        if elapsed_time < 1:
            print(f"{new_line}Elapsed time: {elapsed_time:4.3f} s")
        else:
            print(f"{new_line}Elapsed time: {str(timedelta(seconds=elapsed_time)).split('.')[0]}")

    def record_batches(self, cursor, chunk_size: int = 10_000):
        """ Function returns generator class to return large amount of data in chunks. """

        while True:
            batch_rows = cursor.fetchmany(chunk_size)
            column_names = [col[0] for col in cursor.description]
            if not batch_rows:
                break
            yield pd.DataFrame(batch_rows, columns=column_names)

    def print_list_of_users(self, file):
        """ Function to print users on a screen. """

        if not file:
            print("No file has been passed. Exit.")
            sys.exit()
        data = File.read_file(self.output_file)
        print(data)
        # roles: list = [role for role in data['role_name']]
        # for role in roles:
        #     print(role)

    @staticmethod
    def drop_userObjects(url, username='', password=''):
        """ Truncate bimeisterdb.UserObjects table. """

        Auth = auth.Auth()
        user = User()
        if not username:
            username: str = input('Enter username: ')
        if not password:
            from getpass import getpass
            password: str = getpass('Enter password: ')
        url = Auth.url_validation(url)
        url = url if url else sys.exit()
        provider_id = Auth.get_providerId(url)
        user_access_token = Auth.get_user_access_token(url, username, password, provider_id)
        user_access_token = user_access_token if user_access_token else sys.exit()
        user.delete_user_objects(url, user_access_token)