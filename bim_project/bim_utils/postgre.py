#
import psycopg2
from getpass import getpass
import argparse


class Parser:

    def __init__(self):
        pass

    def get_args(self):
        ''' Test function to parse args. '''

        # parser = argparse.ArgumentParser()
        # parser.parse_args()
        parser = argparse.ArgumentParser()
        parser.add_argument("myvalue", help="Printing the value.")

        args = parser.parse_args()
        print(args.myvalue)


class DB:

    def __init__(self):
        pass

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


        # if not kwargs.get('password', False):
        #     kwargs['password'] = getpass("Enter user's password for db user: ")

        mandatory_args:list = ['host', 'db', 'port', 'user', 'password', 'file']

        return
    
        for arg in mandatory_args:
            if arg not in kwargs.keys():
                print(f"Forgot to provide {arg}!")
                return False


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

        with conn.cursor() as cursor:
            try:
                cursor.execute(open(kwargs['file'], "r").read()) 
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
