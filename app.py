import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai

# Load the data from the CSV file and convert it to Excel
@st.cache_data
def load_data():
    df = pd.read_csv('alumni_data_5000_indian_v3.csv')
    new_column_names = [
        "Student ID", "Student Full Name", "Department Name/Code", "Joining Year", "Graduation Year",
        "Contact Email", "Contact Phone Number", "Date of Birth", "Student Address", "Student City",
        "Academic Score %", "Attendance %", "Got Job Offer in Campus Placement", "Job Offered by Company",
        "Starting Campus Offer Value", "Notes"
    ]
    df.columns = new_column_names
    df.to_excel('alumni_data_converted.xlsx', index=False)
    return df

# Generate SQL query based on the user input
def generate_sql_query(user_query):
    columns = [
        "Student ID", "Student Full Name", "Department Name/Code", "Joining Year", "Graduation Year",
        "Contact Email", "Contact Phone Number", "Date of Birth", "Student Address", "Student City",
        "Academic Score %", "Attendance %", "Got Job Offer in Campus Placement", "Job Offered by Company",
        "Starting Campus Offer Value", "Notes"
    ]
    template = f"""Use the following column names {columns} to generate an SQL query needed to answer this question: {user_query}. 
    Understand the user query well and generate the SQL query.
    The query will fetch data from the Excel file. Use related columns in the SELECT statement and generate a single query. 
    Always SELECT more than necessary column name after understanding the user query. The table name is student_data. 
    Salary package refers to 'Offer value.'"""

    genai.configure(api_key="AIzaSyCXZ1uiMaZnK5mBQPuXd6EOV2IRQxOWHbw")  # Replace with your actual Gemini API Key
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content(template)
    sql_query_cleaned = response.text.replace('```sql\n', '').replace('\n```', '')
    return sql_query_cleaned

# Generate response based on the SQL query result
def generate_response(result_list, user_query):
    template = f"""Use the following data {result_list} to generate a response based on the user query: {user_query}.
    If you're provided with any data, use the data to frame the answers relevant to the user query. Try to frame a sentence with the least data you have.
    Always say "Thanks for asking!" at the end of the answer."""

    genai.configure(api_key="AIzaSyCXZ1uiMaZnK5mBQPuXd6EOV2IRQxOWHbw")  # Replace with your actual Gemini API Key
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content(template)
    return response.text

# Streamlit Chatbot UI
st.title("Alumni Data Chatbot")

# Load the alumni data from CSV
df = load_data()

# Save the data into an in-memory SQLite database
conn = sqlite3.connect(':memory:')
df.to_sql('student_data', conn, index=False, if_exists='replace')

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Ask a question about alumni data (e.g., 'Students who got placed in Wipro in 2020')"):
    # Append user input to session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate SQL query based on the user's question
    sql_query = generate_sql_query(prompt)

    # Execute the generated SQL query
    try:
        result_df = pd.read_sql_query(sql_query, conn)
        result_list = result_df.values.tolist()

        if not result_df.empty:
            # Generate a chatbot response using the result list
            response = generate_response(result_list, prompt)
            with st.chat_message("assistant"):
                st.markdown(response)

            # Append the assistant's response to session state
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            with st.chat_message("assistant"):
                st.markdown("No results found for your query.")
    except Exception as e:
        with st.chat_message("assistant"):
            st.markdown(f"An error occurred: {e}")
