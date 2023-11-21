%%shell
for dialect in "adamawa borgu maacina liptak caka bororro pular"; do
  for f in bible/aligned/$dialect/*/*.flac; do
    filename="$(basename "$f")"
    directory="$(dirname "$f")"
    stem=${filename%.*}
    ffmpeg -i $f -ac 1 -ar 16000 $directory/$stem.wav ;
  done
done