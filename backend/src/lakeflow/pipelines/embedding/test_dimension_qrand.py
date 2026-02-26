from lakeflow.services.qdrant_service import get_client

client = get_client(None)

info = client.get_collection("Admission")

print(info)