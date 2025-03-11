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
from tools import Tools


class DB:
    __logger = Logs().f_logger(__name__)

    def __init__(self):
        pass

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

    ### DEPRECATED FUNCTION
    # def exec_query(self, conn, query):
    #     """ Function executes passed query in DB. """

    #     cursor = conn.cursor()
    #     data = None
    #     try:
    #         cursor.execute(query)
    #         data = cursor.fetchall()
    #         columns = [x[0] for x in cursor.description]
    #         df = pd.DataFrame.from_records(data, columns=columns)
    #         print(df)
    #     except psycopg2.ProgrammingError as err:
    #         if not data:
    #             self.__logger.info(f"Execute query: {cursor.statusmessage}")
    #             print(cursor.statusmessage)
    #             return True
    #         else:
    #             self.__logger.error(err)
    #             print("SQL programming error. Check the log!")
    #             return False
    #     except psycopg2.DatabaseError as err:
    #         self.__logger.error(err.pgerror)
    #         print(err.pgerror)
    #         return False
    #     except psycopg2.Error as err:
    #         if err.pgcode == '42P01':
    #             print('Undefined table in the query.')
    #         print(err.pgerror)
    #         return False
    #     finally:
    #         if conn:
    #             conn.commit()
    #             cursor.close()
    #             conn.close()
    #             print("Database connection closed.")

    def execute_query_in_batches(self, conn, sql_file=None, chunk_size: int = 10_000, sql_query=None):
        """Execute query in batches to optimize local memory usage"""

        def _record_batches():
            while True:
                batch_rows = cur.fetchmany(chunk_size)
                column_names = [col[0] for col in cur.description]
                if not batch_rows:
                    break
                yield pd.DataFrame(batch_rows, columns=column_names)

        if not conn:
            return False
        if sql_file:
            output_file = sql_file[:-3] + 'csv' if sql_file.find(' ') == -1 else 'query_result.csv'
            with open(sql_file, 'r', encoding='utf-8') as file:
                query = file.read()
        elif sql_query:
            output_file = 'query_result.csv'
            query = sql_query
        else:
            return False
        with conn.cursor() as cur:
            start = perf_counter()
            try:
                cur.execute(query)
                if cur.rowcount > 0:
                    header = True
                    mode = 'w'
                    for chunk in _record_batches():
                        chunk.to_csv(output_file, index=False, header=header, mode=mode)
                        if header:
                            header = False
                            mode = 'a'
            except psycopg2.ProgrammingError as err:
                if cur.rowcount == -1:
                    self.__logger.info(f"{cur}")
                    print(cur.statusmessage)
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
            conn.commit()
        end = perf_counter()
        elapsed_time = end - start
        if elapsed_time < 1:
            print(f"Elapsed time: {elapsed_time:4.3f} s")
        else:
            print(f"Elapsed time: {str(timedelta(seconds=elapsed_time)).split('.')[0]}")
        if cur.rowcount > 0:
            sep = "\\" if Tools.is_windows else "/"
            print(f"Query result saved in {os.getcwd()}{sep}{output_file} file!")

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
                  CREATE USER {0} WITH PASSWORD "{1}" IN ROLE pg_read_all_data;
                    ALTER USER {1} IN ROLE pg_read_all_data;
                """.format(name, password)