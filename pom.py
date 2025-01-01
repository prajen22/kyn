import streamlit as st
from cassandra.cluster import Cluster

# Connect to Cassandra
cluster = Cluster(["127.0.0.1"])  # Replace with your Cassandra IP
session = cluster.connect()

# Initialize keyspace and tables for global data
def initialize_global_keyspace():
    session.execute("""
    CREATE KEYSPACE IF NOT EXISTS global_events 
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
    """)
    session.set_keyspace("global_events")
    
    session.execute("""
    CREATE TABLE IF NOT EXISTS global_events (
        event_name TEXT PRIMARY KEY,
        event_time TEXT,
        event_type TEXT,
        location TEXT
    );
    """)

# Initialize user-specific keyspace
def initialize_user_keyspace(username):
    session.execute(f"""
    CREATE KEYSPACE IF NOT EXISTS {username} 
    WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
    """)
    session.set_keyspace(username)
    session.execute("""
    CREATE TABLE IF NOT EXISTS profile (
        name TEXT PRIMARY KEY,
        password TEXT,
        location TEXT
    );
    """)
    session.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        name TEXT,
        event_name TEXT,
        event_time TEXT,
        location TEXT,
        PRIMARY KEY (name, event_name)
    );
    """)
    session.execute("""
    CREATE TABLE IF NOT EXISTS preferences (
        name TEXT,
        event_name TEXT,
        event_time TEXT,
        event_type TEXT,
        location TEXT,
        PRIMARY KEY (name, event_name)
    );
    """)

# Populate events
def populate_events():
    session.set_keyspace("global_events")
    events = [
        {"event_name": "Cricket Match", "event_time": "10:00 AM", "event_type": "Sports", "location": "Chennai Stadium"},
        {"event_name": "Music Show", "event_time": "6:00 PM", "event_type": "Music", "location": "Chennai Concert Hall"},
    ]
    for event in events:
        session.execute(f"""
        INSERT INTO global_events (event_name, event_time, event_type, location)
        VALUES ('{event['event_name']}', '{event['event_time']}', '{event['event_type']}', '{event['location']}');
        """)

# Sign Up Page
def sign_up():
    st.subheader("Sign Up")
    name = st.text_input("Enter Name")
    password = st.text_input("Enter Password", type="password")
    location = st.text_input("Enter Location")
    
    if st.button("Sign Up"):
        initialize_user_keyspace(name)
        session.set_keyspace(name)
        session.execute(f"""
        INSERT INTO profile (name, password, location) 
        VALUES ('{name}', '{password}', '{location}');
        """)
        st.success(f"User {name} registered successfully!")

# Login Page
def login():
    st.subheader("Login")
    name = st.text_input("Enter Name")
    password = st.text_input("Enter Password", type="password")
    
    if st.button("Login"):
        try:
            session.set_keyspace(name)
            result = session.execute(f"SELECT password FROM profile WHERE name = '{name}'").one()
            if result and result.password == password:
                st.session_state['username'] = name
                st.session_state['page'] = "events"
                st.rerun()  # Force rerun to reflect the page change
            else:
                st.error("Invalid username or password.")
        except Exception:
            st.error("User does not exist.")

# Admin Page
def admin_page():
    st.subheader("Admin - Add Events")
    event_name = st.text_input("Event Name")
    event_time = st.text_input("Event Time")
    event_type = st.text_input("Event Type")
    location = st.text_input("Location")
    
    if st.button("Add Event"):
        session.set_keyspace("global_events")
        session.execute(f"""
        INSERT INTO global_events (event_name, event_time, event_type, location)
        VALUES ('{event_name}', '{event_time}', '{event_type}', '{location}');
        """)
        st.success(f"Event '{event_name}' added successfully!")

# Events Page
def events_page():
    st.subheader("Available Events")
    session.set_keyspace("global_events")
    events = session.execute("SELECT * FROM global_events").all()

    # Initialize session_state for tracking the booking status if not already set
    if "booked_event" not in st.session_state:
        st.session_state.booked_event = {}

    cols = st.columns(3)

    for idx, event in enumerate(events):
        with cols[idx % 3]:
            st.subheader(event.event_name)
            st.write(f"Time: {event.event_time}")
            st.write(f"Type: {event.event_type}")
            st.write(f"Location: {event.location}")

            # Check if this event has been already booked
            if event.event_name in st.session_state.booked_event and st.session_state.booked_event[event.event_name]:
                st.success(f"Booked {event.event_name} successfully!")
                continue  # Skip rendering the booking button if already booked

            # Handle the booking
            if st.button(f"Book {event.event_name}", key=f"book_{idx}"):
                username = st.session_state['username']
                session.set_keyspace(username)

                # Insert the booking into the user's bookings table
                session.execute(f"""
                INSERT INTO bookings (name, event_name, event_time, location) 
                VALUES ('{username}', '{event.event_name}', '{event.event_time}', '{event.location}');
                """)

                # Insert the preference into the user's preferences table
                session.execute(f"""
                    INSERT INTO preferences (name, event_name, event_time, event_type, location) 
                    VALUES ('{username}', '{event.event_name}', '{event.event_time}', '{event.event_type}', '{event.location}');
                """)

                # Mark this event as booked in session_state
                st.session_state.booked_event[event.event_name] = True
                st.success(f"Booked {event.event_name} successfully!")
                break  # Exit the loop to prevent re-triggering the button



# Main Application
initialize_global_keyspace()

# Ensure session_state is initialized
if "page" not in st.session_state:
    st.session_state["page"] = "Sign Up"  # Default page
if "username" not in st.session_state:
    st.session_state["username"] = None  # Default username

# Navigation Logic
if st.session_state["page"] == "Sign Up":
    sign_up()
elif st.session_state["page"] == "Login":
    login()
elif st.session_state["page"] == "Admin Page":
    admin_page()
elif st.session_state["page"] == "events":
    events_page()

# Sidebar Navigation
tabs = st.sidebar.radio("Navigation", ["Sign Up", "Login", "Admin Page"])
if tabs == "Sign Up":
    st.session_state["page"] = "Sign Up"
elif tabs == "Login":
    st.session_state["page"] = "Login"
elif tabs == "Admin Page":
    st.session_state["page"] = "Admin Page"
