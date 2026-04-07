import requests

# Chat request
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "query": "What is machine learning?",
        "top_k": 5,
        "temperature": 0.3
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Grounded: {result['grounded']}")
print(f"Sources: {len(result['sources'])} chunks")
