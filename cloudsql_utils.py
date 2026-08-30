import os
import mysql.connector

def get_db_connection():
    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASSWORD", "101519Ayad@%")
    db_name = os.getenv("DB_NAME", "mihna_agent")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = int(os.getenv("DB_PORT", "3306"))
    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME", "project-d699d925-921c-4e54-8c4:asia-south1:mihna-core-ay")

    socket_path = f"/cloudsql/{instance_connection_name}"

    if os.path.exists(socket_path):
        return mysql.connector.connect(
            user=db_user,
            password=db_pass,
            database=db_name,
            unix_socket=socket_path
        )
    else:
        return mysql.connector.connect(
            user=db_user,
            password=db_pass,
            database=db_name,
            host=db_host,
            port=db_port
        )
