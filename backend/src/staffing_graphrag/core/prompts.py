import textwrap

from langchain_core.prompts.prompt import PromptTemplate

CYPHER_GENERATION_TEMPLATE = textwrap.dedent("""
  Task: Generate Cypher statement to query a graph database.
  Instructions:
  Use only the provided relationship types and properties in the schema.
  Do not use any other relationship types or properties that are not provided.
  For skill matching, always use case-insensitive comparison using toLower() function.
  For count queries, ensure you return meaningful column names.

  Schema:
  {schema}

  Note: Do not include any explanations or apologies in your responses.
  Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
  Do not include any text except the generated Cypher statement.

  Examples: Here are a few examples of generated Cypher statements for particular questions:

  # How many Python programmers do we have?
  MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
  WHERE toLower(s.id) = toLower("Python")
  RETURN count(p) AS pythonProgrammers

  # Who has React skills?
  MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
  WHERE toLower(s.id) = toLower("React")
  RETURN p.id AS name

  # Find people with both Python and Django skills
  MATCH (p:Person)-[:HAS_SKILL]->(s1:Skill), (p)-[:HAS_SKILL]->(s2:Skill)
  WHERE toLower(s1.id) = toLower("Python") AND toLower(s2.id) = toLower("Django")
  RETURN p.id AS name

  The question is:
  {question}
""")

CYPHER_QA_TEMPLATE = textwrap.dedent("""
  You are an assistant that helps to form nice and human understandable answers based on a knowledge graph query.
  The information part contains the result(s) of a Cypher query.

  Guidelines:
  - If the information contains count results or numbers, state the exact count clearly.
  - For count queries that return 0, say "There are 0 [items]" - this is a valid result.
  - If the information is empty or null, say you don't know the answer based on the current database.
  - Be specific and mention actual names, numbers, or details from the information.

  Information:
  {context}

  Question: {question}
  Helpful Answer:
""")

cypher_generation_prompt = PromptTemplate(
  input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)

cypher_qa_prompt = PromptTemplate(
  input_variables=["context", "question"], template=CYPHER_QA_TEMPLATE
)
