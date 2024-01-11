import pymysql
pymysql.install_as_MySQLdb()

import mysql.connector

class MySQLNoDuplicatesPipeline:

    def __init__(self):
        self.conn = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            password = '',
            database = 'flask_scrapper_jobs'
        )

        ## Create cursor, used to execute commands
        self.cur = self.conn.cursor()
        
        ## Create quotes table if none exists
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS indeed_jobs(
            id int NOT NULL auto_increment, 
            content text,
            tags text,
            author VARCHAR(255),
            PRIMARY KEY (id)
        )
        """)

    def process_item(self, item, spider):

        ## Check to see if text is already in database 
        self.cur.execute("select * from indeed_jobs where content = %s", (item['text'],))
        result = self.cur.fetchone()

        ## If it is in DB, create log message
        if result:
            spider.logger.warn("Item already in database: %s" % item['text'])


        ## If text isn't in the DB, insert data
        else:

            ## Define insert statement
            self.cur.execute(""" insert into indeed_jobs (content, tags, author) values (%s,%s,%s)""", (
                item["text"],
                str(item["tags"]),
                item["author"]
            ))

            ## Execute insert of data into database
            self.connection.commit()
        return item

    
    def close_spider(self, spider):

        ## Close cursor & connection to database 
        self.cur.close()
        self.conn.close()

