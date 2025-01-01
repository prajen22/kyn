import streamlit as st
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Astra DB credentials from a configuration file or environment variables
from config import astra_client_id, astra_client_secret, astra_database_id, astra_app_name

# Function to connect to Cassandra database
def connect_db():
    cloud_config = {
        'secure_connect_bundle': 'secure-connect-cassandra-db.zip'  # Path to your secure connect bundle
    }
    cluster = Cluster(cloud=cloud_config, auth_provider=PlainTextAuthProvider(astra_client_id, astra_client_secret))
    session = cluster.connect()
    session.set_keyspace("system1")
    return session

# Function to create a table if it doesn't exist
def create_table_if_not_exists():
    session = connect_db()
    session.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            username text,
            password text
        )
    """)

# Function to insert a new user
def insert_user(username, password):
    session = connect_db()
    from uuid import uuid4
    user_id = uuid4()  # Generate a unique ID
    session.execute("INSERT INTO users (id, username, password) VALUES (%s, %s, %s)", (user_id, username, password))

# Function to retrieve all users
def fetch_users():
    session = connect_db()
    rows = session.execute("SELECT * FROM users")
    return rows

# Streamlit UI
st.title("Simple Streamlit Cassandra Test")

# Tab for inserting a new user
tab1, tab2 = st.tabs(["Insert User", "Fetch Users"])

with tab1:
    st.header("Insert New User")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Insert"):
        if username and password:
            create_table_if_not_exists()
            insert_user(username, password)
            st.success("User inserted successfully!")
        else:
            st.error("Please fill in both fields.")

with tab2:
    st.header("Fetch Users")
    if st.button("Fetch Users"):
        users = fetch_users()
        if users:
            st.write("ID | Username | Password")
            for user in users:
                st.write(f"{user.id} | {user.username} | {user.password}")
        else:
            st.write("No users found.")