# GUI-Experiment

This code contains the element of the GUI for the the quantum optics
experiment run in the group of Barak Dayan at the weizmann institute. 

Several files are related to controlling the experiment. 

The GUI file per se uses functions from those files in order to link buttons 
in the gui to functions that control the experiment. 

# Folder structure :

The classes defined in Widgets will define a widget that can then be imported
by main_GUI.py. Upon instantiation, main_GUI.py will open a new tab in the main
window and place said widget into it. 


Planned arborescence for the project:

```
GUI-Experiment 
│   README.md
│   main_GUI.py (used to run main GUI window)
|   main_GUI.ui
│
└─── Functions (not related to GUI. Runs experiment etc'. Probably one per 'tab')
│    │    Simulate.py (contains the functions used for runing the code on a 
│    │                   computed that is not connected to the experimental setup)
│    └─── Temperature
│    │       file1.py (For functions that can be used from anywhere)
│    │       file2.py (For functions that are specific to use with GUI)
│    │   
│    └─── PGC
│    │       file1.py
│    │       file2.py
│    └─── OD
│    │       file1.py
│    │       file2.py
│    └─── Homodyne
│    │       file1.py
│    │       file2.py
│
└─── Widgets (GUI related code. Probably one per 'tab')
     │   Temperature.py
     │   Temperature.ui
     │   PGC.py
     │   PGC.ui
     │   OD.py
     │   OD.ui
     │   Homodyne.py 
     │   Homodyne.ui
     │   usefull_dataplotting_functions.py 
```

# TODO

* Split single .ui file into multiple .ui files, one for each experiment or 'tab'
* Make sure the various objects all have acccess to the same pcg() object
* Code related to QUA and the OPX could be reorganized. Object names could be more general (for example, 
main OPX object shouldn't be named pgc()...)