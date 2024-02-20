## RecordPlayerAlbumDetector
Program that recognizes which album is being played on record player
# Fingerprint.py
Fingerprint.py is where I created the "Audio Fingerprints" for all my exisiting WAV files and stored them in a SQL database.
Researching and understanding Audiofingerprints is crucial to understanding this code, and I highly reccomend [this](https://medium.com/swlh/understanding-audio-fingerprinting-b39682aa3b5f) article on audio fingerprints. To briefly explain the program we first create a spectrogram from a WAV file. We then plot the peaks of the spectrogram and create a hash out of two peaks and their time differences. Once we have a list of hashes, I sent them to a SQL database, along with the name of the album they are associated with for comparison.

# liveReading.py
liveReading.py is where we take the input from our record player and figure out which album is being played. I connected my record player to an audio interface and connected it to my Raspberry pi that way. The code for getting the hashes is the exact same as it is for our input, and to compare them we simply just compare our list of hashes from our input to every hash in the database to see which album has the most similar hashes.

# Future ideas 
The main future idea I have with this project is to have the output on a little LCD screen and attach it to the record player. This is the reason why I decided to use a raspberry pi for the project. Also in the Fingerprint.py file you will see there is unused code involving the time of the peaks. This is because I would also like to digitize how far into the album you are to be displayed. The last thing I want to do is just expand my SQL database, as I didnt put every single vinyl I have in there. One note I have is that the program is accurate about 85% of the time for me. This is due to the methods I used to compare the hashes, since some albums have the same hash four times, whenever the sample happens to have that, the vinyl that has that hash gets four free points and it may lead to some inaccuracies.

