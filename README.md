# GUI-Experiment

This code contains the element of the GUI for the the quantum optics
experiment run in the group of Barak Dayan at the Weizmann institute. 

Files related to controlling the experiment are not included (yet). 

# Folder structure :

The classes defined in Widgets define a widget that are then imported
by main_GUI.py. Main_GUI.py opens a new tab in the main
window and places said widget into it. 

# TODO:

* Make sure the various objects all have access to the same pcg() object
* Make tab widgets inhering from one Parent template
* IMPORTANT: in quantum widget, the PlotData is specific to temperature. It also imports the widgets.temperature.dataplot module and should be more general.
