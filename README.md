# Urban Climate Explorer

A full-stack data analytics capstone project that extracts, stores, and visualizes global urban climate data. 

**Live Dashboard:** [https://urban-climate-explorer-2xy87ysdxnm86jmhitxsnr.streamlit.app/]

## Project Overview
The Urban Climate Explorer automates the collection of climate data, processes it into a relational database, and serves it through an interactive web dashboard. It allows users to explore temperature trends, geographical climate distributions, and weather patterns across various latitudes.

## The Data Pipeline & Tech Stack
This project demonstrates an end-to-end data workflow:
* **Data Extraction (Web Scraping):** Automated data collection using [Selenium] to gather raw climate records.
* **Data Transformation & Cleaning:** Normalizing data types, handling missing values, and structuring records using **Pandas** and **NumPy**.
* **Storage:** Cleaned data is loaded into a local **SQLite** database (`city_climate_data.db`) for lightweight, persistent storage.
* **Visualization:** An interactive front-end built with **Streamlit** and **Plotly**, pulling directly from the SQLite database.
