import typer

import sys

from .service import DB
from . import queries

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
    read_by_line: bool = typer.Option("False", "--read-by-line", "-rbl", help="Read .sql file line-by-line"),
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
    """Get list of materialized views by its name pattern. Default all."""
    pg = DB()
    sql_wildcard = search_pattern.replace('*', '%')
    pg.exec_query(
        conn=sql_context.conn, 
        query=queries.LIST_MATVIEWS_SQL,
        output_file="matviews-list.csv",
        remove_output_file=True,
        params=(sql_wildcard,),  # Secure tuple parameter delivery
        print_=print_
    )

@sql_app.command(name="drop-matviews")
@sql_app.command(name="drop-matview", hidden=True)
def drop_matviews(search_pattern: str = typer.Argument(..., help="Name pattern to search")):
    """Delete materialized views by its name pattern using a secure server loop."""
    pg = DB()
    pattern = search_pattern.replace('*', '%')

    # Count matching views before execution
    matviews_before = pg.count_matviews(pattern, sql_context.conn)
    if matviews_before == 0:
        print(f"Deleted: {matviews_before}")
        sql_context.conn.close()
        return

    terminate_script = queries.TERMINATE_MATVIEW_CONNECTIONS_SQL.format(pattern=pattern)
    pg.exec_query(sql_context.conn, terminate_script, keep_conn=True)

    drop_script = queries.DROP_MATVIEWS_CASCADE_SQL.format(pattern=pattern)
    pg.exec_query(sql_context.conn, drop_script, keep_conn=True)

    if not pg.get_query_status():
        sql_context.conn.close()
        sys.exit(1)

    # Count remaining views
    matviews_after = pg.count_matviews(pattern, sql_context.conn)

    print(f"Deleted: {matviews_before - matviews_after}")
    sql_context.conn.close()