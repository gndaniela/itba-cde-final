import pymysql


conn = pymysql.connect(
        host= 'appdb.cdfnk5utunt6.us-east-1.rds.amazonaws.com', 
        port = 3306,
        user = 'admin', 
        password = 'adminPassw0rd!',
        db = 'appdb',
        )


#Tables Creation
cur=conn.cursor()
create_table="""
CREATE TABLE IF NOT EXISTS interactions (
    id INT(3) AUTO_INCREMENT PRIMARY KEY, 
    localteam VARCHAR(50) NOT NULL,
    awayteam VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
    )

"""
cur.execute(create_table)
conn.commit()

#Functions
#insert new row
def insert_row(localteam, awayteam):
    cur=conn.cursor()
    sql = "INSERT INTO interactions (localteam, awayteam) VALUES (%s,%s)"
    val = (localteam,awayteam)
    cur.execute(sql,val)
    conn.commit()

#get table details
def get_details():
    cur=conn.cursor()
    cur.execute("SELECT * FROM interactions")
    details = cur.fetchall()
    return details

