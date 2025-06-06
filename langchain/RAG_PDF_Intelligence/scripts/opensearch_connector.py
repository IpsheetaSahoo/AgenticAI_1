from opensearchpy import OpenSearch

# Initialize the client
client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_compress=True,
    use_ssl=False,  # because security is disabled
)

# Test connection
if client.ping():
    print("✅ Successfully connected to OpenSearch!")
else:
    print("❌ Failed to connect.")
