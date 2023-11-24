curl -X 'POST' \
  'http://0.0.0.0:8000/job/format/json' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "queries": {
    "0e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ABCD",
    "1e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ABCD",
    "2e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ABCD"
  },
  "targets": {
    "5e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ABCD",
    "6e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ABCD"
  },
  "sequences": [
    [
      "0e22cdce-68b5-4f94-a8a0-2980cbeeb74c",
      "1e22cdce-68b5-4f94-a8a0-2980cbeeb74c"
    ], 
    [
      "0e22cdce-68b5-4f94-a8a0-2980cbeeb74c",
      "1e22cdce-68b5-4f94-a8a0-2980cbeeb74c"
    ]
  ]
}'
