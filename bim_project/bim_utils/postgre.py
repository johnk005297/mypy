#
import psycopg2
from getpass import getpass
import datetime

class DB:


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

        # if not filename:
        #     filename:str = input("Enter sql script file name: ")
        # if not host:
        #     host:str     = input("Enter db host name or IP: ")
        # if not database:
        #     database:str = input("Enter db name: ")
        # if not port:
        #     port:str     = input("Enter db port number: ")
        # if not user:
        #     user:str     = input("Enter db user name: ")
        # filename=None, host=None, database=None, port=None, user=None, password=None
        if not kwargs['password'] in kwargs:
            password:str = getpass("Enter password for database user: ")

        try:
            conn = psycopg2.connect(host=kwargs['host'],
                                    database=kwargs['database'],
                                    port=kwargs['port'],
                                    user=kwargs['user'],
                                    password=kwargs['password']
                                    )

        except psycopg2.Error as err:
            print(f"Database connection error.\n{err}")
            return False

        with conn.cursor() as cursor:
            try:
                cursor.execute(open(kwargs['filename'], "r").read()) 
                res = cursor.fetchall()
                for x in res:
                    print(x)
            except psycopg2.Error as err:
                if err.pgcode == '42P01':
                    print('UndefinedTable in the query.')
                print(err.pgerror)
                return False


        cursor.close()
        conn.close()