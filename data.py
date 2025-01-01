import streamlit as st
from cassandra.cluster import Cluster

# Connect to Cassandra
cluster = Cluster(["127.0.0.1"])  # Replace with your Cassandra IP
session = cluster.connect()

# Initialize keyspace and tables
def initialize_cassandra(username):
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

# Sign Up Page
def sign_up():
    st.title("Sign Up")
    username = st.text_input("Enter Username")
    password = st.text_input("Enter Password", type="password")
    location = st.text_input("Enter Location")
    
    if st.button("Sign Up"):
        if username and password and location:
            initialize_cassandra(username)
            session.set_keyspace(username)
            session.execute(f"""
            INSERT INTO profile (name, password, location) 
            VALUES ('{username}', '{password}', '{location}');
            """)
            st.success("Sign Up Successful! Please log in.")
            st.session_state['page'] = "login"
        else:
            st.error("All fields are required.")

# Log In Page
def login():
    st.title("Log In")
    username = st.text_input("Enter Username", key="login_user")
    password = st.text_input("Enter Password", type="password", key="login_pass")
    
    if st.button("Log In"):
        session.set_keyspace(username)
        user = session.execute(f"SELECT * FROM profile WHERE name='{username}' AND password='{password}' ALLOW FILTERING").one()

        if user:
            st.session_state['username'] = username
            st.session_state['page'] = "events"
        else:
            st.error("Invalid Username or Password.")

# Events Page
def events_page():
    st.title("Available Events")
    events = [
        {"event_name": "Cricket Match", "event_time": "10:00 AM", "location": "Chennai Stadium", "event_type": "Sports"},
        {"event_name": "Football Match", "event_time": "2:00 PM", "location": "Coimbatore Stadium", "event_type": "Sports"},
        {"event_name": "Music Show", "event_time": "6:00 PM", "location": "Chennai Concert Hall", "event_type": "Music"},
        {"event_name": "Comedy Show", "event_time": "8:00 PM", "location": "Madurai Theater", "event_type": "Entertainment"},
        {"event_name": "Dance Show", "event_time": "7:00 PM", "location": "Coimbatore Concert Hall", "event_type": "Dance"},
        {"event_name": "Art Exhibition", "event_time": "10:00 AM", "location": "Trichy Gallery", "event_type": "Art"},
        {"event_name": "Cooking Class", "event_time": "4:00 PM", "location": "Chennai Community Center", "event_type": "Workshop"},
        {"event_name": "Yoga Workshop", "event_time": "6:00 AM", "location": "Ooty Park", "event_type": "Workshop"},
        {"event_name": "Photography Walk", "event_time": "8:00 AM", "location": "Madurai City Center", "event_type": "Photography"}
    ]

    # Create 3 columns
    cols = st.columns(3)

    for idx, event in enumerate(events):
        with cols[idx % 3]:  # Distribute events across 3 columns
            with st.container():  # Wrapping inside a container to create a card-like structure
                st.markdown("""
                <style>
                    .card {
                        padding: 10px;
                        border-radius: 10px;
                        border: 1px solid #ddd;
                        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
                        margin-bottom: 15px;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Card-like layout
                st.markdown('<div class="card">', unsafe_allow_html=True)

                st.subheader(event["event_name"])
                st.write(f"Time: {event['event_time']}")
                st.write(f"Location: {event['location']}")
                st.write(f"Event Type: {event['event_type']}")

                if st.button(f"Book {event['event_name']}", key=f"book_{idx}"):
                    username = st.session_state['username']
                    session.set_keyspace(username)
                    session.execute(f"""
                    INSERT INTO bookings (name, event_name, event_time, location) 
                    VALUES ('{username}', '{event['event_name']}', '{event['event_time']}', '{event['location']}');
                    """)

                    session.execute(f"""
                        INSERT INTO preferences (name, event_name, event_time, event_type, location) 
                        VALUES ('{username}', '{event['event_name']}', '{event['event_time']}', '{event['event_type']}', '{event['location']}');
                    """)

                    st.success(f"Booked {event['event_name']} successfully!")

                st.markdown('</div>', unsafe_allow_html=True)  # Close the card div

# Main Application Flow
if "page" not in st.session_state:
    st.session_state['page'] = "sign_up"

if st.session_state['page'] == "sign_up":
    sign_up()
elif st.session_state['page'] == "login":
    login()
elif st.session_state['page'] == "events":
    events_page()
