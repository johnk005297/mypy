#
import psycopg2
import auth
import sys
import os
import pandas as pd
from log import Logs
from user import User
from getpass import getpass
from time import perf_counter
from datetime import timedelta
from tools import Tools, File


class DB:
    __logger = Logs().f_logger(__name__)

    def __init__(self):
        self.output_file = 'query_result.csv'

    def connect_to_db(self, **kwargs):
        """ Function for establishing connection to db. """

        if not kwargs['password']:
            kwargs['password'] = getpass("Enter db password: ")
        try:
            conn = psycopg2.connect(database=kwargs['db'],
                                    host=kwargs['host'],
                                    user=kwargs['user'],
                                    password=kwargs['password'],
                                    port=kwargs['port']
                                    )
        except psycopg2.OperationalError as err:
            self.__logger.error(err)
            print(f"Database connection error.\n{err}")
        except psycopg2.Error as err:
            self.__logger.error(err)
            print("Error occured. Check the log!")
            return False
        else:
            return conn

    def execute_query_from_file(self, conn, filepath=None):
        """ Execute query from the file. """

        if not conn:
            return None
        if not os.path.isfile(filepath):
            print(f"No such file: {os.path.basename(filepath)}")
            return None
        else:
            file = os.path.basename(filepath).replace(' ', '_')
            filename_without_ext = os.path.splitext(filepath)[0]
            output_file = filename_without_ext + '.csv'
        delimiter = ';'
        # remove output file if it exists
        if os.path.isfile(output_file):
            try:
                os.remove(output_file)
            except OSError as err:
                print(f"Error removing file '{output_file}': {err}")
                print(f"Remove the file {output_file} and try again!")
                return None
        with conn.cursor() as cur:
            start = perf_counter()
            with open(file, 'r', encoding='utf-8') as f:
                sql_buffer: list = []
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('--') or line.startswith('#'):
                        continue # skip empty lines and comments
                    sql_buffer.append(line)
                    if line.endswith(delimiter):
                        query: str = ' '.join(sql_buffer).strip()
                        if query:
                            try:
                                cur.execute(query)
                                conn.commit()
                                if cur.rowcount > 0:
                                    if not os.path.isfile(output_file):
                                        header, mode = True, 'w'
                                    else:
                                        header, mode = False, 'a'
                                    for chunk in self.record_batches(cur):
                                        chunk.to_csv(output_file, index=False, header=header, mode=mode)
                                        header, mode = False, 'a'
                            except psycopg2.ProgrammingError as err:
                                if cur.rowcount == -1:
                                    self.__logger.info(f"{cur}")
                                    print(cur.statusmessage)
                                    conn.commit()
                                else:
                                    self.__logger.error(err)
                                    print("SQL programming error. Check the log!")
                            except psycopg2.errors.ReadOnlySqlTransaction as err:
                                self.__logger.error(err.pgerror)
                                print("ReadOnlySqlTransaction: cannot execute INSERT in a read-only transaction")
                                return False
                            except psycopg2.DatabaseError as err:
                                self.__logger.error(err.pgerror)
                                print(err.pgerror)
                                return False
                            except psycopg2.InterfaceError as err:
                                self.__logger.error(err.pgerror)
                                print(err.pgerror)
                                return False
                            except psycopg2.Error as err:
                                if err.pgcode == '42P01':
                                    print('Undefined table in the query.')
                                print(err.pgerror)
                                return False
                            finally:
                                sql_buffer = [] # clear buffer for next query
        end = perf_counter()
        elapsed_time = end - start
        if elapsed_time < 1:
            print(f"Elapsed time: {elapsed_time:4.3f} s")
        else:
            print(f"Elapsed time: {str(timedelta(seconds=elapsed_time)).split('.')[0]}")
        if os.path.isfile(output_file):
            sep = "\\" if Tools.is_windows else "/"
            print(f"Query result saved in {os.getcwd()}{sep}{output_file} file!")

    def record_batches(self, cursor, chunk_size: int = 10_000):
        while True:
            batch_rows = cursor.fetchmany(chunk_size)
            column_names = [col[0] for col in cursor.description]
            if not batch_rows:
                break
            yield pd.DataFrame(batch_rows, columns=column_names)
        

    def execute_query(self, conn, query=None, query_name=None):
        """Execute passed query ."""

        if not conn or not query or not query_name:
            return False
        output_file: str = query_name + '.csv'
        # remove output file if it exists
        if os.path.isfile(output_file) and query_name:
            try:
                os.remove(output_file)
            except OSError as err:
                print(f"Error removing file '{output_file}': {err}")
                print(f"Remove the file {output_file} and try again!")
                return None
        with conn.cursor() as cur:
            start = perf_counter()
            try:
                cur.execute(query)
                conn.commit()
                if cur.rowcount > 0:
                    header, mode = True, 'w'
                    for chunk in self.record_batches(cur):
                        chunk.to_csv(output_file, index=False, header=header, mode=mode)
                        header, mode = False, 'a'
            except psycopg2.ProgrammingError as err:
                if cur.rowcount == -1:
                    self.__logger.info(f"{cur}")
                    print(cur.statusmessage)
                    conn.commit()
                else:
                    self.__logger.error(err)
                    print("SQL programming error. Check the log!")
            except psycopg2.errors.ReadOnlySqlTransaction as err:
                self.__logger.error(err.pgerror)
                print("ReadOnlySqlTransaction: cannot execute INSERT in a read-only transaction")
                return False
            except psycopg2.DatabaseError as err:
                self.__logger.error(err.pgerror)
                print(err.pgerror)
                return False
            except psycopg2.InterfaceError as err:
                self.__logger.error(err.pgerror)
                print(err.pgerror)
                return False
            except psycopg2.Error as err:
                if err.pgcode == '42P01':
                    print('Undefined table in the query.')
                print(err.pgerror)
                return False
        end = perf_counter()
        elapsed_time = end - start
        if elapsed_time < 1:
            print(f"Elapsed time: {elapsed_time:4.3f} s")
        else:
            print(f"Elapsed time: {str(timedelta(seconds=elapsed_time)).split('.')[0]}")
        if os.path.isfile(output_file):
            sep = "\\" if Tools.is_windows() else "/"
            print(f"Query result saved in {os.getcwd()}{sep}{output_file} file!")

    def print_list_of_users(self, file):
        """ Function to print users on a screen. """

        if not file:
            print("No file has been passed. Exit.")
            sys.exit()
        data = File.read_file(self.output_file)
        roles: list = [role for role in data['role_name']]
        for role in roles:
            print(role)

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


class Queries:

    @classmethod
    def get_matviews_list(cls, name='%'):

        return """ select schemaname, matviewname, matviewowner from pg_catalog.pg_matviews
                   where matviewname  like '{0}';
                """.format(name.replace('*', '%'))

    @classmethod
    def drop_materialized_view(cls, name='%'):

        return """ 
                    DO $$
                    DECLARE
                        view_record RECORD;
                    BEGIN
                        FOR view_record IN
                            SELECT schemaname, matviewname
                            FROM pg_matviews
                            WHERE matviewname LIKE '{0}'
                        LOOP
                            EXECUTE 'DROP MATERIALIZED VIEW IF EXISTS '
                                    || quote_ident(view_record.schemaname) || '.'
                                    || quote_ident(view_record.matviewname)
                                    || ' CASCADE';
                        END LOOP;
                    END;
                    $$;
                    select matviewname from pg_catalog.pg_matviews;
        """.format(name.replace('*', '%'))

    @classmethod
    def refresh_materialized_view(cls, name='%'):

        return """
                    DO $$
                    DECLARE
                        view_record RECORD;
                    BEGIN
                        FOR view_record IN
                            SELECT schemaname, matviewname
                            FROM pg_matviews
                            WHERE matviewname LIKE '{0}'
                        LOOP
                            EXECUTE 'REFRESH MATERIALIZED VIEW '
                                    || quote_ident(view_record.schemaname) || '.'
                                    || quote_ident(view_record.matviewname);
                        END LOOP;
                    END;
                    $$;
                    select matviewname from pg_catalog.pg_matviews where matviewname LIKE '{0}';
                """.format(name.replace('*', '%'))

    @classmethod
    def swith_externalKey_for_mdm_connector(cls, value=''):
        """ Query for switching ExternalKey. Requires for MDM connector integration. 
            Query applies in data_synchronizer_db.
        """

        return """
                    update "ExternalSystems" 
                    set "IsDefault" = false
                    from 
                        ( select "Id" as id from "ExternalSystems" ) as extSysObjId
                    where "Id" = extSysObjId.id;

                    update "ExternalSystems" set "IsDefault" = true 
                    where "ExternalKey" = 'SDI-COD-{0}' ;

                    select "ExternalKey", "IsDefault" from "ExternalSystems" 
                    where "ExternalKey" = 'SDI-COD-{0}';
                """.format(value)

    @classmethod
    def get_list_of_all_db(cls):
        """ Get list of all databases. """

        return """ select datname from pg_database; """

    @classmethod
    def get_list_of_db_tables(cls):
        """ Get list of tables for a given database. """

        return """ 
                    SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public';
                """
    
    @classmethod
    def create_postgresql_user_ro(cls, name, password):
        """ Create postgreSQL user with read only access. """

        return """
                  CREATE USER {0} WITH PASSWORD '{1}' IN ROLE pg_read_all_data;
                    GRANT pg_read_all_data TO {0};
                """.format(name, password)
    
    @classmethod
    def get_list_of_users(cls):
        """ Get list of all DB users. """

        return """
                SELECT usename AS role_name,
                    CASE
                        WHEN usesuper AND usecreatedb THEN
                        CAST('superuser, create database' AS pg_catalog.text)
                        WHEN usesuper THEN
                            CAST('superuser' AS pg_catalog.text)
                        WHEN usecreatedb THEN
                            CAST('create database' AS pg_catalog.text)
                        ELSE
                            CAST('' AS pg_catalog.text)
                    END role_attributes
                FROM pg_catalog.pg_user
                ORDER BY role_name desc;
                """
