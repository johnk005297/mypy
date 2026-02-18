import typer
import pandas as pd
import psycopg2
from psycopg2 import errors

import logging
import sys
import os
import platform
import re
from getpass import getpass
from time import perf_counter
from datetime import timedelta

from tools import File, Tools
from mlogger import Logs

_logger = logging.getLogger(__name__)

class DB:

    __is_query_successful: bool = False

    def __init__(self):
        self._log = Logs()

    @classmethod
    def get_query_status(cls):
        return cls.__is_query_successful
    
    @classmethod
    def set_query_status(cls, value):
        if isinstance(value, bool):
            cls.__is_query_successful = value
            return cls.__is_query_successful
        else:
            raise ValueError("Query status suppose to be boolean!")

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
            output_file=False,
            remove_output_file=False,
            cursor=None,
            chunk_size=10_000,
            params=None,
            header=True,
            print_=False,
            fetch=False,
            keep_conn=False,
            print_elapsed_time=False):
        if not query:
            return None
        is_closed_connection: bool = True
        if remove_output_file and isinstance(output_file, str) and os.path.isfile(output_file):
            try:
                os.remove(output_file)
            except OSError as err:
                print(self._log.err_message)
        if not cursor:
            is_closed_connection = False
            cursor = conn.cursor()
        start = perf_counter()
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
        except errors.InsufficientPrivilege as err:
            _logger.error(err.pgerror)
            print(f"Error: Insufficient Privilege (SQLSTATE 42501). Details: {err}")
            conn.rollback()
            return False
        except errors.ProgrammingError as err:
            if cursor.rowcount in (0, -1):
                _logger.info(f"{cursor}")
                print(cursor.statusmessage)
                conn.commit()
                self.set_query_status(True)
            else:
                _logger.error(err)
                print(self._log.err_message)
                return None
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
            end = perf_counter()
            self.set_query_status(True)
            conn.commit()
        finally:
            if not is_closed_connection and not keep_conn:
                cursor.close()
                conn.close()
            if self.get_query_status() and print_elapsed_time:
                elapsed_time: float = end - start
                if elapsed_time < 1:
                    print(f"Elapsed time: {elapsed_time:4.3f} s")
                else:
                    print(f"Elapsed time: {str(timedelta(seconds=elapsed_time)).split('.')[0]}")
        if print_:
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

        with conn.cursor() as cursor:
            start = perf_counter()
            has_delimiter: bool = False
            with open(filepath, 'r', encoding='utf-8') as f:
                if kwargs['read_by_line']:
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
                else:
                    query = f.read()
                    self.exec_query(conn, query, output_file=output_file, cursor=cursor, chunk_size=kwargs['chunk_size'])
        cursor.close()
        conn.close()
        end = perf_counter()
        _logger.info(filepath)
        elapsed_time: float = end - start
        if os.path.isfile(output_file):
            sep = "\\" if platform.system == "Windows" else "/"
            if kwargs['print_'] or kwargs['print_max']:
                if kwargs['print_max']:
                    self.print_pd_dataframe_csv_file(output_file, print_max=True)
                else:
                    self.print_pd_dataframe_csv_file(output_file)
            else:
                print(f"Query result saved: {os.getcwd()}{sep}{output_file}")
        new_line = "\n" if kwargs['print_'] or kwargs['print_max'] else ""
        if self.get_query_status():
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
            try:
                os.remove(filepath)
            except FileNotFoundError:
                _logger.error(f"Error: {filepath} not found.")
            except PermissionError:
                _logger.error(f"Error: Permission denied to remove {filepath}.")
            except OSError as e:
                _logger.error(f"Error: {e.strerror} (Code: {e.errno})")

    def print_list_of_users(self, file) -> None:
        """ Function to print users on a screen. """

        if not file:
            print("No file has been passed. Exit.")
            sys.exit()
        data = File.read_file(self.output_file)
        roles: list = [role for role in data['role_name']]
        for role in roles:
            print(role)

    def get_query(self, filepath, **kwargs) -> str:
        """ Prepare query from provided sql file.
            Needs for certain .sql queries using multilines and more than one semicolons.
        """
        if not filepath or not self.is_query_file_exists(filepath):
            return None
        if kwargs and kwargs.get('search_pattern'):
            pattern = kwargs['search_pattern']
        else: 
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            file_data = f.read()
            query = '\n'.join([x for x in file_data.split('\n') if not x.startswith('--') and not x.startswith('#')]).format(pattern)
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
        if not result and not result[0]:
            return None
        return result[0]


# sql_app CLI
sql_app = typer.Typer(help="Execute sql query provided in a *.sql file, find/drop materialized views.")

class SQLContext:
    """Store shared DB connection parameters"""
    def __init__(self):
        self.host = None
        self.db = None
        self.user = None
        self.password = None
        self.port = None
        self.conn = None
        self.folder = None

# Create a context instance
sql_context = SQLContext()

@sql_app.callback()
def sql_callback(
    host: str = typer.Option(..., "--host", "-h", help="DB hostname or IP address"),
    db: str = typer.Option(..., "--db", "-d", help="Database name"),
    user: str = typer.Option(..., "--user", "-u", help="Username with access to db"),
    password: str = typer.Option(None, "--password", "-pw", help="Database user password"),
    port: int = typer.Option(5432, "--port", "-p", help="Database port")
                ):
    # Store parameters in context
    sql_context.host = host
    sql_context.db = db
    sql_context.user = user
    sql_context.password = password
    sql_context.port = port
    sql_context.folder = Tools.get_resourse_path('sql_queries')

    # validate connection
    pg = DB()
    sql_context.conn = pg.connect_to_db(
        host=host,
        port=port,
        db=db,
        user=user,
        password=password
        )
    if not sql_context.conn:
        sys.exit(1)

@sql_app.command()
def exec(
    filepath: str = typer.Option(..., "--file", "-f", help="Path to a file with sql query"),
    chunk_size: int = typer.Option(10_000, "--chunk-size", help="Adjust chunks of pulled data from database during select large amount of data"),
    read_by_line: bool = typer.Option("False", "--read-by-line", help="Read .sql file line by line delimited by semicolons. This flag forces to read all the data from .sql file'"),
    print_: bool = typer.Option("False", "--print", help="Print content of dataframe on a screen"),
    print_max: bool = typer.Option("False", '--print-max', help='Print full content of dataframe on a screen')
        ):
    """ Command to execute SQL query in a given database. """

    pg = DB()
    pg.execute_query_from_file(sql_context.conn, filepath=filepath, chunk_size=chunk_size, read_by_line=read_by_line, print_=print_, print_max=print_max)

@sql_app.command(name="get-matviews")
@sql_app.command(name="get-matview", hidden=True)
def get_matviews(
    search_pattern: str = typer.Argument(..., help="Name pattern to search"),
    print_: bool = typer.Option("False", "--print", help="Print content of dataframe on a screen")
                ):
    """ Get list of materialized views by it's name pattern. Default all. """

    pg = DB()
    query = pg.get_list_matviews_query(filepath=os.path.join(sql_context.folder, 'get_list_of_matviews.sql'))
    params: dict = {"name": search_pattern.replace('*', '%')}
    pg.exec_query(sql_context.conn, query, output_file="matviews-list.csv", remove_output_file=True, params=params, print_=print_)

@sql_app.command(name="drop-matviews")
@sql_app.command(name="drop-matview", hidden=True)
def drop_matviews(search_pattern: str = typer.Argument(..., help="Name pattern to search")):
    """ Delete materialized views by it's name pattern. Default all. """

    pg = DB()
    q = Queries()
    pattern = search_pattern.replace('*', '%')
    matviews_before: int = q.count_matviews(pattern, sql_context.conn)
    drop_matviews_query = pg.get_query(filepath=os.path.join(sql_context.folder, 'drop_matviews.sql'), search_pattern=pattern)
    pg.exec_query(sql_context.conn, drop_matviews_query, keep_conn=True)
    if not pg.get_query_status():
        sql_context.conn.close()
        sys.exit()
    matviews_after: int = q.count_matviews(pattern, sql_context.conn)
    print(f"Deleted: {matviews_before - matviews_after}")
    sql_context.conn.close()



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
