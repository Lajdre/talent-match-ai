from functools import lru_cache

from langchain_neo4j import Neo4jGraph

from core.config import config


@lru_cache(maxsize=1)
def get_neo4j_graph() -> Neo4jGraph:
  password = config.NEO4J_PASSWORD.get_secret_value() if config.NEO4J_PASSWORD else None

  return Neo4jGraph(
    url=config.NEO4J_URI, username=config.NEO4J_USERNAME, password=password
  )
