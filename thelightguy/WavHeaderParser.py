import struct
from datetime import datetime, timedelta
import re
import os

class WavHeaderParser:
    
    def __init__(self, file_path, verbose = False):
    
        self.cue_points = []
        self.fmt_chunk = None
        self.data_chunk_info = None
        self.start_datetime = None 
    
        self.filename = file_path
        self.verbose = verbose 
        self.__read(file_path)
        
        
    def __read(self, file_path):
        self.vprint(f"Parsing {file_path}")
 
        with open(file_path, 'rb') as f:

            riff, size, fformat = struct.unpack('<4sI4s', f.read(12))
            if riff != b'RIFF' or fformat != b'WAVE':
                raise ValueError("Not a valid WAV file (header start is neither WAVE nor RIFF).")

            while True:
                chunk_header = f.read(8)
                if not chunk_header:
                    break

                chunk_id, chunk_size = struct.unpack('<4sI', chunk_header)
                self.vprint(f"- CHUNK : {chunk_id} of {chunk_size} bytes long")
                
                if chunk_id == b'fmt ':
                    if self.fmt_chunk is not None:
                        raise ValueEror("Not a valid WAV file (too many format chunks, it must appear exactly once)")
                    
                    fmt_raw = struct.unpack('<HHIIHH', f.read(chunk_size))
                    
                    self.fmt_chunk = {
                        "encoding": "PCM" if fmt_raw[0] == 1 else "OTHER", 
                        "channels": fmt_raw[1], 
                        "sample_rate": fmt_raw[2],
                        "bits": fmt_raw[5],
                        "align": fmt_raw[4],
                        "avg_bytes_per_second": fmt_raw[3]
                    }
                    
                    self.vprint(f"  {self.fmt_chunk['encoding']} {self.fmt_chunk['bits']} bits, {self.fmt_chunk['sample_rate']} Hz, {self.fmt_chunk['channels']} ch ")
                    
                    if fmt_raw[0] != 1:
                        raise ValueError("Only WAV files encoded as PCM are supported, this seems to be another codec")
                    
                elif chunk_id == b'data':
                    self.data_chunk_info = {'offset': f.tell(), 'size': chunk_size}
                    self.vprint(f"  offset: {self.data_chunk_info['offset']}, size: {chunk_size} bytes")
                    
                    f.seek(chunk_size, 1)
                    
                elif chunk_id == b'cue ':
                    cue_data = f.read(chunk_size)
                    num_cue_points = struct.unpack('<I', cue_data[:4])[0]
                    for i in range(num_cue_points):
                        cue_point_data = cue_data[4 + i*24 : 28 + i*24]
                        cue_id, position, _, _, _, sample_offset = struct.unpack('<IIIIII', cue_point_data)
                        self.vprint(f"  cue point {cue_id} at {position} samples")
                        self.cue_points.append({'id': cue_id, 'position': position, 'sample_offset': sample_offset})
                
                elif chunk_id == b"bext":
                    bext_data = f.read(chunk_size)
                    try:
                        # in Zoom H5 bext chunk, OriginationDate is at position 320 for 10 bytes, 
                        # OriginationTime follows it directly for 8 bytes
                        odate = bext_data[320: 330].decode('utf-8')
                        otime = bext_data[330: 338].decode('utf-8')
                        self.vprint(f"  Origination date/time: {odate} {otime}")
                        
                        self.start_datetime = datetime.strptime(odate + " " + otime, "%Y-%m-%d %H:%M:%S")
                        
                    except ValueError:
                        pass 
                    
                else:
                    self.vprint(f"  Skipping uninteresting chunk {chunk_id}")
                    f.seek(chunk_size, 1)
                    
            if self.fmt_chunk is None:
                raise ValueError("Not a valid WAV file (missing format chunk, it must appear exactly once)")
        
        self.vprint("Done parsing")
        self.vprint("")
    
    def getFilename(self):
        return self.filename 
    
    def getFormat(self):
        return self.fmt_chunk
        
    def getCuePoints(self):
        res = []
        for c in self.cue_points:
            cue_seconds = c['sample_offset'] / self.fmt_chunk['sample_rate']
            res.append({'id': c['id'], 'sample': c['sample_offset'], 'seconds': cue_seconds})
        
        return res
        
    def getDataInfo(self):
        return self.data_chunk_info
        
    def getSampleCount(self):
        return self.data_chunk_info['size'] / self.fmt_chunk['align']
    
    def getLengthSeconds(self):
        return self.data_chunk_info['size'] / self.fmt_chunk['avg_bytes_per_second']
        
    def getStartTime(self):
        return self.start_datetime
        
    def getEndTime(self):
        if self.start_datetime is None:
            return None
        
        ts = timedelta(seconds = self.getLengthSeconds())
        return self.start_datetime + ts
        
    def vprint(self, string):
        if self.verbose is False:
            return
            
        print(string)
        
        
    def isContinuationOf(self, previousFile):
    
        if previousFile is None:
            self.vprint("Checking for continuationn: Previous is None, so nope")
            return False
        
            
        prevbn = os.path.basename(previousFile.getFilename())
        thisbn = os.path.basename(self.getFilename())
        
        self.vprint(f"Checking for continuation: Will check if {thisbn} comes after {prevbn}")
        
        prevdir = os.path.dirname(previousFile.getFilename())
        thisdir = os.path.dirname(previousFile.getFilename())
        
        if prevdir != thisdir:
            self.vprint("Directories are different, so nope")
            return False

        
        # 
        regex = r"^(PANOK\-)?ZOOM([0-9]{4})_Tr(12|LR)\-([0-9]{4})\.WAV$"
        
        prevm = re.match(regex, prevbn)
        thism = re.match(regex, thisbn)
        
        if prevm is None:
            raise ValueError("The previous WAV file doesn't follow standard ZOOM H5 naming conventions")
            
        if thism is None:
            raise ValueError("The current WAV file doesn't follow standard ZOOM H5 naming conventions")
            
        _, prev_sess_num, prev_input_name, prev_sequence = prevm.groups()        
        _, this_sess_num, this_input_name, this_sequence = thism.groups()
        
        if prev_sess_num != this_sess_num:
            self.vprint(f"Different session numbers ({prev_sess_num}, {this_sess_num}), so nope")
            return False 
            
        if prev_input_name != this_input_name:
            self.vprint(f"Different input names ({prev_input_name}, {this_input_name}), so nope")
            return False 
            
        try:
            prev_seq = int(prev_sequence)
            this_seq = int(this_sequence)
            
            if this_seq != prev_seq + 1:
                self.vprint("Numbers not in sequence, so nope")
                return False
        except ValueError:
            self.vprint("Failed to parse sequence numbers, so nope")
            return False
            
        time1 = previousFile.getEndTime()
        time2 = self.getStartTime()
        delta = time2.timestamp() - time1.timestamp()
        
        self.vprint(f"Time delta between end of previous and start of self: {delta} seconds")
        
        if delta > 2:
            self.vprint("Time delta too large, so nope")
            return False 
        
        self.vprint("Files are indeed following each other")
        return True
        
        
        
        
        