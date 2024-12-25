# AstroTriage
Use this script to triage and get information about astrophotography subs to make processing easier.

2 functions are available:

## Filter images by star roundness
Enter a folder path to read all .NEF files in that folder, determine the average star roundness, and display a graph showing how many subs will be rejected if a certain threshold is used:
![screenshot](https://github.com/alexlafortune/astrotriage/blob/main/screenshot.png?raw=true)
Choose a threshold that avoids rejecting too many subs or allows too many bad subs.
Subs below the chosen threshold will be safely deleted (sent to Recycle Bin).

## Export metadata
Enter a folder path to read all .NEF files in that folder and export their ISO and exposure time to a spreadsheet. Useful if you use different settings to frame your target than when you're actually shooting subs you intend to use.