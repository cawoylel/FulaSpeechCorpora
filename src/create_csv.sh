%%shell

dialects=("adamawa" "borgu" "maacina" "liptako" "caka" "bororro" "pular")

for dialect in "${dialects[@]}"; do
  echo "Generating CSV for $dialect..."
  rm -f "${dialect}_transcriptions.csv"

  for f in "bible/aligned/$dialect"/*/*.json; do
    if [ -f "$f" ]; then
      python3 - <<END_PYTHON
import json
import os

with open("$f", "r") as json_file:
    for line in json_file:
        json_data = json.loads(line)
        filename = os.path.basename(json_data["audio_filepath"]).replace(".flac", ".wav")
        book = os.path.basename(os.path.dirname(json_data["audio_filepath"]))
        transcription = json_data["text"]
        dialect = json_data["audio_filepath"].split('/')[2]

        print(f"{dialect}_{book}_{filename},{transcription},{dialect}")

        with open("${dialect}_transcriptions.csv", "a") as csv_file:
            csv_file.write(f"{dialect}_{book}_{filename},{transcription},{dialect}\n")
END_PYTHON
    fi
  done
done
