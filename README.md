md5tool
=======

Python script to generate or check md5 checksums recursively for files in a directory tree.

## Usage

To search recursively for files in a directory and its subdirectories, and check files against their corresponding .md5 checksum files:

    md5tool.py check dir1 [dir2, dir3,...]

To generate .md5 checksum files for any files in a directory or its subdirectories which are missing them:

    md5tool.py generate dir1 [dir2, dir3,...]

To display a help message to show the usage patterns above:

    md5tool.py --help

## Naming scheme for checksum files

This script assumes the following naming scheme for the .md5 checksum files

 * Each .md5 checksum file is stored in the same directory as the file for which that checksum was calculated.
 * Each .md5 checksum file is named the same as the file for which it is calculated, but with an additional ".md5" extension.
   - E.g. the checksum for dir1/myfile.mov should be stored in dir1/myfile.mov.md5

## Basic instructions for Mac OS X

 1. Download the *ZIP archive* from github, or clone the repository with **git**.
 2. Place the **md5tool.py** script somewhere convenient, e.g. a `scripts` directory in your Documents folder.
 3. Open the **Terminal** program (in the `Applications/Utilities` directory on your Mac).
 4. Run the following command in Terminal to set permissions for the script (you only need to do this once).

        chmod a+x Documents/scripts/md5tool.py
 5. Type the following into Terminal to check files in a directory:

        ./Documents/scripts/md5tool.py check MYDIRECTORY
  - Replace `MYDIRECTORY` with the name of the directory you want to be checked.
  - To save time, you can *drag and drop* a directory from the **Finder** into the terminal window to specify the directory path.

## Basic instructions for Microsoft Windows

 1. Windows does not have Python installed by default, so first download and install it from [python.org](http://www.python.org/download/).
  - **md5tool.py** has been primarily tested with *Python 2.7*, but may also work with *Python 3.4*.
 2. Next, it is necessary to update the Windows PATH variable so that python can be located from the command line.
  - Open the Control Panel from the Start Menu and go to:
     * System Settings
     * Advanced System Settings
     * Advanced Tab
     * Environmental Settings (extra menu at the bottom)
  - Add a new User Variable Path:
     * `C:\Python27`
     * (If you have a different version of Python, adjust the path name accordingly)
 3. Download the *ZIP archive* from github, or clone the repository with **git**.
 4. Place the **md5tool.py** script somewhere convenient, e.g. a `scripts` directory on your `C:` drive.
 5. Open the Windows **CMD** program to get a command line window.
 6. Type the following into the command line window to check files in a directory:

        python C:\scripts\md5tool.py check MYDIRECTORY
  - Replace `MYDIRECTORY` with the name of the directory you want to be checked.
