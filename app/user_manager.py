import hashlib
import psycopg2
import os
from dotenv import load_dotenv
from app.exceptions import UserNotFoundError

load_dotenv()


class UserManager:
    def __init__(self, db_config):
        # Establish database connection
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()

    def register_user(self, username, password):
        
        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            # Insert user into the users table
            insert_query = "INSERT INTO users (username, password_hash) VALUES (%s, %s);"
            self.cursor.execute(insert_query, (username, hashed_password))
            self.conn.commit()
            return "User registered successfully"
        except psycopg2.IntegrityError:
            self.conn.rollback()
            return "Username already exists"

    def login(self, username: str, password: str):
        """
        Tries to login with the username and password
        Password is stored in sha256 format
        Returns login successful Invalid credentials
        """
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Query to check if the user exists and validate the password
        select_query = "SELECT password_hash FROM users WHERE username = %s;"
        self.cursor.execute(select_query, (username,))
        result = self.cursor.fetchone()

        if result:
            stored_password = result[0]
            if stored_password == hashed_password:
                return "Login successful"
        else:
            raise UserNotFoundError
    def remove_user(self, username):
        # Delete user from the users table
        delete_query = "DELETE FROM users WHERE username = %s;"
        self.cursor.execute(delete_query, (username,))
        if self.cursor.rowcount > 0:
            self.conn.commit()
            return "User removed successfully"
        else:
            self.conn.rollback()
            return "User not found"

    def close_connection(self):
        # Close cursor and connection
        self.cursor.close()
        self.conn.close()


if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': os.environ.get("DB_ENDPOINT"),
        'dbname': os.environ.get("DB_NAME"),
        'user': os.environ.get("DB_USERNAME"),
        'password': os.environ.get("DB_PASSWORD"),
        'port': os.environ.get("DB_PORT")
    }

    user_manager = UserManager(db_config)
    print(user_manager.register_user("testrobert", "testlösen"))
    print(user_manager.login("testrobert", "testlösen"))
    #print(user_manager.remove_user("alice"))
    user_manager.close_connection()
