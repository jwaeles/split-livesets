import struct
import sys

def parse_wav_chunks(file_path):
    with open(file_path, 'rb') as f:
        riff, size, fformat = struct.unpack('<4sI4s', f.read(12))
        if riff != b'RIFF' or fformat != b'WAVE':
            raise ValueError("Not a valid WAV file (header start is neither WAVE nor RIFF).")

        cue_points = []
        fmt_chunk = None
        data_chunk_info = None

        while True:
            chunk_header = f.read(8)
            if not chunk_header:
                break

            chunk_id, chunk_size = struct.unpack('<4sI', chunk_header)
            if chunk_id == b'fmt ':
                if fmt_chunk is not None:
                    raise ValueEror("Not a valid WAV file (too many format chunks, it must appear exactly once)")
                
                fmt_chunk = struct.unpack('<HHIIHH', f.read(chunk_size))
            elif chunk_id == b'data':
                data_chunk_info = {'offset': f.tell(), 'size': chunk_size}
                f.seek(chunk_size, 1)
            elif chunk_id == b'cue ':
                cue_data = f.read(chunk_size)
                num_cue_points = struct.unpack('<I', cue_data[:4])[0]
                for i in range(num_cue_points):
                    cue_point_data = cue_data[4 + i*24 : 28 + i*24]
                    cue_id, position, _, _, _, sample_offset = struct.unpack('<IIIIII', cue_point_data)
                    cue_points.append({'id': cue_id, 'position': position, 'sample_offset': sample_offset})
            else:
                # print(f"Skipping uninteresting chunk {chunk_id}")
                f.seek(chunk_size, 1)
                
        if fmt_chunk is None:
            raise ValueError("Not a valid WAV file (missing format chunk, it must appear exactly once)")

        return fmt_chunk, data_chunk_info, cue_points

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <WAV file path>")
        sys.exit(1)

    file_path = sys.argv[1]
    fmt_chunk, data_chunk_info, cue_points = parse_wav_chunks(file_path)
    print("Format Chunk:", fmt_chunk)
    print("Data Chunk Info:", data_chunk_info)
    print("Cue Points:", cue_points)

if __name__ == "__main__":
    main()
