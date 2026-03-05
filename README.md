AI FOR HEALTH - SRIP 2026: SLEEP RESPIRATION ANALYSIS

This repository contains the data processing and visualization pipeline for detecting breathing irregularities that occur during sleep.
It processes overnight physiological signals (Nasal Airflow, Thoracic Movement, and SpO2) collected from sleep study participants.

DIRECTORY STRUCTURE
Project Root/
|-- Data/                  (Raw participant data folders like AP01, AP02, etc.)
|-- Visualizations/        (Generated PDF plots for 1st participant)
|-- scripts/

|   |-- vis.py             (Script for generating 8-hour sleep plots)
|   |-- create_dataset.py  (Script for filtering and windowing data)
|-- README.txt
|-- requirements.txt

Dataset created is not included as file was too big , one can use create_dataset.py to create the dataset
Only first participant visualization is provided in folder , one can generate other participant visualization as mentioned below.

PART 1: DATA VISUALIZATION
The vis.py script explores how the recorded signals look across the 8-hour sleep sessions. It plots Nasal Airflow, Thoracic Movement, and SpO2, and overlays annotated breathing events as highlighted regions.

Usage:
Provide the path to a specific participant's folder using the -name argument. The script will generate a PDF visualization and store it in the Visualizations directory.

Command to run:
python scripts/vis.py -name "Data/AP01"

PART 2: SIGNAL PREPROCESSING AND DATASET CREATION
The create_dataset.py script prepares the raw signals for machine learning. It performs the following operations:

Filtering: Applies a Butterworth bandpass filter (0.17 Hz to 0.4 Hz) to isolate the relevant breathing frequency range and remove noise.

Windowing: Splits the continuous signals into 30-second windows with a 50% (15-second) overlap.

Labeling: Assigns a target label (e.g., "Normal", "Hypopnea") based on whether the window overlaps by more than 50% with a clinically annotated event.

Usage:
Provide the main data directory (-in_dir) and the desired output directory (-out_dir). The script will process all participant folders and compile them into a single file saved to the Dataset directory.

Command to run:
python scripts/create_dataset.py -in_dir "Data" -out_dir "Dataset"
