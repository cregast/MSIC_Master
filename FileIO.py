import csv
from Functions import IsNumber, TypeChange


class SmallData:
    # Each SmallData object corresponds to a line of intensities for 1 unique compound
    ID = 0
    mz = ''
    driftTime = 0 # Not required, samples with a drift time will be marked so
    intensities = []
    name = ''   # Name of experiment, from filename.d
    lineNum = 0
    maxInt = 0  # Only the first SmallData per medData has a maxInt(ensity)
    width = 0   # Width of sample area
    height = 0  # Height of sample area (must have the same units as width )


def OpenTSV(filename):
    # Reads in a .tsv Skyline export
    bigData = []    # Holds all the data
    medData = []    # One medData has all the data for one unique m/z image
    maxInt = 0

    with open(filename) as tsv:
        reader = csv.reader(tsv, 'excel-tab')
        next(reader) # Skips the header
        for line in reader: # Scan the data into an array of smallData objects, File must be .tsv with comma separated sublists
            smallData = SmallData()
            smallData.ID = line[0]
            smallData.mz = line[1]
            smallData.driftTime = float(line[2])
            smallData.intensities = TypeChange(line[4].split(','), int)
            for intensity in smallData.intensities:
                if intensity > maxInt:
                    maxInt = intensity ## Find a better way to find the max int of a whole image
            smallData.name = line[5]
            # Determines line number by scanning the last places of the filename.
            # Assumes filename in the vein of experiment_conditions_line999.d
            if IsNumber(line[6][-3]): # Just add another if statement if you have more than 1000 lines
                smallData.lineNum = int(line[6][-3:])
            elif IsNumber(line[6][-2]):
                smallData.lineNum = int(line[6][-2:])
            else:
                smallData.lineNum = int(line[6][-1])
            try:
                if (smallData.ID == medData[-1].ID):
                    medData.append(smallData)
                else:
                    medData[0].maxInt = maxInt
                    bigData.append(medData)
                    maxInt = 0
                    medData = []
                    medData.append(smallData)
            except IndexError:
                medData.append(smallData)
    medData[0].maxInt = maxInt
    bigData.append(medData)
    return(bigData)


def OpenTxt(filename):
    # Reads in a txt file (created in Imaging.py)
    medData = []
    settings = []

    with open(filename) as txt:
        settings = txt.readline().rstrip().split()
        i = 1
        for line in txt.readlines():
            smallData = SmallData()
            smallData.lineNum = i
            smallData.intensities = TypeChange(line.split(), int)
            if 'DT' in filename:
                smallData.mz = filename[-21:-13]
                smallData.driftTime = filename[-9:-4]
            else:
                smallData.mz = filename[-9:-4]
            medData.append(smallData)
            i += 1

    maxInt = 0
    for smallData in medData:
        for intensity in smallData.intensities:
            if intensity > maxInt:
                maxInt = intensity
        smallData.name = settings[2]
        smallData.width = int(settings[0])
        smallData.height = int(settings[1])
    medData[0].maxInt = maxInt
    return(medData)