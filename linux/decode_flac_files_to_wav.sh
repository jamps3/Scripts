for f in *.flac; do flac -d "$f" "${f%.flac}.wav"; done
