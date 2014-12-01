from sqlalchemy import Table,Column,Integer,String,MetaData,DateTime,ForeignKey

"""
Schema used by the DB to handle content exchange.
"""
metadata = MetaData()
computers = Table('computers', metadata,
                Column('computername', String, primary_key=True),
                Column('status', Integer),
                Column('update0', DateTime),
                Column('update1', DateTime), 
                Column('is_mac', Integer),  
)
resources = Table('resources', metadata,
                Column('resource', String, primary_key=True),
                Column('count', Integer),
                Column('timestamp', String),
)
