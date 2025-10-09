import logging
import sys
import os
import platform
import re
import pandas as pd
import psycopg2
from psycopg2 import errors
from getpass import getpass
from time import perf_counter
from datetime import timedelta
from tools import File
from mlogger import Logs

_logger = logging.getLogger(__name__)

class DB:

    _successful_query: bool = False

    def __init__(self):
        self._log = Logs()

    def connect_to_db(self, **kwargs):
        """ Function for establishing connection to db. """

        if not kwargs['password']:
            kwargs['password'] = getpass("Enter db password: ")
        try:
            conn = psycopg2.connect(
                database=kwargs['db'],
                host=kwargs['host'],
                user=kwargs['user'],
                password=kwargs['password'],
                port=kwargs['port']
                                    )
        except errors.OperationalError as err:
            _logger.error(err)
            print(f"Database connection error.\n{err}")
        except psycopg2.Error as err:
            _logger.error(err)
            print(self._log.err_message)
            return False
        else:
            return conn

    def is_query_file_exists(self, filepath) -> bool:
        """ Check if sql query file exists. """
        if not os.path.isfile(filepath):
            print(f"No such file: {os.path.basename(filepath)}")
            return False
        else: return True

    def get_output_filename(self, filepath) -> str:
        """ Check for result output file name. """

        if not self.is_query_file_exists(filepath):
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

    def exec_query(
            self,
            conn,
            query,
            output_file=None,
            remove_output_file=False,
            cursor=None,
            chunk_size=10_000,
            params=None,
            header=True,
            print=False,
            fetch=False,
            keep_conn=False):
        if not query:
            return None
        is_closed_connection: bool = True
        if remove_output_file and os.path.isfile(output_file):
            try:
                os.remove(output_file)
            except OSError as err:
                print(self._log.err_message)
        if not cursor:
            is_closed_connection = False
            cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if fetch:
                result = cursor.fetchone()
                return result
            if cursor.rowcount > 0:
                mode = 'w' if not os.path.isfile(output_file) else 'a'
                for chunk in self.record_batches(cursor, chunk_size=chunk_size):
                    chunk.to_csv(output_file, index=False, header=header, mode=mode)
                    header, mode = False, 'a'
        except errors.UndefinedTable as err:
            _logger.error(err)
            print(err)
            return False
        except errors.ProgrammingError as err:
            if cursor.rowcount in (0, -1):
                _logger.info(f"{cursor}")
                print(cursor.statusmessage)
                conn.commit()
                self._successful_query = True
            else:
                _logger.error(err)
                print(self._log.err_message)
        except errors.ReadOnlySqlTransaction as err:
            _logger.error(err.pgerror)
            print(f"Error: {err}")
            return False
        except errors.DatabaseError as err:
            _logger.error(err.pgerror)
            conn.rollback()
            print(err.pgerror)
            return False
        except errors.InterfaceError as err:
            _logger.error(err.pgerror)
            conn.rollback()
            print(err.pgerror)
            return False
        except errors.IntegrityError as err:
            conn.rollback()
            _logger.error(err)
            print(self._log.err_message)
            return False
        except errors.Error as err:
            conn.rollback()
            print(err)
            return False
        else:
            self._successful_query = True
            conn.commit()
        finally:
            if not is_closed_connection and not keep_conn:
                cursor.close()
                conn.close()
        if print:
            self.print_pd_dataframe_csv_file(output_file)

    def execute_query_from_file(self, conn, **kwargs):
        """ Execute query from the file. """

        if kwargs['filepath']:
            filepath: str = kwargs['filepath']
        else:
            return None
        if not self.is_query_file_exists(filepath):
            return None
        output_file: str = self.get_output_filename(filepath)
        if not conn or not output_file:
            return None
        has_delimiter: bool = False
        with conn.cursor() as cursor:
            start = perf_counter()
            with open(filepath, 'r', encoding='utf-8') as f:
                if kwargs['read_all']:
                    file_data = f.read()
                    query = '\n'.join([x for x in file_data.split('\n') if not x.startswith('--') and not x.startswith('#')])
                    self.exec_query(conn, query, output_file=output_file, cursor=cursor, chunk_size=kwargs['chunk_size'])
                else:
                    sql_buffer: list = []
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('--') or line.startswith('#'):
                        continue # skip empty lines and comments
                    sql_buffer.append(line)
                    if line.endswith(';'):
                        has_delimiter = True
                        query: str = ' '.join(sql_buffer).strip()
                        if query:
                            self.exec_query(conn, query, output_file=output_file, cursor=cursor, chunk_size=kwargs['chunk_size'])
                            sql_buffer = [] # clear buffer for next query
                if not has_delimiter:
                    print(f"No semicolon(;) symbol was found in {os.path.basename(filepath)}\nCheck query syntax or use '--read-all' flag, and try again!")
                    sys.exit()
        cursor.close()
        conn.close()
        end = perf_counter()
        _logger.info(filepath)
        elapsed_time = end - start
        if os.path.isfile(output_file):
            sep = "\\" if platform.system == "Windows" else "/"
            if kwargs['print'] or kwargs['print_max']:
                if kwargs['print_max']:
                    self.print_pd_dataframe_csv_file(output_file, print_max=True)
                else:
                    self.print_pd_dataframe_csv_file(output_file)
            else:
                print(f"Query result saved: {os.getcwd()}{sep}{output_file}")
        new_line = "\n" if kwargs['print'] or kwargs['print_max'] else ""
        if self._successful_query:
            if elapsed_time < 1:
                print(f"{new_line}Elapsed time: {elapsed_time:4.3f} s")
            else:
                print(f"{new_line}Elapsed time: {str(timedelta(seconds=elapsed_time)).split('.')[0]}")

    def record_batches(self, cursor, chunk_size):
        """ Function returns generator class to return large amount of data in chunks. """
        while True:
            batch_rows = cursor.fetchmany(chunk_size)
            column_names = [col[0] for col in cursor.description]
            if not batch_rows:
                break
            yield pd.DataFrame(batch_rows, columns=column_names)

    def print_pd_dataframe_csv_file(self, filepath, print_max=False):
        """ Print .csv file content. """
        try:
            df = File.read_file(filepath)
            if print_max:
                pd.set_option('display.max_rows', None)  # Display all rows
                pd.set_option('display.max_columns', None) # Display all columns
                pd.set_option('display.width', None) # Adjust width for better display of wide data
            if not isinstance(df, bool) and not df.empty:
                print(df)
        except pd.errors.ParserError as err:
            _logger.error(err)
            print(f"Can't print output because it contains more than one SELECT results.")
        except Exception as err:
            _logger.error(err)
            print(self._log.err_message)
        else:
            File.remove_file(filepath)

    def print_list_of_users(self, file):
        """ Function to print users on a screen. """

        if not file:
            print("No file has been passed. Exit.")
            sys.exit()
        data = File.read_file(self.output_file)
        roles: list = [role for role in data['role_name']]
        for role in roles:
            print(role)

    def get_drop_matviews_query(self, filepath, **kwargs) -> str:
        """ Prepare query from drop matview sql file. """
        if not filepath or not self.is_query_file_exists(filepath):
            return None
        if kwargs and kwargs.get('name'):
            matview_name = kwargs['name']
        else: 
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            file_data = f.read()
            query = '\n'.join([x for x in file_data.split('\n') if not x.startswith('--') and not x.startswith('#')]).format(matview_name)
            return query

    def get_list_matviews_query(self, filepath) -> str:
        """ List matviews by provided name pattern. """
        if not filepath or not self.is_query_file_exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            file_data = f.read()
            query = '\n'.join([x for x in file_data.split('\n') if not x.startswith('--') and not x.startswith('#')])
        return query


class Queries:
    @staticmethod
    def count_matviews(name, conn) -> str:
        query: str = "select count(*) from pg_catalog.pg_matviews where matviewname ilike '{0}';".format(name)
        result = DB.exec_query(DB, conn, query, fetch=True, keep_conn=True)
        return result[0]

    # DEPRECATED MODULE
    # @staticmethod
    # def drop_userObjects(url, username='', password=''):
    #     """ Truncate bimeisterdb.UserObjects table. """

    #     Auth = auth.Auth()
    #     user = User()
    #     if not username:
    #         username: str = input('Enter username: ')
    #     if not password:
    #         from getpass import getpass
    #         password: str = getpass('Enter password: ')
    #     url = Auth.url_validation(url)
    #     url = url if url else sys.exit()
    #     provider_id = Auth.get_providerId(url)
    #     user_access_token = Auth.get_user_access_token(url, username, password, provider_id)
    #     user_access_token = user_access_token if user_access_token else sys.exit()
    #     user.delete_user_objects(url, user_access_token)
