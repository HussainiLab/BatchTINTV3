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
there is no directory chosen), as a few checkboxes, and a few buttons at the bottom. You are going to want to click the 'choose directory' button and navigate to a directory that this program will analyze. 
***If you do not click the 'apply' button on the Choose Directory window, the directory will not be applied, so make sure you click 'apply' and not 'back'***

Choose the directory based off of the following modes:

1) Batch: This you need to choose a directory that contains sub-directories with the sessions you want to analyze.
```
Chosen Directory
    └── Session 1
    |      └── session_file.set
    |      └── session_file.pos
    |      └── ...
    └── Session 2
    |      └── session_file2.set
    |      └── session_file2.pos
    |      └── ...
    |    
    └── session_file3.set
    └── session_file3.pos
    └── ...
    
In the above example, it will convert the sub-directories 'Session 1' and 'Session 2', but not the session files directly within the chosen directory (session_file3)
```

2) Non Batch: You will choose the directory that directly contains the session files that you want to convert. Thus using the same example above, it will skip the files within sub-directories 'Session 1' and 'Session 2', and only look for those files directly within the Chosen Directory, thus session_file3 will be chosen. ***Note: if you want this mode, click the Non-Batch checkbox***

Once a directory is chosen, you will see the Queue populate a list of sessions that are able to be converted (if it has already been converted, it won't be on this list). You can re-order this list if you want certain files to be converted first using the Move Up/Down buttons. 

You should now look at the Klusta Settings (by clicking the Klusta Settings button) and look through the basic/advanced settings options. The format should look familiar as it is a replica (almost) of that which you've seen while using Tint.

It is important to change the ***Number of Tetrodes*** option in the 'basic' tab. This will help the GUI look for the tetrode data. Our lab uses both 4 and 8 tetrode drives therefore the default for this GUI was set to 8. This number does not need to be exact, but it needs to be greater than or equal to the number of tetrodes you used in the files you are analyzing. If you have 8 tetrodes but the field has the number 4 filled in, it will only analyze the first four tetrodes (if they exist in the folder). It will skip any non-existing tetrodes.

Once these settings have been applied, the values will be saved for the next time you open up the GUI.

There is also capabilities of determining if you want Tint to run in "silent" mode or be "visible". There is a Run Silently checkbox on main window of the GUI that you will be able to check. If it is checked everything will run in the background.

You can press Run if all the settings are correct. A Processed folder will be created within the directory you chose which will have your newly created .CUT files.

## Authors
* **Geoff Barrett** - [Geoff’s GitHub](https://github.com/GeoffBarrett)

## License

This project is licensed under the GNU  General  Public  License - see the [LICENSE.md](LICENSE.md) file for details
