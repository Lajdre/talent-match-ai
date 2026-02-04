import logging

from services.neo4j_service import get_neo4j_graph

logger = logging.getLogger(__name__)


def reset_database() -> dict:
  """Perform a complete cleanup of the Neo4j database.

  1. Deletes all nodes and relationships.
  2. Drops all constraints.
  3. Drops all indexes (except system indexes).
  """
  graph = get_neo4j_graph()

  try:
    logger.info("Deleting all nodes and relationships...")
    graph.query("MATCH (n) DETACH DELETE n")

    logger.info("Dropping all constraints...")
    constraints = graph.query("SHOW CONSTRAINTS")
    for constraint in constraints:
      name = constraint.get("name")
      if name:
        try:
          graph.query(f"DROP CONSTRAINT {name}")
        except Exception:
          logger.exception("Could not drop constraint: %s.", name)

    logger.info("Dropping all indexes...")
    indexes = graph.query("SHOW INDEXES")
    for index in indexes:
      name = index.get("name")
      if name and not name.startswith("__") and index.get("type") != "LOOKUP":
        try:
          graph.query(f"DROP INDEX {name}")
        except Exception:
          logger.exception("Could not drop index: %s.", name)

    # Verification
    node_count = graph.query("MATCH (n) RETURN count(n) as count")[0]["count"]
    rel_count = graph.query("MATCH ()-[r]->() RETURN count(r) as count")[0]["count"]

    if node_count == 0 and rel_count == 0:
      return {"status": "success", "message": "Database completely cleared"}
    return {
      "status": "warning",
      "message": f"Cleanup incomplete. Nodes: {node_count}, Relationships: {rel_count}",
    }

  except Exception as e:
    logger.exception("Error during database reset.")
    # Fallback basic cleanup
    graph.query("MATCH (n) DETACH DELETE n")
    raise RuntimeError(f"Database reset failed: {str(e)}") from None
