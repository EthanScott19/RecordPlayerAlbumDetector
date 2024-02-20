import pyaudio
import wave
import acoustid
import mariadb
from pydub import AudioSegment
import numpy as np
from matplotlib import mlab
from matplotlib import pyplot as plt
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import(generate_binary_structure,
                                     iterate_structure,
                                     binary_erosion,)
from scipy import signal
from scipy.io import wavfile
from statistics import NormalDist
import hashlib
import sys
CHUNK = 1024 * 3 #Trial and error of finding the chunk size that worked with my audio interface
FORMAT = pyaudio.paInt16
CHANNELS = 2 #Amount of channels
RATE = 44100 #Sample rate
RECORD_SECONDS = 20 #Record length. Longer for better results, shorter for more impressive results. I found 20 to be the sweet spot.
WAVE_OUTPUT_FILENAME = ""#Path of wherever you want the input from your vinyl to go.

p = pyaudio.PyAudio()
input_device_index = 2 #This is the usb index that my Audio interface was pluggeed into. Without specicfication, it just used default.

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=input_device_index)

print("Recording")

frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("Calculating")

stream.stop_stream()
stream.close()
p.terminate()
#Converting readings to WAV
wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()
fileName = '/home/ethanscott/Music/Output/output.wav'

rate, data = wavfile.read(fileName) #The same exact pprocess for storing the other vinyls in the database. #Anything from here to ln 96 is explained in Fingerprint.py
data = data[:,1]
frequencies,times,spectrogram = signal.spectrogram(data,rate)
plt.pcolormesh(times,frequencies,np.log(spectrogram))

def get_peaks(specgram,no_of_iteration = 10, min_amplitude = 10):
    structure = generate_binary_structure(2,2)
    neighborhood = iterate_structure(structure,no_of_iteration)
    local_max = maximum_filter(specgram,footprint=neighborhood) == specgram
    background = (specgram == 0)
    eroded_background = binary_erosion(background, structure=neighborhood,border_value=1)
    detected_peaks = local_max ^ eroded_background
    peaks = specgram[detected_peaks].flatten()
    peak_freqs, peak_times = np.where(detected_peaks)
    peak_indices = np.where(peaks > min_amplitude)
    freqs = peak_freqs[peak_indices]
    times = peak_times[peak_indices]
    return list(zip(freqs,times))
peaks = get_peaks(spectrogram)
def generate_hash(freq1, freq2, time_diff):
    hash_string = f"{freq1}|{freq2}|{time_diff}"
    hash_object = hashlib.sha1(hash_string.encode())
    hash_value = hash_object.hexdigest()
    return hash_value

def generate_hashes(peaks, max_time_diff=5):
    hashes = []
    for i in range(len(peaks)):
        for j in range(i + 1, len(peaks)):
            time_diff = peaks[j][1] - peaks[i][1]
            if 0 < time_diff <= max_time_diff:
                freq1 = peaks[i][0]
                freq2 = peaks[j][0]
                hash_value = generate_hash(freq1, freq2, time_diff)
                hashes.append((hash_value))
    return hashes
hashes = generate_hashes(peaks)

def get_all_hashes_with_album(): #New code
    try:
        conn = mariadb.connect(
            user="",#MariaDB Username
            password="", #MariaDB Password
            host="localhost",
            port=3306,
            database="" #Name of Database
        )
        cur = conn.cursor()
        cur.execute("SELECT hash_value, album_name FROM Hashes") # Fetch all hash values and corresponding album names from the database
        all_hashes_with_album = cur.fetchall() # Fetch all hash values and album names into a list of tuples
        return all_hashes_with_album
    except mariadb.Error as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()
            
hashes_with_album_from_database = get_all_hashes_with_album() #Calling our function
hashes_with_album_set = {(hash_value, album_name) for hash_value, album_name in hashes_with_album_from_database} #This was experimental to try to calculate the accuracy, but it wasn't spot on so I left it out in the end
album_counts = {}
for i in hashes:
    for hash_value, album_name in hashes_with_album_from_database:
        if i == hash_value:  # Compare each hash in hashes with 'hash_value' from the database.
            if album_name in album_counts:
                album_counts[album_name] += 1
            else:
                album_counts[album_name] = 1 #Initializing for first appearance

max_album = max(album_counts, key=album_counts.get) #This is our most likely match
matchList = []
for hash_value in max_album:#1
    matchList.append(hash_value)#2
matchSet = set(matchList) #3
hash_set = set(hashes)#4
confidence = (len(matchSet)/(len(hash_set)))*100 #Once again, this is innacurate and was left out. 1 2 3 and 4 are all for this calculation too.
print("Currently playing", max_album) 
print("Hash counts per album:", album_counts)

