from flask import Flask, request, jsonify, render_template
import pandas as pd
import subprocess
import logging
import mysql.connector
import re

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='llm_nl_sql.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Load the CSV files into DataFrames
csv_file_path = 'orig_flight.csv'
faq_csv_file_path = 'for_nl_faq.csv'
try:
    df = pd.read_csv(csv_file_path)
    logging.info("CSV file read successfully.")
    faq_df = pd.read_csv(faq_csv_file_path, header=None, names=['Content'])
    logging.info("FAQ CSV file read successfully.")
except Exception as e:
    logging.error(f"Error reading CSV file: {e}")
    raise

# Convert DataFrame to a textual description
def dataframe_to_text(df):
    text = "The flight database includes the following entities:\n"
    for column in df.columns:
        text += f"- {column}: "
        text += ', '.join(df[column].astype(str).unique()[:5])  # Include a sample of unique values
        text += "\n"
    return text

content = dataframe_to_text(df)

# Function to convert natural language to SQL using LLaMA
def nl_to_sql(nl_query):
    prompt = f"""
    You are an AI assistant that helps with database management. Based on the following content, convert the given natural language query to an SQL query:

    The flight database includes the following entities:
    {content}

    Table name: orig_flight

    Natural language query: {nl_query}
    SQL query:
    """
    try:
        # Save the prompt to a temporary file
        with open('prompt.txt', 'w') as file:
            file.write(prompt)
        logging.info("Prompt saved to prompt.txt successfully.")
        
        # Prepare the command to load the model and input the prompt
        command = f"""
        /usr/local/bin/ollama run llama3.1:8b << EOF
        {prompt}
        EOF
        """
        logging.info("Running Ollama with the specified command.")
        
        # Execute the command
        response = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Process the output as plain text
        sql_query = response.stdout.strip()
        logging.info(f"Ollama response received successfully. SQL Query: {sql_query}")
        
        return sql_query

    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while running Ollama: {e}")
        logging.error(f"Output: {e.output}")
        raise

# Function to execute SQL query on MySQL database
def execute_sql_query(sql_query):
    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(
            host="127.0.0.1",  # Use the correct host
            port="3307",       # Use the correct port
            user="root",
            password="6455",   # Replace with your actual password
            database="llm_testing"
        )
        cursor = connection.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]  # Get column names before closing cursor
        cursor.close()
        connection.close()
        logging.info(f"SQL query executed successfully. Results: {results}, Columns: {columns}")
        return results, columns
    except mysql.connector.Error as err:
        logging.error(f"Error: {err}")
        raise

# Function to fetch relevant FAQ entries based on the SQL query
def fetch_faq(sql_query):
    try:
        # Extract keywords from the SQL query (simple implementation for demonstration)
        matches = re.findall(r"(?:WHERE|AND)?\s*([a-zA-Z_]+)\s*=\s*'([^']+)'", sql_query, re.IGNORECASE)
        keywords = [match[1] for match in matches]
        logging.info(f"Extracted SQL keywords: {keywords}")
        matching_faqs = faq_df[faq_df['Content'].str.contains('|'.join(keywords), case=False, na=False)]
        logging.info(f"Found {len(matching_faqs)} matching FAQs for keywords: {keywords}")
        return matching_faqs['Content'].tolist()
    except Exception as e:
        logging.error(f"Error fetching FAQ: {e}")
        raise

@app.route('/')
def home():
    return render_template('llm_nl_sql.html')

@app.route('/query', methods=['POST'])
def query():
    nl_query = request.form.get('query')
    logging.info(f"Received NL Query: {nl_query}")
    if not nl_query:
        return jsonify({'error': 'No query provided'}), 400

    sql_query = nl_to_sql(nl_query)
    logging.info(f"Generated SQL Query: {sql_query}")
    try:
        results, columns = execute_sql_query(sql_query)
        result_dict = [dict(zip(columns, row)) for row in results]
        
        faq_results = fetch_faq(sql_query)
        logging.info(f"FAQ Results: {faq_results}")
        
        return jsonify({'query_results': result_dict, 'faq_results': faq_results})
    except Exception as e:
        logging.error(f"Error in /query endpoint: {e}")
        return jsonify({'error': str(e), 'sql_query': sql_query}), 500

if __name__ == '__main__':
    app.run(debug=True)
