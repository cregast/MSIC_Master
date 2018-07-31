# Visualizes raw IM-MS data with a Mass Profiler report
# Input: 1+ folders of MS data with a Mass Profiler report
# Output: An Images folder within the experimental folder
# Converts the Mass Profiler output to a format compatible with Skyline
# Uses SkylineRunner to generate a list of peaks with intensities
# Maps each intensity to a pixel in an image, one for each compound
#   Pixel color is calculated by dividing its intensity by the highest intensity in that image
# A matching .txt file for every image that enables post-processing (other _ClickMe programs)
import csv
from Functions import OpenSettings
import glob
import pathlib
import os
import time
from Imaging import SaveImage, CreateTxtFile
from FileIO import OpenTSV
from subprocess import Popen
import sys
from PyQt5.QtWidgets import (QFileDialog, QAbstractItemView, QListView, QTreeView, QApplication, QDialog)

# File Explorer class
class getExistingDirectories(QFileDialog):
    def __init__(self, *args):
        super(getExistingDirectories, self).__init__(*args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.Directory)
        self.setOption(self.ShowDirsOnly, True)
        self.findChildren(QListView)[0].setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.findChildren(QTreeView)[0].setSelectionMode(QAbstractItemView.ExtendedSelection)


userInput = input('Would you like to change the settings? (Y/N): ')
if userInput.lower() == 'y':
    settings = OpenSettings()
else:
    with open('SETTINGS.txt') as file: # If you don't change settings, the defaults are used
        settings = file.read().splitlines()

print('Select the folder(s) containing your raw data and Mass Profiler output: ')
qapp = QApplication(sys.argv)
dlg = getExistingDirectories()
if dlg.exec_() == QDialog.Accepted:
    directories = (dlg.selectedFiles())

Dimensions = []
print('Input sample area aspect ratio: ')
for directory in directories:
    file = os.path.basename(directory)
    width = int(input('%s width: ' % file))
    height = int(input('%s height: ' % file))
    Dimensions.append((width, height))

startTime = time.time()

q = 0
for directory in directories:
    if ' ' in directory:
        print('Error: Please remove spaces from folder path: %s' % directory)
    else:
        os.chdir(directory)

        # Scan in MP export and generate transition list
        for file in glob.glob('*.xls'):
            with open(file) as CSV:
                reader = csv.reader(CSV)
                header = next(reader)
                if (header[0][0:12] == 'MassProfiler'): # if file is MP export
                    for i in range(3):
                        # Skip the rest of the default MP header
                        next(reader)
                    columns = str(next(reader))[2:-2].split('\\t') # Identifies column headers
                    i = 0
                    indexDT = False
                    for item in columns:
                        if item == 'ID':
                            indexID = i
                        elif item == 'DT':
                            indexDT = i
                        elif item == 'm/z':
                            indexMZ = i
                        elif item == 'Z':
                            indexZ = i
                        i += 1

                    experiment = file[0:-4]
                    newFile = (experiment + '_TL.csv')

                    with open(newFile, 'w', newline='') as exportCSV:
                        writer = csv.writer(exportCSV)
                        if indexDT:
                            writer.writerow(['Precursor Name\tExplicit Drift Time (msec)\tPrecursor m/z\tPrecursor Charge']) # Transition list header, Skyline can auto-detect these column headers
                            for line in reader:
                                newLine = str(line)
                                newLine = newLine[2:-2].split('\\t')
                                newLine = (newLine[indexID] + '\t' + newLine[indexDT] + '\t' + newLine[indexMZ] + '\t' + newLine[indexZ])
                                writer.writerow([newLine])
                        else:
                            writer.writerow(['Precursor Name\tPrecursor m/z\tPrecursor Charge']) # Transition list header, Skyline can auto-detect these column headers
                            for line in reader:
                                newLine = str(line)
                                newLine = newLine[2:-2].split('\\t')
                                newLine = (newLine[indexID] + '\t' + newLine[indexMZ] + '\t' + newLine[indexZ])
                                writer.writerow([newLine])
                else: # if not a mass profiler export file
                    pass

    # Create SkylineRunner bat file
    with open('CreateReport.bat', 'w') as bat:
        # Could make this into one bat.write() command but minimal gain
        bat.write(settings[2])
        bat.write(' --in=' + settings[1])
        bat.write(' --import-process-count=%d' % os.cpu_count())
        bat.write(' --import-transition-list=%s\\%s' % (os.getcwd(), newFile))
        bat.write(' --import-all-files=%s' % os.getcwd())
        bat.write(' --report-name=PythonTemplate --report-file=%s\\%s.tsv --report-format=TSV' % (os.getcwd(), experiment)) # Export report
        bat.write(' --out=%s\\%s.sky' % (os.getcwd(), experiment))

    # Run bat file
    print('\n\033[4m%s\033[0m\nCreating Skyline report, this will take several minutes...' % os.path.basename(directory))
    p = Popen("CreateReport.bat", cwd=os.getcwd())
    stdout, stderr = p.communicate()

    # Open TSV (Skyline Report)
    TSVname = ('%s\\%s.tsv' % (os.getcwd(), experiment))
    bigData = OpenTSV(TSVname)

    # Create Images
    pathlib.Path('./Images').mkdir(parents=True, exist_ok=True)
    os.chdir('./Images')
    print('Creating images')

    i = 1
    for medData in bigData:
        medData[0].width  = Dimensions[q][0]
        medData[0].height = Dimensions[q][1]
        SaveImage(medData, settings)
        CreateTxtFile(medData)
        sys.stdout.write('\rProcessing image %d of %d' % (i, len(bigData)))
        i += 1
    print('\nDone\n')

print('Processing time: %.2f sec' % (time.time() - startTime))