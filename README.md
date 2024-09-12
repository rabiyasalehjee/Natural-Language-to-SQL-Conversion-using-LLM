# Natural Language to SQL Conversion using LLM

This project is a Flask-based application that leverages an LLM (Large Language Model) to convert natural language queries into SQL. The application also includes an FAQ matching feature, which fetches relevant entries based on the generated SQL query.

## Features

- **Natural Language to SQL Conversion**: Converts user-inputted natural language queries into SQL using LLaMA (or similar models).
- **MySQL Database Integration**: Executes the generated SQL query on a connected MySQL database.
- **FAQ Matching**: Extracts keywords from the SQL query and provides relevant FAQ entries from a pre-defined dataset.

## Requirements

- Python 3.x
- Flask
- pandas
- mysql-connector-python
- LLaMA Model or compatible LLM
- MySQL database


## Acknowledgements

- The LLaMA model or similar large language models for their conversion capabilities.
- Flask, pandas, and MySQL for powering the backend of this project.
