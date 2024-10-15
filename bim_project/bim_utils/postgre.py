#
import psycopg2
import auth
import sys
import csv
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
        except psycopg2.Error as err:
            print(f"Database connection error.\n{err}")
            return False
        else:
            return conn

    def exec_query(self, conn, query):
        """ Function executes passed query in DB. """

        cursor = conn.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            columns = [x[0] for x in cursor.description]
            for x in result:
                print(*x)
        except psycopg2.ProgrammingError:
            self.__logger.info(query)
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

    def exec_query_from_file(self, **kwargs):

        if not kwargs['password']:
            kwargs['password'] = getpass("Enter db password: ")
        try:
            conn = psycopg2.connect(database=kwargs['db'],
                                    host=kwargs['host'],
                                    user=kwargs['user'],
                                    password=kwargs['password'],
                                    port=kwargs['port']
                                    )

        except psycopg2.Error as err:
            print(f"Database connection error.\n{err}")
            return False

        with open(kwargs['file'], 'r', encoding='utf-8') as file:
            sql_query = file.read()

        with conn.cursor() as cursor:
            success_msg: str = "SQL query executed successfully!"
            try:
                # cursor.execute(open(kwargs['file'], "r").read())
                cursor.execute(sql_query)
                if cursor.description == None:
                    print("SQL query hasn't been executed.")
                    return False
                result = cursor.fetchall()

                # Extract the table headers
                headers = [i[0] for i in cursor.description]

                # Open CSV file for writing
                fileName: str = kwargs['file'][:-4] + '.csv'
                csvFile = csv.writer(open(fileName, 'w', newline=''),
                                    delimiter=',', lineterminator='\r\n',
                                    quoting=csv.QUOTE_ALL, escapechar='\\')

                # Add the header and data to the CSV file
                csvFile.writerow(headers)
                csvFile.writerows(result)
                print(success_msg)
                print(f"Result saved in {kwargs['file'][:-4]}_result.csv file!")

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
    def create_sf_materialized_view(cls):

        return """
                    CREATE OR REPLACE FUNCTION sf_drop_materialized_view()
                    RETURNS void AS $$

                    DECLARE
                        view_record RECORD;
                    BEGIN
                        FOR view_record IN
                            SELECT schemaname, matviewname
                            FROM pg_matviews
                            WHERE matviewname LIKE 'sf_%'
                        LOOP
                            EXECUTE 'DROP MATERIALIZED VIEW IF EXISTS '
                                    || quote_ident(view_record.schemaname) || '.'
                                    || quote_ident(view_record.matviewname)
                                    || ' CASCADE';
                        END LOOP;
                    END;
                    $$ LANGUAGE plpgsql; 
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

                    select sf_drop_materialized_view();
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