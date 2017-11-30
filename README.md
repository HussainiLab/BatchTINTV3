# BatchTINTV3
BatchTINT is A GUI created by the Taub Institute in order to create an end-user friendly batch processing solution to complement Axona's new command line modification of TINT.

This GUI will allow the user to define a directory. Within this directory it will be continuously (unless closed) searching for new files to analyze via Tint. The user simply drags a folder containing the appropriate '.set', '.eegx', '.pos', and '.x' tetrode files and the GUI will automatically detect these files and take care of the rest.

# Requirements
***Operating System***: Windows

This GUI was created with the Windows operating system in mind. Therefore, it is untested on Mac OSX, as well as Linux. It is possible
(though unlikely) that it would work on other operating systems.

Suggested: Use of Python 3.4.4, PyQt4 is most compatible with this version of Python, however there are Python 3.5 versions that may work

Python 3.4.4 can be downloaded here as well: https://www.python.org/downloads/release/python-344/

# Installation

1) For those that do not have GitHub installed on their desktop, they will need to install the GitHub Desktop Application: 
https://desktop.github.com/

2) The next step would be to open the Command Prompt

3) In the Command Prompt navigate to the folder where you want to clone the repository (type in: cd folder_path).

If you want it on your Desktop type in the following: ```cd "C:\Users\ [user name]\Desktop\"```

4) Then your next step will be to clone the repository by typing in the following to your Command Prompt:
```
git clone https://github.com/GeoffBarrett/BatchTINT.git
```
***Note: This may take a few minutes. If there is an error produced by the Command Prompt saying the following:*** 

***'git' is not recognized as an internal or external command, operable program or batch file.***

***ensure that you have added the appropriate git locations to the path system variable. Follow these steps in order to add system variables***


  a) First. you are going to need to find the location of git-core and copy the path, it will be similar to the following:
  
  C:\Users\ [Your Username]\AppData\Local\GitHub\ [Something Similar to PortableGit_25d850739bc178b2eb13c3e2a9faafea2f9143c0]\mingw32\libexec\git-core
  
  b) Second, you will need to find the path of the 'bin' folder within the 'mingw32' folder which will look similar to the following:
  
  C:\Users\ [your name]\AppData\Local\GitHub\ [Something Similar to PortableGit_25d850739bc178b2eb13c3e2a9faafea2f9143c0]\mingw32\bin
  
  c) Go to the following window: Control Panel -> System and Security -> System -> Advanced Systems Settings 
  -> Advanced Tab (if not already on it) and -> Environmental Variables 
  
  d) Under 'System variables' edit the 'Path' variable
  
  e) If the variable is a single line of paths then append the two paths to the end of the variable, 
  you will need to add a semicolon to separate each path (existing path;git-core path;bin path).
  If the window you are looking at has a list of the different paths then you will simply add the two paths separately.
  
  f) Click apply/okay to confirm the addition of these paths, close the existing Command Prompt, open a new Command Prompt and the commands will now be available

5) If you are using Python 3.4.4 I have included two wheel (.whl) files in the GitHub repository for PyQt4 that will need
to be installed via the Command Prompt.

If you have not added the Python 3.4.4 path to the system variable (as done for the GitHub path) then you will have to do the same.

Add the following paths to the 'path' system variable:

C:\Python34\Scripts
C:\Python34

You should also upgrade the 'pip' python script which allows for the downloading of python libraries. To upgrade pip, type the
following into the Command Prompt (remember to close and re-open the Command Prompt after adding the system variable): 

```python -m pip install --upgrade pip```

Now you can type the following into the command prompt to install PyQt4:

```python -m pip install [wheel file path] ```

***If you have spaces in your wheel file path make sure to surround the path by quotes***
example: 

```python -m pip install "C:\Users\My Name\Desktop\GitHub\file.whl"```

The wheel files are the following:

64-bit PC: use the PyQt4-4.11.4-cp34-none-win_amd64.whl files

32-bit PC: use the PyQt4-4.11.4-cp34-none-win32.whl file

***Note: if you are using Python 3.5 you can find those .whl files here: http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyqt4***

6) Install the python library responsible for some of the images on the GUI

Type in the following into the Command Prompt:

```python -m pip install pillow```

7) You will also have to add Tint to the system variable as we did before with GitHub and Python

Add the following path for 64-bit systems: C:\Program Files (x86)\Axona\Tint

32-bit systems should be the following: C:\Program Files\Axona\Tint

# Running GUI

Now in your Command Prompt you can type the following in order to run the GUI:
The easiest way to run it is to create a '.bat' file on the desktop that contains the following information:
```
cd "[pathway to your BatchTINT folder]"
python BatchSort.py
exit
```
When you click this .bat file it will run the program.

Now you can see a main window of the GUI that states the current directory (if it's your first time opening the program, it will say 
there is no directory chosen), as a few checkboxes, and a few buttons at the bottom. You are going to want to click the 'choose directory' button and navigate to a directory that this program will analyze. For our lab I made a Google Drive account and shared it with the lab, and those that want to utilize the GUI will just drop their files in the shared folder and it will analyze it, you can use whichever method is easiest for you (Dropbox, mapped network drives, etc). ***If you do not click the 'apply' button on the Choose Directory window, the directory will not be applied, so make sure you click 'apply' and not 'back'***

Once a directory has been chosen you can now look through the Klusta Settings (by clicking the Klusta Settings button) and look through the basic/advanced settings options. The format should look familiar as it is a replica (almost) of that which you've seen while using Tint.

It is important to change the ***Number of Tetrodes*** option in the 'basic' tab. This will help the GUI look for the tetrode data. Our lab uses both 4 and 8 tetrode drives therefore the default for this GUI was set to 8. This number does not need to be exact, but it needs to be greater than or equal to the number of tetrodes you used in the files you are analyzing. If you have 8 tetrodes but the field has the number 4 filled in, it will only analyze the first four tetrodes (if they exist in the folder). It will skip any non-existing tetrodes.

Once these settings have been applied, the values will be saved for the next time you open up the GUI.

How this works is the GUI will look in the chosen directory for new folders (and existing folders). On start-up it will look through existing folders already in the directory to check if any of them need analysis. Once the analysis of these files has been completed it will wait new folders to be detected. Once anew folder has been detected it will look for the appropriate files corresponding to the '.set' files it detects. One at a time these tetrode files will be analyzed via KlustaKwik through Tint. ***Note: if there is an existing .cut file for a corresponding tetrode, the analysis of this tetrode will be skipped.*** A Command Prompt will print messages stating which file it is analyzing, if there is a new file, etc. ***Do not close this Command Prompt or the GUI will stop***.

As long as each folder contains all the appropriate file types that Tint needs, the GUI will analyze the data appropriately. Prior to the newest update, you would have each session (One '.set' and it's corresponding files) per folder. Now the GUI will look for however many '.set' files there are within each folder and analyze their corresponding tetrode data.

There is also capabilities of determining if you want Tint to run in "silent" mode or be "visible". There is a Run Silently checkbox on main window of the GUI that you will be able to check. If it is checked everything will run in the background.

There is also a Multi-Thread checkbox. Once this is checked you will be able to determine how many threads you want to utilize. Essentially multi-threading is pseudo parallel-processing technique. The "# Threads" field can be filled in once the checkbox is checked. This value will correspond to the number of tetrodes you want to process at the same time. You will want to make this decision based off of the processing power and RAM that your computer has. ***Note: the multi-threading functionality has not been implemented yet, but the field is there as a place-holder.***

## Authors
* **Geoff Barrett** - [Geoff’s GitHub](https://github.com/GeoffBarrett)

## License

This project is licensed under the GNU  General  Public  License - see the [LICENSE.md](LICENSE.md) file for details
