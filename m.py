import mysql.connector

def test():
    db_connection = mysql.connector.connect(
            
        host = '172.17.0.2', # for linux db
        port = '3306',
        database = 'clients',
        user = 'root',
        password = 'root',
        auth_plugin='mysql_native_password'
    )     
    cursor = db_connection.cursor()

    if not db_connection.is_connected():
        print("No connection")  
        
    cur = db_connection.cursor()
    cur.execute("delete from organizations where org_id = 1")
    db_connection.commit()
    # result = cur.fetchall()
    # for x in result:
    #     print(x)

test()