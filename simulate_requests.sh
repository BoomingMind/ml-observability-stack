#!/bin/bash

for i in {1..1000}
do
  # Generate random data
  fixed_acidity=$(awk -v min=4 -v max=15 'BEGIN{srand(); print min+rand()*(max-min)}')
  volatile_acidity=$(awk -v min=0.1 -v max=1.2 'BEGIN{srand(); print min+rand()*(max-min)}')
  citric_acid=$(awk -v min=0 -v max=1 'BEGIN{srand(); print min+rand()*(max-min)}')
  residual_sugar=$(awk -v min=0.9 -v max=15.5 'BEGIN{srand(); print min+rand()*(max-min)}')
  chlorides=$(awk -v min=0.012 -v max=0.611 'BEGIN{srand(); print min+rand()*(max-min)}')
  free_sulfur_dioxide=$(awk -v min=1 -v max=72 'BEGIN{srand(); print int(min+rand()*(max-min))}')
  total_sulfur_dioxide=$(awk -v min=6 -v max=289 'BEGIN{srand(); print int(min+rand()*(max-min))}')
  density=$(awk -v min=0.99007 -v max=1.00369 'BEGIN{srand(); print min+rand()*(max-min)}')
  pH=$(awk -v min=2.74 -v max=4.01 'BEGIN{srand(); print min+rand()*(max-min)}')
  sulphates=$(awk -v min=0.33 -v max=2 'BEGIN{srand(); print min+rand()*(max-min)}')
  alcohol=$(awk -v min=8.4 -v max=14.9 'BEGIN{srand(); print min+rand()*(max-min)}')

  # Construct the JSON payload
  json_data="{\"data\": [$fixed_acidity, $volatile_acidity, $citric_acid, $residual_sugar, $chlorides, $free_sulfur_dioxide, $total_sulfur_dioxide, $density, $pH, $sulphates, $alcohol]}"

  # Send the curl request
  curl -X POST "http://127.0.0.1:8000/predict" \
       -H "Content-Type: application/json" \
       -d "$json_data"

  echo "Request $i sent"

  # Optional: add a small delay to avoid overwhelming the server
  #sleep 0.1
done