from src.services.neo4j_service import get_neo4j_graph


def check_connection():
  print("Attempting to connect to Neo4j...")

  try:
    graph = get_neo4j_graph()

    # Counts all nodes in the database
    result = graph.query("MATCH (n) RETURN count(n) as count")

    count = result[0]["count"]
    print("Connection Successful!")
    print(f"Current Node Count: {count}")

    if count == 0:
      print("   (The database is empty)")
    else:
      print("   (The database has data)")

  except Exception as e:
    print(f"Connection Failed: {e}")
    print("Check your NEO4J_URI, USERNAME, and PASSWORD in environment variables.")


if __name__ == "__main__":
  check_connection()
