import psycopg2

class DataBaseManager:
    def __init__(self, host, port, database, user, password):
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        self.cursor = self.conn.cursor()

    def create_table(self, table_name, columns):
        """
        Creates a new table in the database.
        
        Parameters:
        table_name (str): Name of the table to create.
        columns (dict): Dictionary where keys are column names and values are column data types.
        """
        column_def = ", ".join([f"{name} {data_type}" for name, data_type in columns.items()])
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({column_def})")
        self.conn.commit()

    def get_all_data(self, table_name):
        """
        Retrieves all data from a table.
        
        Parameters:
        table_name (str): Name of the table to retrieve data from.
        
        Returns:
        list: List of tuples, where each tuple represents a row of data.
        """
        self.cursor.execute(f"SELECT * FROM {table_name}")
        return self.cursor.fetchall()

    def append_data(self, table_name, data):
        """
        Appends data to a table.
        
        Parameters:
        table_name (str): Name of the table to append data to.
        data (dict): Dictionary where keys are column names and values are the data to insert.
        """
        columns = ", ".join(data.keys())
        values = ", ".join(["%s" for _ in data])
        self.cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({values})", tuple(data.values()))
        self.conn.commit()