ACCESS_TOKEN_EXPIRE_MINUTES = 100
SECRET_KEY = "Vitthal"
SQLALCHEMY_DATABASE_URL = (
    "mysql+pymysql://{user}:{password}@{host}:{port}/{database}".format(
        user="<root>",
        password="<password>",
        host="localhost",
        port=3306,
        database="<databaseName>",
    )
)

OPEN_AI_KEY = "YourKey"
