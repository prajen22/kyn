import streamlit as st
import streamlit.components.v1 as components
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
from datetime import datetime

from config import astra_client_id, astra_client_secret, astra_database_id, astra_app_name

# Function to connect to Cassandra database
def connect_db():
    cloud_config = {
        'secure_connect_bundle': 'secure-connect-cassandra-db.zip'  # Path to your secure connect bundle
    }
    cluster = Cluster(cloud=cloud_config, auth_provider=PlainTextAuthProvider(astra_client_id, astra_client_secret))
    session = cluster.connect()
    session.set_keyspace(username)  # Set the keyspace for the user

    return session


def create_keyspace_for_user(username, session):
    """Create a keyspace for the user."""
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {username} WITH REPLICATION = {{ 'class' : 'SimpleStrategy', 'replication_factor' : 1 }}
    """)
    session.set_keyspace(username)

def create_tables_for_user(username, session):
    """Create necessary tables for the user in their keyspace."""
    session.execute("""
        CREATE TABLE IF NOT EXISTS user (
            username TEXT PRIMARY KEY,
            curr_location TEXT,
            event_time TIMESTAMP
        )
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            username TEXT,
            event_name TEXT,
            event_time TIMESTAMP,
            event_location TEXT,
            PRIMARY KEY (username, event_name)
        )
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            username TEXT,
            event_type TEXT,
            event_time TIMESTAMP,
            event_location TEXT,
            PRIMARY KEY (username, event_type)
        )
    """)

def create_admin_tables(session):
    """Create necessary tables for the admin."""
    session.execute("""
        CREATE TABLE IF NOT EXISTS admin_events (
            event_id UUID PRIMARY KEY,
            event_name TEXT,
            event_type TEXT,
            event_time TIMESTAMP,
            event_location TEXT
        )
    """)

def user_signup(username, password, permanent_location, session):
    """Sign up a new user."""
    session.execute(f"INSERT INTO profile (username, password, permanent_location) VALUES ('{username}', '{password}', '{permanent_location}')")

def user_login(username, password, current_location, session):
    """Log in a user and update their current location."""
    result = session.execute(f"SELECT * FROM profile WHERE username = '{username}' AND password = '{password}'").one()

    if result:
        # Create a keyspace and tables for the user
        create_keyspace_for_user(username, session)
        create_tables_for_user(username, session)
        
        session.execute(f"INSERT INTO user (username, curr_location, event_time) VALUES ('{username}', '{current_location}', NULL)")
        return True
    return False

def admin_add_event(event_name, event_type, event_time, event_location, session):
    """Add a new event as admin."""
    session.execute(f"INSERT INTO admin_events (event_id, event_name, event_type, event_time, event_location) VALUES (uuid(), '{event_name}', '{event_type}', '{event_time}', '{event_location}')")

def suggest_event_based_on_preferences(username, session):
    """Suggest events based on user preferences and admin table."""
    preferences = session.execute(f"SELECT * FROM preferences WHERE username = '{username}'").all()
    events = session.execute("SELECT * FROM admin_events").all()

    matched_events = []
    for preference in preferences:
        for event in events:
            if (preference.event_type == event.event_type or
                preference.event_time == event.event_time or
                preference.event_location == event.event_location):
                matched_events.append(event)

    if matched_events:
        return [f"{event.event_name} at {event.event_location} on {event.event_time}" for event in matched_events]
    return ["No events match your preferences at the moment."]

def get_all_admin_events(session):
    """Get all events from the admin table."""
    events = session.execute("SELECT * FROM admin_events").all()
    return [f"{event.event_name} at {event.event_location} on {event.event_time}" for event in events]

def process_query_with_groq(query):
    """Process the query using the GROQ API (stub)."""
    return f"Processed your query: {query}"

def process_user_query(username, query, session):
    """Process user query."""
    responses = []

    # Check if the query contains both event suggestion and LLM-related parts
    if "suggest me an event" in query.lower():
        # Suggest events based on preferences from the database
        event_suggestions = suggest_event_based_on_preferences(username, session)
        responses.append("Here are some event suggestions based on your preferences:")
        responses.extend(event_suggestions)

    elif "what are the events" in query.lower():
        # Get all events from the admin table
        events = get_all_admin_events(session)
        if events:
            responses.append("Here are the available events:")
            responses.extend(events)
        else:
            responses.append("No events available at the moment.")

    if "features" in query.lower() or "app" in query.lower():
        # Respond with details about app features (LLM or predefined response)
        responses.append("Regarding the new features of our app, here are some exciting updates:")
        responses.append("1. Event booking system: You can now book events based on your preferences.")
        responses.append("2. Real-time event suggestions based on location and time.")
        responses.append("3. Chatbot integration to answer queries and suggest events.")
        responses.append("4. Admin panel for adding and managing events.")

    # If the query contains something else, process it using the GROQ API or some other LLM model
    if "suggest me an event" not in query.lower() and "features" not in query.lower() and "what are the events" not in query.lower():
        # If no specific match, handle the query via the GROQ API or some other LLM model
        responses.append(process_query_with_groq(query))

    return responses


# Streamlit App
st.title("Event Management System")
choice = st.sidebar.radio("Navigate", ["Signup", "Login", "Admin"])

session = connect_db()
create_admin_tables(session)

def get_current_location():
    # JavaScript code to get the user's location
    js_code = """
    <script>
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                var coords = position.coords.latitude + "," + position.coords.longitude;
                window.parent.postMessage({coords: coords}, "*");
            }, function(error) {
                window.parent.postMessage({coords: "Error: " + error.message}, "*");
            });
        } else {
            window.parent.postMessage({coords: "Geolocation is not supported by this browser."}, "*");
        }
    </script>
    """
    
    # Inject JavaScript into Streamlit app
    components.html(js_code, height=0, width=0)

    # Listen for the response from the JavaScript code
    result = st.experimental_get_query_params()
    if "coords" in result:
        return result["coords"][0]
    else:
        return "Unable to fetch location"

if choice == "Signup":
    st.subheader("Signup")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    location = st.text_input("Permanent Location")
    if st.button("Signup"):
        user_signup(username, password, location, session)
        st.success("Signup successful!")

elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    # Get current location using GPS
    location = get_current_location()
    
    if st.button("Login"):
        if user_login(username, password, location, session):
            st.success("Login successful!")
            tab1, tab2 = st.tabs(["Events Page", "Chatbot Page"])

            with tab1:
                st.subheader("Events")
                events = session.execute("SELECT * FROM admin_events").all()
                for event in events:
                    if st.button(f"Book {event.event_name}", key=f"book_{event.event_id}"):

                        session.execute(f"INSERT INTO bookings (username, event_name, event_time, event_location) VALUES ('{username}', '{event.event_name}', '{event.event_time}', '{event.event_location}')")
                        st.success(f"Booked {event.event_name} successfully!")

            with tab2:
                st.subheader("Chatbot")
                query = st.text_input("Ask the chatbot")
                if st.button("Submit Query"):
                    responses = process_user_query(username, query, session)
                    for response in responses:
                        st.write(response)

        else:
            st.error("Invalid credentials!")

elif choice == "Admin":
    st.subheader("Admin Panel")
    event_name = st.text_input("Event Name")
    event_type = st.text_input("Event Type")
    event_time = st.text_input("Event Time (YYYY-MM-DD HH:MM:SS)")
    event_location = st.text_input("Event Location")
    if st.button("Add Event"):
        admin_add_event(event_name, event_type, event_time, event_location, session)
        st.success("Event added successfully!")
