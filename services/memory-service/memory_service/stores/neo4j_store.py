"""Neo4j store — knowledge graph memory."""

from __future__ import annotations

from neo4j import AsyncGraphDatabase, AsyncManagedTransaction

from aisc_utils import get_logger, settings

logger = get_logger(__name__)


class Neo4jStore:
    def __init__(self) -> None:
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_pool_size=10,
        )

    async def connect(self) -> None:
        async with self._driver.session() as session:
            await session.run("RETURN 1")
        logger.info("neo4j_connected", uri=settings.neo4j_uri)

    async def close(self) -> None:
        await self._driver.close()

    async def run_query(
        self, cypher: str, params: dict | None = None
    ) -> list[dict]:
        async with self._driver.session() as session:
            result = await session.run(cypher, params or {})
            records = await result.data()
            return records

    async def run_write_query(
        self, cypher: str, params: dict | None = None
    ) -> list[dict]:
        async with self._driver.session() as session:
            result = await session.execute_write(
                lambda tx: tx.run(cypher, params or {})
            )
            records = await result.data()
            return records

    async def merge_node(
        self, label: str, properties: dict
    ) -> None:
        prop_string = ", ".join(
            f"{k}: ${k}" for k in properties
        )
        await self.run_write_query(
            f"MERGE (n:{label} {{{prop_string}}}) SET n += $props",
            {**properties, "props": properties},
        )

    async def create_relationship(
        self,
        from_label: str,
        from_props: dict,
        rel_type: str,
        to_label: str,
        to_props: dict,
    ) -> None:
        await self.run_write_query(
            f"""
            MATCH (a:{from_label}) WHERE a.id = $from_id
            MATCH (b:{to_label}) WHERE b.id = $to_id
            MERGE (a)-[r:{rel_type}]->(b)
            RETURN r
            """,
            {"from_id": from_props.get("id"), "to_id": to_props.get("id")},
        )

    async def get_entity_relations(
        self, label: str, entity_id: str
    ) -> list[dict]:
        return await self.run_query(
            f"""
            MATCH (n:{label} {{id: $id}})-[r]-(m)
            RETURN labels(m) as labels, m, type(r) as relationship
            """,
            {"id": entity_id},
        )


neo4j_store = Neo4jStore()
