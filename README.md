# GUI-Experiment

This code contains the ellement of the GUI for the the quantum optics
experiment run in the group of Barak Dayan at the weizmann institute. 

Several files are related to controlling the experiment. 

The GUI file per se uses functions from those files in order to link buttons 
in the gui to functions that control the experiment. 

# Folder structure :

The classes defined in Widgets will define a widget that can then be imported
by main_GUI.py. Upon instanciation, main_GUI.py will open a new tab in the main
window and place said widget into it. 


Planned arborescence for the project:

```
GUI_main 
│   README.md
│   main_GUI.py (used to run main GUI window)
│
└─── Functions (not related to GUI, run experiment etc'. Probably one per 'tab')
│    │   Simulate.py (contains the functions used for runing the code on a 
│    │                computed that is not connected to the experimental setup)
│    │   Temperature
│    │    │  file1.py (typically, for functions that can be used from anywhere)
│    │    │  file2.py (typically, for functions that are specific to use with GUI)
│    │   
│    │   PGC
│    │    │  file1.py
│    │    │  file2.py
│    │   OD
│    │    │  file1.py
│    │    │  file2.py
│
└─── Widgets (GUI related code. Probably one per 'tab')
     │   Temperature.py
     │   PGC.py
     │   OD.py
     │   usefull_dataplotting_functions.py 
```