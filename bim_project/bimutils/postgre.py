import logging
import os
import platform
import re
import sys
from collections.abc import Generator, Sequence
from datetime import timedelta, datetime
from getpass import getpass
from time import perf_counter
from pathlib import Path

import pandas as pd
import psycopg
import typer
from psycopg import errors

from mlogger import Logs
from tools import Tools



from psycopg.types.datetime import TimestampLoader, TimestamptzLoader

# Create custom loaders to translate PostgreSQL infinity to Python boundaries
class SafeTimestampLoader(TimestampLoader):
    def load(self, data: bytes) -> datetime:
        if data == b"infinity":
            return datetime.max
        if data == b"-infinity":
            return datetime.min
        return super().load(data)

class SafeTimestamptzLoader(TimestamptzLoader):
    def load(self, data: bytes) -> datetime:
        if data == b"infinity":
            return datetime.max.replace(tzinfo=datetime.timezone.utc)
        if data == b"-infinity":
            return datetime.min.replace(tzinfo=datetime.timezone.utc)
        return super().load(data)

# Register these globally so Psycopg 3 intercepts them automatically on all queries
psycopg.adapters.register_loader("timestamp", SafeTimestampLoader)
psycopg.adapters.register_loader("timestamptz", SafeTimestamptzLoader)


_logger = logging.getLogger(__name__)

class DB:

    __is_query_successful: bool = False

    def __init__(self):
        self._log = Logs()

    @classmethod
    def get_query_status(cls) -> bool:
        return cls.__is_query_successful
    
    @classmethod
    def set_query_status(cls, value: bool) -> bool:
        if isinstance(value, bool):
            cls.__is_query_successful = value
            return cls.__is_query_successful
        else:
            raise ValueError("Query status must be boolean!")

    def connect_to_db(self, **kwargs) -> psycopg.Connection | None:
        """Establishes a connection to the database using psycopg."""
        if not kwargs['password']:
            kwargs['password'] = getpass("Enter db password: ")
        try:
            conn = psycopg.connect(
                dbname=kwargs['db'],
                host=kwargs['host'],
                user=kwargs['user'],
                password=kwargs['password'],
                port=kwargs['port'],
                options="-c client_encoding=UTF8"
                                    )
        except errors.OperationalError as err:
            _logger.error(err)
            print(f"Database connection error.\n{err}")
        except errors.Error as err:
            _logger.error(err)
            print(self._log.err_message)
            return None
        else:
            return conn

    def get_output_filename(self, query_name: str) -> str | None:
        """Generates a safe CSV output filename based on the query name."""

        # Ensure name doesn't contain invalid characters for a filename
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', query_name)
        output_file = f"{safe_name.lower()}.csv"
        output_path = Path(output_file)

        # Safely clear out any old run's CSV file before writing fresh data
        if output_path.is_file():
            try:
                output_path.unlink(missing_ok=True)
            except OSError as err:
                print(f"Error removing old output file '{output_file}': {err}")
                print(f"Please manually delete {output_file} and try again.")
                return None
        return output_file

    def exec_query(
        self,
        conn: psycopg.Connection,
        query: str,
        output_file: str | bool = False,
        remove_output_file: bool = False,
        cursor: psycopg.Cursor | None = None,
        chunk_size: int = 10_000,
        params: Sequence | dict | None = None,
        header: bool = True,
        print_: bool = False,
        print_max: bool = False,
        fetch: bool = False,
        keep_conn: bool = False,
        print_elapsed_time: bool = False
    ) -> list[tuple] | tuple | bool | None:
        if not query:
            return None

        if remove_output_file and isinstance(output_file, str):
            try:
                Path(output_file).unlink(missing_ok=True)
            except OSError:
                print(self._log.err_message)

        is_external_cursor = cursor is not None
        start = perf_counter()

        is_read_query = query.strip().upper().startswith(("SELECT", "WITH", "SHOW", "EXPLAIN"))
        use_server_streaming = is_read_query

        created_internal_cursor = False

        try:
            if use_server_streaming:
                cursor = conn.cursor(name="streaming_cursor")
                created_internal_cursor = True
            elif not is_external_cursor:
                cursor = conn.cursor()

            cursor.execute(query, params or ())

            if fetch:
                return cursor.fetchone()

            if is_read_query and cursor.description:
                if not print_ and not print_max:
                    mode = 'w'
                    for chunk_df in self.record_batches(cursor, chunk_size=chunk_size):
                        chunk_df.to_csv(output_file, index=False, header=header, mode=mode)
                        header, mode = False, 'a'
                else:
                    if print_max:
                        pd.set_option('display.max_rows', None)    # Show all rows in chunk
                        pd.set_option('display.max_columns', None) # Show all columns
                        pd.set_option('display.width', None)       # Expand display width

                    total_printed_rows = 0
                    max_safe_print_rows = 100_000

                    for chunk_df in self.record_batches(cursor, chunk_size=chunk_size):
                        if not chunk_df.empty:
                            print(chunk_df)
                            total_printed_rows += len(chunk_df)

                        if total_printed_rows >= max_safe_print_rows:
                            print(f"\n⚠️  [Output Truncated: Result set exceeds the safe display limit of {max_safe_print_rows:,} rows]")
                            break
            else:
                if cursor.rowcount > 0:
                    print(f"Success: {cursor.rowcount} row(s) affected.")
                else:
                    print(f"Command executed successfully: {cursor.statusmessage}")

            self.set_query_status(True)
            conn.commit()

        except errors.SyntaxError as err:
            _logger.error(err)
            print(f"\n❌ SQL Syntax Error: {err}")
            return False
        except (errors.UndefinedTable, errors.InsufficientPrivilege) as err:
            _logger.error(err)
            print(f"Database constraint error: {err}")
            conn.rollback()
            return False
        except errors.ReadOnlySqlTransaction as err:
            _logger.error(err)
            print(f"Caught expected read-only transaction error: {err}")
        except errors.Error as err:
            conn.rollback()
            _logger.error(err)
            print(self._log.err_message)
            return False
        finally:
            end = perf_counter()
            if (not is_external_cursor or created_internal_cursor) and cursor:
                cursor.close()
            if not keep_conn and not is_external_cursor:
                conn.close()

            if self.get_query_status() and print_elapsed_time:
                elapsed_time = end - start
                if elapsed_time < 1:
                    print(f"Elapsed time: {elapsed_time:4.3f} s")
                else:
                    print(f"Elapsed time: {str(timedelta(seconds=elapsed_time)).split('.')}")

    def execute_query_from_file(self, conn: psycopg.Connection, **kwargs) -> None:
        """Executes query blocks from provided external files securely."""
        filepath = kwargs.get('filepath')
        if not filepath:
            print("Error: No file path provided.")
            return None
        file_path_obj = Path(filepath)
        if not file_path_obj.is_file():
            print(f"No such file: {file_path_obj.name}")
            return None

        # Generate a clean CSV output filename based on their SQL file's name
        output_file = self.get_output_filename(file_path_obj.stem)
        if not conn or not output_file:
            return None

        start = perf_counter()
        has_delimiter = False
        chunk_size = kwargs.get('chunk_size', 10_000)

        # Extract display preferences safely
        print_flag = kwargs.get('print_', False)
        print_max_flag = kwargs.get('print_max', False)
        should_display_on_screen = print_flag or print_max_flag

        try:
            with conn.cursor() as cursor:
                with open(filepath, 'r', encoding='utf-8') as f:
                    if kwargs.get('read_by_line'):
                        sql_buffer = []
                        for line in f:
                            cleaned_line = line.strip()
                            if not cleaned_line or cleaned_line.startswith(('--', '#')):
                                continue
                            sql_buffer.append(cleaned_line)

                            if cleaned_line.endswith(';'):
                                has_delimiter = True
                                query = ' '.join(sql_buffer).strip()
                                if query:
                                    self.exec_query(
                                        conn, query, output_file=output_file,
                                        cursor=cursor, chunk_size=chunk_size, keep_conn=True,
                                        print_=print_flag, print_max=print_max_flag
                                    )
                                    sql_buffer = []
                        if not has_delimiter:
                            print(f"No semicolon (;) found in {file_path_obj.name}\nCheck query syntax or remove '--read-by-line' flag, and try again!")
                            sys.exit(1)
                    else:
                        query = f.read()
                        self.exec_query(
                            conn, query, output_file=output_file,
                            cursor=cursor, chunk_size=chunk_size, keep_conn=True,
                            print_=print_flag, print_max=print_max_flag
                        )
        finally:
            conn.close()

        end = perf_counter()
        _logger.info(filepath)
        elapsed_time = end - start

        # Only display file save paths if the user DID NOT request a screen print
        if not should_display_on_screen and Path(output_file).is_file():
            sep = "\\" if platform.system() == "Windows" else "/"
            print(f"Query result saved: {os.getcwd()}{sep}{output_file}")

        new_line = "\n" if should_display_on_screen else ""
        if self.get_query_status():
            if elapsed_time < 1:
                print(f"{new_line}Elapsed time: {elapsed_time:4.3f} s")
            else:
                print(f"{new_line}Elapsed time: {str(timedelta(seconds=elapsed_time)).split('.')}")

    def record_batches(self, cursor: psycopg.Cursor, chunk_size: int) -> Generator[pd.DataFrame, None, None]:
        """Function returns generator class to return large amount of data in chunks."""
        while True:
            batch_rows = cursor.fetchmany(chunk_size)
            if not batch_rows:
                break
            column_names = [col.name for col in cursor.description] if cursor.description else []
            yield pd.DataFrame(batch_rows, columns=column_names)


class Queries:

    COUNT_MATVIEWS_SQL = """
        SELECT count(*) 
        FROM pg_catalog.pg_matviews 
        WHERE matviewname ILIKE %s;
    """

    LIST_MATVIEWS_SQL = """
        SELECT matviewname, schemaname 
        FROM pg_catalog.pg_matviews 
        WHERE matviewname ILIKE %s;
    """

    DROP_MATVIEW_SQL = "DROP MATERIALIZED VIEW IF EXISTS {};"

    @staticmethod
    def count_matviews(name: str, conn: psycopg.Connection) -> int | None:
        """Securely checks total materialized views matching a pattern."""
        db_instance = DB()
        result = db_instance.exec_query(
            conn, Queries.COUNT_MATVIEWS_SQL, params=(name,), fetch=True, keep_conn=True
        )
        if result and isinstance(result, tuple):
            return result[0]
        return None


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
    chunk_size: int = typer.Option(10_000, "--chunk-size", help="Adjust chunk size for pulling data"),
    read_by_line: bool = typer.Option("False", "--read-by-line", help="Read .sql file line-by-line"),
    print_: bool = typer.Option("False", "--print", help="Print dataframe preview to screen"),
    print_max: bool = typer.Option("False", '--print-max', help='Print full dataframe content')
        ):
    """Command to execute a user's local SQL query file in a given database."""

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
