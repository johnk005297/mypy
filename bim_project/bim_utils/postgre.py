#
import psycopg2
import auth
import sys
import csv
from log import Logs
from user import User


class DB:
    __logger = Logs().f_logger(__name__)

    def __init__(self):
        pass

    @staticmethod
    def pp(cursor, data=None, rowlens=0):
        d = cursor.description
        if not d:
            return "#### NO RESULTS ###"
        names = []
        lengths = []
        rules = []
        if not data:
            data = cursor.fetchall()
        for dd in d:    # iterate over description
            l = dd[1]
            if not l:
                l = 12             # or default arg ...
            l = max(l, len(dd[0])) # Handle long names
            names.append(dd[0])
            lengths.append(l)
        for col in range(len(lengths)):
            if rowlens:
                rls = [len(row[col]) for row in data if row[col]]
                lengths[col] = max([lengths[col]]+rls)
            rules.append("-"*lengths[col])
        format = " ".join(["%%-%ss" % l for l in lengths])
        result = [format % tuple(names)]
        result.append(format % tuple(rules))
        for row in data:
            result.append(format % row)
        return "\n".join(result)


    def exec_query(self):

        conn = psycopg2.connect(host='10.169.123.133',
                                database='authdb',
                                port='10265',
                                user='bimauth',
                                password='dbpass',
                                )
        
        cursor = conn.cursor()
        query = "select * from \"AspNetUsers\" where \"UserName\" = 'admin'"
        cursor.execute(query)
        res = cursor.fetchall()
        column_names = [x[0] for x in cursor.description]
        print(column_names)

        cursor.close()
        conn.close()

    def exec_query_from_file(self, **kwargs):

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
