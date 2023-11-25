curl -X 'POST' \
  'http://0.0.0.0:8000/job/format/json' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "queries": [
    {
      "target": "0e22cdce-68b5-4f94-a8a0-2980cbeeb74c",
      "query": "2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"
    },
    {
      "target": "1e22cdce-68b5-4f94-a8a0-2980cbeeb74c",
      "query": "3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"
    }
  ],
  "sequences": {
    "0e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ABCDEF",
    "2e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ABCDEF",
    "1e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ABCDEF",
    "3e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ABCDEF"
  }
}'
