import struct
from datetime import datetime

class WavHeaderParser:
    cue_points = []
    fmt_chunk = None
    data_chunk_info = None
    start_datetime = None 
    filename = None
    
    def __init__(self, file_path):
        self.filename = file_path
        self.__read(file_path)
        pass
        
    def __read(self, file_path):
        
        with open(file_path, 'rb') as f:
            riff, size, fformat = struct.unpack('<4sI4s', f.read(12))
            if riff != b'RIFF' or fformat != b'WAVE':
                raise ValueError("Not a valid WAV file (header start is neither WAVE nor RIFF).")

            while True:
                chunk_header = f.read(8)
                if not chunk_header:
                    break

                chunk_id, chunk_size = struct.unpack('<4sI', chunk_header)
                
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
                    
                    if fmt_raw[0] != 1:
                        raise ValueError("Only WAV files encoded as PCM are supported, this seems to be another codec")
                    
                elif chunk_id == b'data':
                    self.data_chunk_info = {'offset': f.tell(), 'size': chunk_size}
                    f.seek(chunk_size, 1)
                    
                elif chunk_id == b'cue ':
                    cue_data = f.read(chunk_size)
                    num_cue_points = struct.unpack('<I', cue_data[:4])[0]
                    for i in range(num_cue_points):
                        cue_point_data = cue_data[4 + i*24 : 28 + i*24]
                        cue_id, position, _, _, _, sample_offset = struct.unpack('<IIIIII', cue_point_data)
                        self.cue_points.append({'id': cue_id, 'position': position, 'sample_offset': sample_offset})
                
                elif chunk_id == b"bext":
                    bext_data = f.read(chunk_size)
                    try:
                        # in Zoom H5 bext chunk, OriginationDate is at position 320 for 10 bytes, 
                        # OriginationTime follows it directly for 8 bytes
                        odate = bext_data[320: 330].decode('utf-8')
                        otime = bext_data[330: 338].decode('utf-8')
                        
                        self.start_datetime = datetime.strptime(odate + " " + otime, "%Y-%m-%d %H:%M:%S")
                        
                    except ValueError:
                        pass 
                    
                else:
                    # print(f"Skipping uninteresting chunk {chunk_id}")
                    f.seek(chunk_size, 1)
                    
            if self.fmt_chunk is None:
                raise ValueError("Not a valid WAV file (missing format chunk, it must appear exactly once)")
    
    def getFilename(self):
        return self.filename 
    
    def getFormat(self):
        return self.fmt_chunk
        
    def getCuePoints(self):
        return self.cue_points
        
    def getDataInfo(self):
        return self.data_chunk_info
        
    def getSampleCount(self):
        return self.data_chunk_info['size'] / self.fmt_chunk['align']
    
    def getLengthSeconds(self):
        return self.data_chunk_info['size'] / self.fmt_chunk['avg_bytes_per_second']
        
        
        