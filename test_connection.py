from sqlalchemy import create_engine

# Replace this with the path to your database
engine = create_engine("sqlite:///./books.db")
try:
    connection = engine.connect()
    print("Connection successful")
except Exception as e:
    print("Connection failed:", e)
finally:
    connection.close()
