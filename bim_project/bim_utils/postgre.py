#
import psycopg2
import auth
import sys
import pandas as pd
from log import Logs
from user import User
from getpass import getpass


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

    def exec_query(self, conn, query=False, sql_file=False, out=False):
        """ Function executes passed query in DB. """

        cursor = conn.cursor()
        indent = ' ' * 4
        if sql_file:
            result_file = sql_file[:-3] + 'csv'
            with open(sql_file, 'r', encoding='utf-8') as file:
                query = file.read()
        if not sql_file and not query:
            return False
        try:
            cursor.execute(query)
            data = cursor.fetchall()
            columns = [x[0] for x in cursor.description]
            df = pd.DataFrame.from_records(data, columns=columns)
            if sql_file and out:
                print(df)
            elif sql_file:
                df.to_csv(result_file, index=False)
                self.__logger.info(f"Execute query:\n{query}".replace('\n', '\n' + indent))
                print(f"Query result saved in {result_file} file!")
            else:
                print(df)
        except psycopg2.ProgrammingError as err:
            self.__logger.error(err)
            print("SQL programming error. Check the log!")
            return False
        except psycopg2.DatabaseError as err:
            self.__logger.error(err.pgerror)
            print(err.pgerror)
            return False
        except psycopg2.Error as err:
            if err.pgcode == '42P01':
                print('Undefined table in the query.')
            print(err.pgerror)
            return False
        finally:
            conn.commit()
            cursor.close()
            conn.close()

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
    def get_matviews_list(cls):

        return """ select schemaname, matviewname, matviewowner from pg_catalog.pg_matviews
                   where matviewname  like 'sf_%';
                """

    @classmethod
    def drop_sf_materialized_view(cls):

        return """  
                    CREATE OR REPLACE FUNCTION sf_drop_materialized_view()
                    RETURNS void
                    LANGUAGE plpgsql
                    AS $$
                    DECLARE
                        view_record RECORD;
                    BEGIN
                        FOR view_record IN
                            SELECT schemaname, matviewname
                            FROM pg_matviews
                            WHERE matviewname LIKE 'sf_matview_%'
                        LOOP
                            EXECUTE 'DROP MATERIALIZED VIEW IF EXISTS '
                                    || quote_ident(view_record.schemaname) || '.' 
                                    || quote_ident(view_record.matviewname) 
                                    || ' CASCADE';
                        END LOOP;
                    END;
                    $$;

                    --select sf_drop_materialized_view();
             """
    
    @classmethod
    def refresh_sf_materialized_view(cls):

        return """
                    CREATE OR REPLACE FUNCTION sf_refresh_materialized_view()
                    RETURNS void
                    LANGUAGE plpgsql
                    AS $$
                    DECLARE
                        view_record RECORD;
                    BEGIN
                        FOR view_record IN
                            SELECT schemaname, matviewname
                            FROM pg_matviews
                            WHERE matviewname LIKE 'sf_matview_%'
                        LOOP
                            EXECUTE 'REFRESH MATERIALIZED VIEW '
                                    || quote_ident(view_record.schemaname) || '.'
                                    || quote_ident(view_record.matviewname);
                        END LOOP;
                    END;
                    $$;

                    select sf_refresh_materialized_view();
                """
    
    @classmethod
    def swith_externalKey_for_mdm_connector(cls, value=''):
        """ Query for switching ExternalKey. Requires for MDM connector integration. """

        return """
                    update "ExternalSystems" 
                    set "IsDefault" = false
                    from (
                        select "ExternalKey" as key from "ExternalSystems"
                        ) as get_key
                    where "ExternalKey" = get_key.key;

                    update "ExternalSystems" set "IsDefault" = true 
                    where "ExternalKey" = 'SDI-COD-{0}' ;

                    select "ExternalKey", "IsDefault" from "ExternalSystems" 
                    where "ExternalKey" = 'SDI-COD-{0}';
                """.format(value)
    
    @classmethod
    def get_list_of_all_db(cls):

        return """ select datname from pg_database; """