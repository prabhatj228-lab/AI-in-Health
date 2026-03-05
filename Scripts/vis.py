import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import argparse
from matplotlib.backends.backend_pdf import PdfPages

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-name", required=True, help="Path to the participant folder")
    args = parser.parse_args()

    folder_path = args.name
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
        print(f"Error: Could not find all 4 required files in {folder_path}.")
        print(f"Found - Flow: {bool(flow_path)}, Thoracic: {bool(thor_path)}, SpO2: {bool(spo2_path)}, Events: {bool(events_path)}")
        exit(1)
        
    flow =load_signal(flow_path)
    thor =load_signal(thor_path)
    spo2 =load_signal(spo2_path)
    
    events =load_events(events_path)
    
    segment_durations = pd.Timedelta(minutes =5)

    start_time =flow.index[0]
    end_time =flow.index[-1]

    os.makedirs("Visualizations",exist_ok =True)
    
    participant_id = os.path.basename(os.path.normpath(folder_path))
    pdf_path = os.path.join("Visualizations", f"{participant_id}_visualization.pdf")

    with PdfPages(pdf_path) as pdf:
      current_start =start_time

      while current_start<end_time:

        current_end =current_start + segment_durations

        flow_seg = flow.loc[current_start:current_end]
        thor_seg = thor.loc[current_start:current_end]
        spo2_seg = spo2.loc[current_start:current_end]
        
        fig ,ax =plt.subplots(3,1,figsize =(12,8), sharex =True)

        ax[0].plot(flow_seg.index,flow_seg['value'])
        ax[0].set_title("Nasal Airflow")

        ax[1].plot(thor_seg.index,thor_seg['value'])
        ax[1].set_title("Thoracic Movement")

        ax[2].plot(spo2_seg.index,spo2_seg['value'])
        ax[2].set_title("Spo2")

        for ev_start ,ev_end ,event_type in events:
          if ev_end>=current_start and ev_start<=current_end:
            for a in ax:
              a.axvspan(ev_start,ev_end,alpha=0.3)
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()

        current_start =current_end

