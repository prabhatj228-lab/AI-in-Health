import pandas as pd
from scipy.signal import butter , filtfilt
import pickle
import os
import numpy as np
import argparse

def load_signal(file_path):
  with open(file_path,'r') as f:
    lines =f.readlines()

    start_row =0
    for i , line in enumerate(lines):
      if line.strip()=='Data:':
        start_row =i+1
        break
    df =pd.read_csv(file_path,sep=';',skiprows =start_row,
                    names=['timestamp','value'])
    df['timestamp'] =pd.to_datetime(
        df['timestamp'],
        format ='%d.%m.%Y %H:%M:%S,%f'
    )
    df.set_index('timestamp',inplace =True)
    return df

def load_events(filepath):
  events =[]

  with open(filepath,'r') as f:
    lines =f.readlines()

  events_lines =[l for l in lines if '-' in l and ';' in l]

  for line in events_lines:
    parts =line.strip().split(';')

    time_range =parts[0]
    event_type =parts[2].strip()

    start_time , end_time =time_range.split('-')

    start = pd.to_datetime(
        start_time,
        format ='%d.%m.%Y %H:%M:%S,%f'
    )

    date_part = start.strftime("%d.%m.%Y")

    end =pd.to_datetime(
        date_part + " " +end_time,
        format ='%d.%m.%Y %H:%M:%S,%f'
    )
    if end <start:
      end+=pd.Timedelta(days=1)

    events.append((start,end,event_type))

  return events

def bandpass_filter(signal , fs =32 , low =0.17 ,high =0.4):
  nyquist = fs/2

  low_cut = low/nyquist
  high_cut = high/nyquist

  b,a = butter(4,[low_cut,high_cut],btype='band')

  filtered_signal =filtfilt(b,a ,signal)

  return filtered_signal

def get_label(window_start , window_end , events):
  best_overlap  =pd.Timedelta(0)
  label ="Normal"

  for event_start , event_end ,event_type in events:
    overlap =min(window_end ,event_end)-max(window_start,event_start)

    if overlap<=pd.Timedelta(0):
      continue
    
    if overlap>best_overlap:
      best_overlap =overlap
      label = event_type
    
  if best_overlap >pd.Timedelta(seconds=15):
    return label
  else:
    return "Normal"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-in_dir", required=True, help="Input directory containing participant folders")
    parser.add_argument("-out_dir", required=True, help="Output directory for the dataset")
    args = parser.parse_args()

    in_dir = args.in_dir
    out_dir = args.out_dir

    ml_dataset = []

    if not os.path.exists(in_dir):
        print(f"Error: Directory '{in_dir}' does not exist.")
        exit(1)
        
    for participant_folder in os.listdir(in_dir):
        folder_path = os.path.join(in_dir, participant_folder)
        
        if not os.path.isdir(folder_path):
            continue
            
        print(f"Processing participant: {participant_folder}...")

        all_files = os.listdir(folder_path)
        flow_path, thor_path, spo2_path, events_path = None, None, None, None

        for file_name in all_files:
            name_lower = file_name.lower()
            if 'flow' in name_lower and 'event' not in name_lower:
                flow_path = os.path.join(folder_path, file_name)
            elif 'thorac' in name_lower:
                thor_path = os.path.join(folder_path, file_name)
            elif 'spo2' in name_lower:
                spo2_path = os.path.join(folder_path, file_name)
            elif 'event' in name_lower:
                events_path = os.path.join(folder_path, file_name)

        if not all([flow_path, thor_path, spo2_path, events_path]):
            print(f"  -> Skipping {participant_folder}: Could not find all 4 required files.")
            continue

        flow = load_signal(flow_path)
        thor = load_signal(thor_path)
        spo2 = load_signal(spo2_path)
        events = load_events(events_path)

        thor['filtered'] = bandpass_filter(thor['value'])
        flow['filtered'] = bandpass_filter(flow['value'])
        spo2_resampled = spo2.resample("31.25ms").interpolate()
        
        window_size = pd.Timedelta(seconds=30)
        step_size = pd.Timedelta(seconds=15)
        start_time = flow.index[0]
        end_time = flow.index[-1]
        
        current_start = start_time

        while current_start + window_size <= end_time:
            current_end = current_start + window_size

            flow_window = flow['filtered'].loc[current_start:current_end].iloc[:960]
            thor_window = thor['filtered'].loc[current_start:current_end].iloc[:960]
            spo2_window = spo2_resampled['value'].loc[current_start:current_end].iloc[:960]

            if len(flow_window) == 960 and len(thor_window) == 960 and len(spo2_window) == 960:
                label = get_label(current_start, current_end, events)
                
                sample = np.vstack([
                    flow_window.values,
                    thor_window.values,
                    spo2_window.values
                ])
                
                ml_dataset.append((sample, label, participant_folder))

            current_start += step_size

    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "breathing_dataset.pkl")
    
    with open(out_file, "wb") as f:
        pickle.dump(ml_dataset, f)