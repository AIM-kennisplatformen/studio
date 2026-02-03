# Task: Document the TypeQL query construction patterns used in the TypeDB sink

**Parent Feature:** #109 - Documentation on translating a question to a query

## Description

Create comprehensive documentation for the TypeQL query construction patterns implemented in the TypeDB sink module (`studio/src/mcp_servers/lib/typedb/db_sink.py`). This documentation should explain how TypeQL queries are structured, the patterns used for different query types (match, get, insert), and how entity/relation/attribute access is handled within the TypeDBSink class.

This task directly contributes to the parent feature's goal of documenting the complete question-to-query translation flow by providing detailed reference material for the actual query construction layer.

## Requirements

1. [ ] Document the structure of the TypeDBSink class and its responsibilities
2. [ ] Explain the TypeQL match-get query pattern used for data retrieval (as seen in `fetch_person_timesheets`)
3. [ ] Document how entity attributes are accessed and filtered in queries
4. [ ] Describe the relation traversal patterns used in TypeQL queries
5. [ ] Include annotated code examples showing query construction techniques
6. [ ] Document the response parsing patterns (extracting values from query answers)
7. [ ] Add inline code comments to the db_sink.py file explaining each query pattern
