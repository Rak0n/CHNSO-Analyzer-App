# CHNSO-Analyzer-App
# 🧪 CHNSO Analyzer & Dashboard

## 📖 Overview & Motivation

The **CHNSO Analyzer** is a modular, automated web application built with Streamlit. It is designed to solve a common bottleneck in chemical laboratories: processing messy, instrument-generated Excel files containing elemental analysis data (Carbon, Hydrogen, Nitrogen, Sulfur).

Historically, these files contain hidden metadata, blank columns, and formatting issues (like using `-` instead of `0` or mixing means and standard deviations in the same cell). This app seamlessly cleans the raw data, groups replicates, calculates exact means and scientific standard deviations, and calculates Oxygen (`O`) by difference—allowing the user to dynamically input Moisture and Ash percentages. Finally, it exports a clean, ready-to-publish Excel report and provides interactive visualizations.

## ✨ Key Features

- **Robust File Parsing:** Automatically ignores machine metadata and finds the correct data headers, even if the raw file structure is inconsistent.
    
- **Custom Sorting:** Users can interactively select which samples to process and manually define their exact export order.
    
- **Advanced O Calculation:** Computes `O (%) = 100 - C - H - N - S - Moisture - Ash`.
    
- **Smart Dashboards:** Interactive Plotly charts with error bars. Automatically hides Moisture/Ash from charts if their values are zero.
    
- **Professional Excel Export:** Generates a 3-sheet Excel workbook (Raw Data, Means Only, and Formatted "Mean ± SD" tables) ready for academic papers or further graphing.
    

## 🏗️ Architecture & Modules Guide

To respect memory limits (especially the 1GB RAM limit on Streamlit Cloud) and ensure maintainability, the application is divided into highly specialized modules.

### `app.py` (Main Application)

The entry point of the app. It manages the Streamlit UI layout (tabs, columns, headers) and the `st.session_state` to retain data across interactions. It acts as the orchestrator, passing data between the UI and the underlying backend modules.

### `modules/file_handler.py`

The robust I/O engine.

- **`load_excel_files()`**: Uses a "Reverse Engineering" approach. Instead of relying on rigid row skips, it reads the file as a raw matrix, scans for the "Name" header, standardizes column names (mapping variations like `N %` or `Nitrogen` to simply `N`), handles missing elements, and converts instrumental dashes (`-`) into zeroes.
    
- **`create_excel_download()`**: Uses `xlsxwriter` to generate the final 3-sheet Excel report with professional formatting (colored headers, adjusted column widths) purely in memory.
    

### `modules/data_processing.py`

The mathematical core powered by `pandas` and `numpy`.

- Groups sample replicates by Name.
    
- Calculates the Mean and Standard Deviation for C, H, N, and S.
    
- Propagates errors to calculate the Standard Deviation for Oxygen.
    
- Strictly enforces the user's custom sorting order defined in the UI.
    
- Structures the three final dataframes required for the Excel export.
    

### `modules/ui_components.py`

- **`ash_moisture_form()`**: Renders an interactive, Excel-like data grid (`st.data_editor`). It automatically populates a table with the selected samples, allowing the user to quickly type in Moisture and Ash percentages for the subsequent `O` calculation.
    

### `modules/visualizations.py`

The interactive graphics engine powered by `plotly.graph_objects`.

- **`plot_single_sample()`**: Generates a bar chart for a specific sample showing C, O, H, N, S. Dynamically adds Moisture and Ash bars _only_ if they are greater than zero. Includes visual error bars representing the Standard Deviation.
    
- **`plot_comparison()`**: Generates a grouped bar chart allowing the user to visually compare multiple samples side-by-side.
    

## 🚀 User Guide (How to use the App)

### Tab 1: 📂 Data Loading & Selection

1. **Upload:** Drag and drop one or more `.xlsx` files straight from your elemental analyzer.
    
2. **Select:** In the first table ("1. Selezione Sample"), check the boxes next to the samples you want to analyze. Replicates are grouped automatically.
    
3. **Order:** In the second table ("2. Anteprima Dati e Ordinamento"), double-click the `Ordine` column to change the numbers. Click the `Ordine` column header to sort the table. **This exact order will be respected in your final Excel download.**
    

### Tab 2: ⚙️ Calculations & Moisture/Ash

1. **Input Variables:** An interactive grid will appear. Enter the Moisture (%) and Ash (%) for your selected samples. Leave them at `0` if not applicable.
    
2. _(Optional)_ Check the box to completely ignore Moisture and Ash for the entire session.
    
3. **Execute:** Click **"🚀 Esegui Calcoli"**. The app will calculate means, standard deviations, and Oxygen.
    
4. **Download:** Click the download button to get your beautifully formatted 3-sheet Excel report.
    

### Tab 3: 📊 Single Dashboard

Select a single sample from the dropdown menu to view its elemental composition breakdown in an interactive bar chart. Hover over the bars to see exact percentages and error ranges.

### Tab 4: ⚖️ Comparison Dashboard

Select multiple samples from the dropdown menu. The app will generate a grouped bar chart, allowing you to easily compare carbon or oxygen contents across different runs or materials.

