from pydub import AudioSegment
import numpy as np
from matplotlib import mlab
from matplotlib import pyplot as plt
from scipy.ndimage.morphology import(generate_binary_structure,
                                     iterate_structure,
                                     binary_erosion,)
from scipy.ndimage.filters import maximum_filter
from scipy import signal
from scipy.io import wavfile
from statistics import NormalDist
import hashlib
import mariadb
import sys


fileName = #Wherever you have your file saved
rate, data = wavfile.read(fileName) #Reading data for WAV file
data = data[:,1] #Only selecting channel 2 because that was the input for my record player in my audio interface
frequencies,times,spectrogram = signal.spectrogram(data,rate) # Creating spectrogram
plt.pcolormesh(times,frequencies,np.log(spectrogram))

def get_peaks(specgram,no_of_iteration = 10, min_amplitude = 10): #Finding peaks of spectrogram for further data analysis and audio fingerprinting.
    structure = generate_binary_structure(2,2) #This code mostly came from Ashwini Verma from medium. He published an article on audio fingerprinting called 'Understanding Audio Fingerprinting'
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
    hash_string = f"{freq1}|{freq2}|{time_diff}" # Concatenate frequency, frequency pairing, and time difference
    hash_object = hashlib.sha1(hash_string.encode())
    hash_value = hash_object.hexdigest() # Get the hexadecimal representation of the hash
    return hash_value
def generate_hashes(peaks, max_time_diff=5):
    hashes = []
    for i in range(len(peaks)):
        for j in range(i + 1, len(peaks)):
            time_diff = peaks[j][1] - peaks[i][1]  # Calculate time difference. 
            if 0 < time_diff <= max_time_diff:
                freq1 = peaks[i][0]
                freq2 = peaks[j][0]
                hash_value = generate_hash(freq1, freq2, time_diff)
                hashes.append((hash_value, peaks[i][1]))  # Store hash and time of the first peak. First peak not needed, I just kept it just in case.
    return hashes
hashes = generate_hashes(peaks)
def insert_hashes(hashes, album_name):
    try:
        conn = mariadb.connect(
            user="",# MariaDB username
            password="", #MariaDB password
            host="localhost",
            port=3306,
            database="" #database name
        )
        cur = conn.cursor()

        # Insert each hash into the database along with the album name
        for i in hashes:
            hash_value = i[0]  # Getting the hash instead of the time of first peak, since it was not needed.
            cur.execute("INSERT INTO Hashes (hash_value, album_name) VALUES (?, ?)", (hash_value, album_name))

        conn.commit()
    except mariadb.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
album_name = '' #Name of the album 
insert_hashes(hashes, album_name) # Call the function to insert hashes into the database
