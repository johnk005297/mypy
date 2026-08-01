import pandas as pd
import psycopg
from psycopg import errors
from psycopg.types.datetime import TimestampLoader, TimestamptzLoader
from rich.console import Console

import logging
import os
import platform
import re
from collections.abc import Generator, Sequence
from datetime import timedelta, datetime
from getpass import getpass
from time import perf_counter
from pathlib import Path

from common.mlogger import Logs
from . import queries

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
                options="-c client_encoding=UTF8",
                cursor_factory=psycopg.ClientCursor
                                    )
        except errors.OperationalError as err:
            _logger.error(err)
            print(f"Database connection error.\n{err}")
        except errors.Error as err:
            _logger.error(err)
            print(self._log.err_message)
            return None
        else:
            conn.prepare_threshold = None
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

        # Determine if we are actually writing data out to a physical CSV file
        should_stream_to_a_file = bool(output_file and isinstance(output_file, str))
        is_read_query = query.strip().upper().startswith(("SELECT", "WITH", "SHOW", "EXPLAIN"))

        # Only use a Server-Side named cursor if we are BOTH a read query AND saving to a file!
        use_server_streaming = should_stream_to_a_file and is_read_query

        created_internal_cursor = False
        try:
            self.set_query_status(False)
            if use_server_streaming:
                cursor = conn.cursor(name="streaming_cursor")
                created_internal_cursor = True
            elif not is_external_cursor:
                cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

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
                    max_safe_print_rows = 50_000

                    for chunk_df in self.record_batches(cursor, chunk_size=chunk_size):
                        if not chunk_df.empty:
                            print(chunk_df)
                            total_printed_rows += len(chunk_df)
                        if total_printed_rows > max_safe_print_rows:
                            print(f"\n⚠️  [Output Truncated: Result set exceeds the safe display limit of {max_safe_print_rows:,} rows]")
                            break
            else:
                if cursor.statusmessage and cursor.statusmessage.strip().upper() != "DO":
                    print(cursor.statusmessage)
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
            return False
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
                    print(f"Elapsed time: {str(timedelta(seconds=elapsed_time)).split('.')[0]}")

    def execute_query_from_file(self, conn: psycopg.Connection, **kwargs) -> None:
        """Executes query blocks from user-provided external files securely."""
        filepath = kwargs.get('filepath')
        if not filepath:
            print("Error: No file path provided.")
            return None
        file_path_obj = Path(filepath)
        if not file_path_obj.is_file():
            print(f"No such file: {file_path_obj.name}")
            return None

        output_file = self.get_output_filename(file_path_obj.stem)
        if not conn or not output_file:
            return None

        start = perf_counter()
        chunk_size = kwargs.get('chunk_size', 10_000)
        print_flag = kwargs.get('print_', False)
        print_max_flag = kwargs.get('print_max', False)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_lines = f.readlines()
            clean_lines = [
                line for line in raw_lines
                if line.strip() and not line.strip().startswith(('--', '#'))
            ]
            query = ''.join(clean_lines).strip()

            if not query:
                print(f"No valid SQL queries found inside {file_path_obj.name}")
                return None

            # Execute the clean query string using a plain, unified client cursor
            with Console().status(f"Query execution...", spinner="clock"):
                with conn.cursor() as cursor:
                    self.exec_query(
                        conn=conn,
                        query=query,
                        output_file=output_file,
                        cursor=cursor,
                        chunk_size=chunk_size,
                        keep_conn=True,
                        print_=print_flag,
                        print_max=print_max_flag
                    )
        finally:
            conn.close()
        end = perf_counter()
        _logger.info(filepath)
        elapsed_time = end - start

        should_display_on_screen = print_flag or print_max_flag
        if not should_display_on_screen and Path(output_file).is_file():
            sep = "\\" if platform.system() == "Windows" else "/"
            print(f"Query result saved: {os.getcwd()}{sep}{output_file}")

        new_line = "\n" if should_display_on_screen else ""
        if self.get_query_status():
            if elapsed_time < 1:
                print(f"{new_line}Elapsed time: {elapsed_time:4.3f} s")
            else:
                print(f"{new_line}Elapsed time: {str(timedelta(seconds=elapsed_time)).split('.')[0]}")

    def record_batches(self, cursor: psycopg.Cursor, chunk_size: int) -> Generator[pd.DataFrame, None, None]:
        """Function returns generator class to return large amount of data in chunks."""
        while True:
            batch_rows = cursor.fetchmany(chunk_size)
            if not batch_rows:
                break
            column_names = [col.name for col in cursor.description] if cursor.description else []
            yield pd.DataFrame(batch_rows, columns=column_names)


    @staticmethod
    def count_matviews(name: str, conn: psycopg.Connection) -> int | None:
        """Securely checks total materialized views matching a pattern."""
        db_instance = DB()
        result = db_instance.exec_query(
            conn, queries.COUNT_MATVIEWS_SQL, params=(name,), fetch=True, keep_conn=True
        )
        if result and isinstance(result, tuple):
            return result[0]
        return None