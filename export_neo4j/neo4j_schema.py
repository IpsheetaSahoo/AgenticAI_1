"""
Neo4j Schema Creation for Shrimp Export Data
Creates constraints, indexes, and initial schema
"""

from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jSchemaBuilder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def create_constraints(self):
        """Create uniqueness constraints for all node types"""
        
        constraints = [
            # Shipment constraints
            "CREATE CONSTRAINT shipment_invoice IF NOT EXISTS FOR (s:Shipment) REQUIRE s.invoice_no IS UNIQUE",
            
            # Product constraints
            "CREATE CONSTRAINT product_hscode IF NOT EXISTS FOR (p:Product) REQUIRE p.hs_code IS UNIQUE",
            
            # Exporter constraints
            "CREATE CONSTRAINT exporter_iec IF NOT EXISTS FOR (e:Exporter) REQUIRE e.iec IS UNIQUE",
            
            # Consignee constraints
            "CREATE CONSTRAINT consignee_id IF NOT EXISTS FOR (c:Consignee) REQUIRE c.consignee_id IS UNIQUE",
            
            # Country constraints
            "CREATE CONSTRAINT country_iso IF NOT EXISTS FOR (c:Country) REQUIRE c.iso_code_2 IS UNIQUE",
            
            # IndianPort constraints
            "CREATE CONSTRAINT indian_port_code IF NOT EXISTS FOR (ip:IndianPort) REQUIRE ip.port_code IS UNIQUE",
            
            # DestinationPort constraints
            "CREATE CONSTRAINT dest_port_name IF NOT EXISTS FOR (dp:DestinationPort) REQUIRE dp.port_name IS UNIQUE",
            
            # TimeMonth constraints
            "CREATE CONSTRAINT time_month IF NOT EXISTS FOR (tm:TimeMonth) REQUIRE tm.year_month IS UNIQUE"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"Created constraint: {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")
                except Exception as e:
                    logger.warning(f"Constraint might already exist: {e}")
    
    def create_indexes(self):
        """Create indexes for frequently queried properties"""
        
        indexes = [
            # Shipment indexes
            "CREATE INDEX shipment_date IF NOT EXISTS FOR (s:Shipment) ON (s.date)",
            "CREATE INDEX shipment_year_month IF NOT EXISTS FOR (s:Shipment) ON (s.year_month)",
            "CREATE INDEX shipment_month IF NOT EXISTS FOR (s:Shipment) ON (s.month)",
            "CREATE INDEX shipment_year IF NOT EXISTS FOR (s:Shipment) ON (s.year)",
            
            # Exporter indexes
            "CREATE INDEX exporter_name IF NOT EXISTS FOR (e:Exporter) ON (e.name)",
            "CREATE INDEX exporter_city IF NOT EXISTS FOR (e:Exporter) ON (e.city)",
            
            # Consignee indexes
            "CREATE INDEX consignee_name IF NOT EXISTS FOR (c:Consignee) ON (c.name)",
            
            # Country indexes
            "CREATE INDEX country_name IF NOT EXISTS FOR (c:Country) ON (c.name)",
            
            # TimeMonth indexes
            "CREATE INDEX time_month_year IF NOT EXISTS FOR (tm:TimeMonth) ON (tm.year)",
            "CREATE INDEX time_month_month IF NOT EXISTS FOR (tm:TimeMonth) ON (tm.month)",
            "CREATE INDEX time_month_quarter IF NOT EXISTS FOR (tm:TimeMonth) ON (tm.quarter)",
            
            # Product indexes
            "CREATE INDEX product_hscode2 IF NOT EXISTS FOR (p:Product) ON (p.hs_code_2)",
            "CREATE INDEX product_hscode4 IF NOT EXISTS FOR (p:Product) ON (p.hs_code_4)"
        ]
        
        with self.driver.session() as session:
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(f"Created index: {index.split('FOR')[1].split('ON')[0].strip()}")
                except Exception as e:
                    logger.warning(f"Index might already exist: {e}")
    
    def verify_schema(self):
        """Verify that schema is created correctly"""
        
        with self.driver.session() as session:
            # Check constraints
            result = session.run("SHOW CONSTRAINTS")
            constraints = [record for record in result]
            logger.info(f"Total constraints created: {len(constraints)}")
            
            # Check indexes
            result = session.run("SHOW INDEXES")
            indexes = [record for record in result]
            logger.info(f"Total indexes created: {len(indexes)}")
            
            return len(constraints) > 0 and len(indexes) > 0
    
    def clear_database(self):
        """Clear all nodes and relationships - USE WITH CAUTION"""
        
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Database cleared")
    
    def get_database_stats(self):
        """Get current database statistics"""
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            
            stats = {record["label"]: record["count"] for record in result}
            
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship, count(r) as count
                ORDER BY count DESC
            """)
            
            rel_stats = {record["relationship"]: record["count"] for record in rel_result}
            
            logger.info("=== Database Statistics ===")
            logger.info("Nodes:")
            for label, count in stats.items():
                logger.info(f"  {label}: {count}")
            
            logger.info("Relationships:")
            for rel, count in rel_stats.items():
                logger.info(f"  {rel}: {count}")
            
            return {"nodes": stats, "relationships": rel_stats}


def main():
    """Main execution function"""
    
    # Configuration - UPDATE THESE VALUES
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "shrimpdata123"
    
    # Initialize schema builder
    builder = Neo4jSchemaBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        logger.info("Starting schema creation...")
        
        # Create constraints
        logger.info("Creating constraints...")
        builder.create_constraints()
        
        # Create indexes
        logger.info("Creating indexes...")
        builder.create_indexes()
        
        # Verify schema
        logger.info("Verifying schema...")
        if builder.verify_schema():
            logger.info("✓ Schema created successfully!")
        else:
            logger.error("✗ Schema creation failed!")
        
        # Get initial stats
        builder.get_database_stats()
        
    except Exception as e:
        logger.error(f"Error during schema creation: {e}")
        raise
    finally:
        builder.close()


if __name__ == "__main__":
    main()