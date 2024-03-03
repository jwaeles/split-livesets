import argparse
from pathlib import Path 
from thelightguy.WavHeaderParser import WavHeaderParser
import os.path

verbose_mode = False 

def print_format(p:WavHeaderParser, line_prepend = "", line_append = ""):
    
    f = p.getFormat()
    
    print(f"{line_prepend}Encoding: {f['encoding']}{line_append}")
    print(f"{line_prepend}Channels: {f['channels']}{line_append}")
    print(f"{line_prepend}Sample rate: {f['sample_rate']} Hz{line_append}")
    print(f"{line_prepend}Bits: {f['bits']} bits{line_append}")
    
def parse_wav_files(dirname):

    dir_path = Path(dirname)
    files = [str(file) for file in dir_path.iterdir() if file.suffix.lower() == '.wav']
    
    files.sort()
    res = []
    
    for file in files:
        res.append(WavHeaderParser(file))
        
    return res
    

def process_directory(dirname):
    
    files = parse_wav_files(dirname)
    
    for file in files:
        
        print(os.path.basename(file))
        print(f"\t{p.getSampleCount()} samples, {p.getLengthSeconds()} seconds")
        print_format(p, "\t", "")
        
        
        #print(f"\t{p.getCuePoints()}")

def main():
    # Create ArgumentParser object
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

    # Example usage
    if verbose_mode:
        print(f"Verbose mode is ON. Processing files in directory: {directory}")
    else:
        print(f"Processing files in directory: {directory}")

    # Place your file processing code here
    # ...
    process_directory(directory)

if __name__ == "__main__":
    main()
