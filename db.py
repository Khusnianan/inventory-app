import psycopg2

def get_connection():
    return psycopg2.connect(
        host="your-host",
        database="your-db-name",
        user="your-username",
        password="your-password",
        port="your-port"
    )
