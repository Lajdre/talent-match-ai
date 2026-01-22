from langchain_neo4j import Neo4jGraph

from core.config import config


def get_neo4j_graph() -> Neo4jGraph:
  return Neo4jGraph(
    url=config.NEO4J_URI, username=config.NEO4J_USERNAME, password=config.NEO4J_PASSWORD
  )
