#
import psycopg2
import csv

class DB:

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

        with conn.cursor() as cursor:
            try:
                cursor.execute(open(kwargs['file'], "r").read()) 
                result = cursor.fetchall()

                # Extract the table headers
                headers = [i[0] for i in cursor.description]

                # Open CSV file for writing
                fileName:str = kwargs['file'][:-4] + '.csv'
                csvFile = csv.writer(open(fileName, 'w', newline=''),
                                    delimiter=',', lineterminator='\r\n',
                                    quoting=csv.QUOTE_ALL, escapechar='\\')
                
                # Add the header and data to the CSV file
                csvFile.writerow(headers)
                csvFile.writerows(result)                

            except psycopg2.DatabaseError as err:
                print(err.pgerror)

            except psycopg2.Error as err:
                if err.pgcode == '42P01':
                    print('Undefined table in the query.')
                print(err.pgerror)
                return False

            finally:
                cursor.close()
                conn.close()

