import argparse
from pathlib import Path 
from thelightguy.WavHeaderParser import WavHeaderParser
import os.path
from datetime import datetime, timedelta

verbose_mode = False 

def print_format(p:WavHeaderParser, line_prepend = "", line_append = ""):
    
    f = p.getFormat()
    
    print(f"{line_prepend}Encoding: {f['encoding']}{line_append}")
    print(f"{line_prepend}Channels: {f['channels']}{line_append}")
    print(f"{line_prepend}Sample rate: {f['sample_rate']} Hz{line_append}")
    print(f"{line_prepend}Bits: {f['bits']} bits{line_append}")
    
def parse_wav_files(dirname):

    if verbose_mode:
        print()
        print(f"Checking for .wav files in folder {dirname}")
        print()

    dir_path = Path(dirname)
    files = [str(file) for file in dir_path.iterdir() if file.suffix.lower() == '.wav']
    
    files.sort()
    res = []
    
    for file in files:
        try:
            res.append(WavHeaderParser(file, verbose_mode))
        except ValueError as vex:
            print(vex)
            pass
        
    return res
    
def group_files(files):

    if verbose_mode:
        print("Grouping files")
    
    prev_file = None
    grouped = []
    
    # this will make a list of dictionaries
    for file in files:
        isContinuation = False 
        try:
            isContinuation = file.isContinuationOf(prev_file)
        except ValueError as vex:
            if verbose_mode:
                print(vex)
            pass 
          
        if isContinuation:
            # insert in latest existing list
            grouped[len(grouped)-1]["files"].append(file)
        else:
            # make new list
            grouped.append({"title": None, "files": [file]})
        
        prev_file = file 
        
    for i in range(len(grouped)):
        g = grouped[i]
        filenames = []
        
        for f in g["files"]:
            filenames.append(f.getFilename())
            
        grouped[i]["title"] = os.path.basename(os.path.commonprefix(filenames)) + ("*" if len(filenames) > 1 else "")
    
    
    if verbose_mode:
        print("Done grouping files")
        print()
        
    return(grouped)
    

def process_directory(dirname):
    print()
    print(f"Directory: {os.path.basename(dirname)}")
    
    files = parse_wav_files(dirname)
    groups = group_files(files)
    warnings = []
    
    for g in groups:
        print()
        print(f"\tGROUP {g['title']}")
        firstFile = g["files"][0]
        lastFile = None
        startTime = firstFile.getStartTime()
        previousSeconds = 0.0
        cueCount = 1
        
        print(f"\t - Recording started {startTime}")
        
        for f in g["files"]:
            for c in f.getCuePoints():
                cueSeconds = c['seconds'] + previousSeconds 
                td = timedelta(seconds = cueSeconds)
                print(f"\t\tCue point {cueCount} found {td} after start")
                cueCount = cueCount + 1 
            previousSeconds = previousSeconds + f.getLengthSeconds()
            lastFile = f
        
        print(f"\t - Recording stopped {lastFile.getEndTime()}")
        

def main():
    global verbose_mode
    
    parser = argparse.ArgumentParser(description="Process some WAV files.")

    # Add required 'directory' argument
    parser.add_argument('directory', type=str, help='Directory containing the WAV files to process.')

    # Add optional '--verbose' flag
    parser.add_argument('--verbose', action='store_true', help='Enable verbose mode for debugging.')

    # Parse arguments
    args = parser.parse_args()

    # Access the arguments
    directory = args.directory
    verbose_mode = args.verbose


    process_directory(directory)

if __name__ == "__main__":
    main()
