// =========================================
// SAMPLE CYPHER QUERIES FOR SHRIMP EXPORT ANALYSIS
// Based on 6W Framework: What, Who, Where, When, Why, How
// =========================================

// =========================================
// 1️⃣ WHAT - Specification & Value Analysis
// =========================================

// Q1: What are the most common product specifications (from goods description)?
MATCH (s:Shipment)-[c:CONTAINS]->(p:Product)
RETURN p.hs_code, 
       c.goods_description,
       count(*) as shipment_count,
       sum(c.quantity) as total_quantity,
       avg(c.unit_price_usd) as avg_unit_price_usd,
       sum(c.fob_usd) as total_fob_usd
ORDER BY shipment_count DESC
LIMIT 20;

// Q2: What is the unit price range across different specifications?
MATCH (s:Shipment)-[c:CONTAINS]->(p:Product)
WHERE c.unit_price_usd > 0
RETURN c.goods_description,
       min(c.unit_price_usd) as min_price,
       max(c.unit_price_usd) as max_price,
       avg(c.unit_price_usd) as avg_price,
       count(*) as shipments
ORDER BY avg_price DESC
LIMIT 20;

// Q3: What is the average FOB price trend month-over-month?
MATCH (s:Shipment)-[:OCCURRED_IN]->(tm:TimeMonth)
MATCH (s)-[c:CONTAINS]->(p:Product)
RETURN tm.year_month,
       count(DISTINCT s) as shipment_count,
       sum(c.fob_usd) as total_fob_usd,
       avg(c.unit_price_usd) as avg_unit_price
ORDER BY tm.year_month;

// Q4: What specifications yield highest value per KG?
MATCH (s:Shipment)-[c:CONTAINS]->(p:Product)
WHERE c.std_quantity > 0 AND c.fob_usd > 0
WITH c.goods_description, 
     sum(c.fob_usd) / sum(c.std_quantity) as value_per_kg,
     count(*) as shipment_count,
     sum(c.std_quantity) as total_kg
ORDER BY value_per_kg DESC
RETURN goods_description, value_per_kg, shipment_count, total_kg
LIMIT 20;


// =========================================
// 2️⃣ WHO - Supplier / Exporter Performance
// =========================================

// Q5: Who are the top exporters by total FOB value?
MATCH (e:Exporter)-[:SHIPPED]->(s:Shipment)-[c:CONTAINS]->(p:Product)
RETURN e.iec,
       e.name,
       e.city,
       count(DISTINCT s) as total_shipments,
       sum(c.fob_usd) as total_fob_usd,
       avg(c.unit_price_usd) as avg_unit_price,
       sum(c.quantity) as total_quantity
ORDER BY total_fob_usd DESC
LIMIT 20;

// Q6: Who maintains price stability (minimal fluctuation)?
MATCH (e:Exporter)-[:SHIPPED]->(s:Shipment)-[c:CONTAINS]->(p:Product)
WHERE c.unit_price_usd > 0
WITH e.name, 
     collect(c.unit_price_usd) as prices,
     count(*) as shipment_count
WHERE shipment_count > 5
RETURN e.name,
       min(prices) as min_price,
       max(prices) as max_price,
       avg(prices) as avg_price,
       stdev(prices) as price_std_dev,
       (max(prices) - min(prices)) / avg(prices) * 100 as price_variation_pct
ORDER BY price_variation_pct ASC
LIMIT 20;

// Q7: Who are repeat exporters with consistent volume?
MATCH (e:Exporter)-[:SHIPPED]->(s:Shipment)-[:OCCURRED_IN]->(tm:TimeMonth)
WITH e, tm.year_month as month, count(s) as monthly_shipments
WITH e, 
     count(month) as active_months,
     avg(monthly_shipments) as avg_monthly_shipments,
     stdev(monthly_shipments) as volume_consistency
WHERE active_months >= 6
RETURN e.name, 
       active_months,
       avg_monthly_shipments,
       volume_consistency
ORDER BY volume_consistency ASC
LIMIT 20;

// Q8: Which exporters have repeat consignee relationships?
MATCH (e:Exporter)-[:SHIPPED]->(s:Shipment)-[:SENT_TO]->(c:Consignee)
WITH e, c, count(s) as shipments_to_consignee
WHERE shipments_to_consignee > 1
WITH e, count(c) as repeat_consignees, sum(shipments_to_consignee) as total_repeat_shipments
MATCH (e)-[:SHIPPED]->(s2:Shipment)
WITH e, repeat_consignees, total_repeat_shipments, count(DISTINCT s2) as total_shipments
RETURN e.name,
       total_shipments,
       repeat_consignees,
       total_repeat_shipments,
       (total_repeat_shipments * 100.0 / total_shipments) as repeat_business_pct
ORDER BY repeat_business_pct DESC
LIMIT 20;


// =========================================
// 3️⃣ WHERE - Logistics & Market Destination
// =========================================

// Q9: Where are shipments originating from (Indian ports)?
MATCH (s:Shipment)-[:DEPARTED_FROM]->(ip:IndianPort)
MATCH (s)-[c:CONTAINS]->(p:Product)
RETURN ip.port_name,
       count(DISTINCT s) as shipment_count,
       sum(c.fob_usd) as total_fob_usd,
       sum(c.quantity) as total_quantity
ORDER BY total_fob_usd DESC;

// Q10: Where are they delivered (top destination countries)?
MATCH (s:Shipment)-[:EXPORTED_TO]->(country:Country)
MATCH (s)-[c:CONTAINS]->(p:Product)
RETURN country.name,
       country.iso_code_2,
       count(DISTINCT s) as shipment_count,
       sum(c.fob_usd) as total_fob_usd,
       avg(c.unit_price_usd) as avg_unit_price,
       sum(c.quantity) as total_quantity
ORDER BY total_fob_usd DESC;

// Q11: Which port pairs (routes) are most used?
MATCH (s:Shipment)-[:DEPARTED_FROM]->(ip:IndianPort)
MATCH (s)-[:ARRIVED_AT]->(dp:DestinationPort)
MATCH (s)-[c:CONTAINS]->(p:Product)
RETURN ip.port_name as origin,
       dp.port_name as destination,
       count(DISTINCT s) as shipment_count,
       sum(c.fob_usd) as total_value,
       avg(c.unit_price_usd) as avg_unit_price
ORDER BY shipment_count DESC
LIMIT 20;

// Q12: Where does unit price differ significantly by destination?
MATCH (s:Shipment)-[:EXPORTED_TO]->(country:Country)
MATCH (s)-[c:CONTAINS]->(p:Product)
WHERE c.unit_price_usd > 0
WITH country.name as country, 
     avg(c.unit_price_usd) as avg_price,
     count(*) as shipment_count
WHERE shipment_count > 5
RETURN country,
       avg_price,
       shipment_count
ORDER BY avg_price DESC
LIMIT 20;


// =========================================
// 4️⃣ WHEN - Timing & Price Seasonality
// =========================================

// Q13: December exports for last 3 years (comparative)
MATCH (s:Shipment)-[:OCCURRED_IN]->(tm:TimeMonth)
WHERE tm.month = 12 AND tm.year IN [2020, 2021, 2022, 2023]
MATCH (s)-[c:CONTAINS]->(p:Product)
MATCH (s)-[:EXPORTED_TO]->(country:Country)
RETURN tm.year,
       country.name,
       count(DISTINCT s) as shipment_count,
       sum(c.quantity) as total_quantity,
       sum(c.fob_usd) as total_fob_usd,
       avg(c.unit_price_usd) as avg_unit_price
ORDER BY tm.year DESC, total_fob_usd DESC;

// Q14: When do prices peak or dip (monthly seasonality)?
MATCH (s:Shipment)-[:OCCURRED_IN]->(tm:TimeMonth)
MATCH (s)-[c:CONTAINS]->(p:Product)
WHERE c.unit_price_usd > 0
RETURN tm.month,
       avg(c.unit_price_usd) as avg_price,
       sum(c.fob_usd) as total_value,
       count(*) as shipment_count
ORDER BY tm.month;

// Q15: When do exporters ship highest volumes (quarterly)?
MATCH (s:Shipment)-[:OCCURRED_IN]->(tm:TimeMonth)
MATCH (s)-[c:CONTAINS]->(p:Product)
RETURN tm.year,
       tm.quarter,
       count(DISTINCT s) as shipment_count,
       sum(c.quantity) as total_quantity,
       sum(c.fob_usd) as total_value
ORDER BY tm.year, tm.quarter;

// Q16: Year-over-year growth analysis
MATCH (s:Shipment)-[:OCCURRED_IN]->(tm:TimeMonth)
MATCH (s)-[c:CONTAINS]->(p:Product)
WITH tm.year as year, 
     sum(c.fob_usd) as total_value,
     sum(c.quantity) as total_quantity
ORDER BY year
RETURN year,
       total_value,
       total_quantity,
       round((total_value - lag(total_value) OVER (ORDER BY year)) / lag(total_value) OVER (ORDER BY year) * 100, 2) as yoy_value_growth_pct;


// =========================================
// 5️⃣ WHY - Profit or Risk Explanation
// =========================================

// Q17: Why is one exporter's FOB higher? (Product mix analysis)
MATCH (e:Exporter {name: 'KALYAN AQUA AND MARINE EXPORTS INDIA PRIVATE LIMITED'})-[:SHIPPED]->(s:Shipment)-[c:CONTAINS]->(p:Product)
RETURN c.goods_description,
       count(*) as shipment_count,
       avg(c.unit_price_usd) as avg_unit_price,
       sum(c.fob_usd) as total_fob
ORDER BY total_fob DESC;

// Compare with another exporter
MATCH (e:Exporter {name: 'KAY KAY EXPORTS'})-[:SHIPPED]->(s:Shipment)-[c:CONTAINS]->(p:Product)
RETURN c.goods_description,
       count(*) as shipment_count,
       avg(c.unit_price_usd) as avg_unit_price,
       sum(c.fob_usd) as total_fob
ORDER BY total_fob DESC;

// Q18: Why does a country offer premium? (Market analysis)
MATCH (s:Shipment)-[:EXPORTED_TO]->(country:Country {name: 'UNITED STATES'})
MATCH (s)-[c:CONTAINS]->(p:Product)
RETURN c.goods_description,
       count(*) as shipments,
       avg(c.unit_price_usd) as avg_price_usa
ORDER BY avg_price_usa DESC
LIMIT 10;

// Q19: Why do volumes fluctuate? (Supply consistency by exporter)
MATCH (e:Exporter)-[:SHIPPED]->(s:Shipment)-[:OCCURRED_IN]->(tm:TimeMonth)
MATCH (s)-[c:CONTAINS]->(p:Product)
WITH e.name as exporter,
     tm.year_month as month,
     sum(c.quantity) as monthly_quantity
WITH exporter,
     collect(monthly_quantity) as quantities,
     count(*) as active_months
WHERE active_months >= 6
RETURN exporter,
       active_months,
       avg(quantities) as avg_monthly_qty,
       stdev(quantities) as qty_std_dev,
       stdev(quantities) / avg(quantities) * 100 as coefficient_of_variation
ORDER BY coefficient_of_variation ASC
LIMIT 20;


// =========================================
// 6️⃣ HOW - Decision Execution & Strategy
// =========================================

// Q20: How to identify best value exporters? (Price + Volume + Consistency)
MATCH (e:Exporter)-[:SHIPPED]->(s:Shipment)-[c:CONTAINS]->(p:Product)
WHERE c.unit_price_usd > 0
WITH e,
     count(DISTINCT s) as total_shipments,
     sum(c.quantity) as total_quantity,
     avg(c.unit_price_usd) as avg_price,
     stdev(c.unit_price_usd) as price_std_dev,
     sum(c.fob_usd) as total_value
WHERE total_shipments > 5
RETURN e.name,
       e.city,
       total_shipments,
       total_quantity,
       avg_price,
       price_std_dev,
       price_std_dev / avg_price * 100 as price_variation_pct,
       total_value,
       total_value / total_shipments as avg_shipment_value
ORDER BY price_variation_pct ASC, total_value DESC
LIMIT 20;

// Q21: How to find best months for sourcing? (Price + Volume analysis)
MATCH (s:Shipment)-[:OCCURRED_IN]->(tm:TimeMonth)
MATCH (s)-[c:CONTAINS]->(p:Product)
WHERE c.unit_price_usd > 0
WITH tm.month as month,
     avg(c.unit_price_usd) as avg_price,
     sum(c.quantity) as total_volume,
     count(DISTINCT s) as shipment_count
RETURN month,
       avg_price,
       total_volume,
       shipment_count,
       total_volume / shipment_count as avg_volume_per_shipment
ORDER BY avg_price ASC;

// Q22: How to identify reliable long-term partners?
MATCH (e:Exporter)-[:SHIPPED]->(s:Shipment)-[:SENT_TO]->(c:Consignee)
WITH e, c, count(s) as repeat_shipments
WHERE repeat_shipments >= 3
WITH e,
     count(c) as loyal_consignees,
     sum(repeat_shipments) as total_repeat_business
MATCH (e)-[:SHIPPED]->(s2:Shipment)-[:OCCURRED_IN]->(tm:TimeMonth)
WITH e,
     loyal_consignees,
     total_repeat_business,
     count(DISTINCT tm.year_month) as active_months
WHERE active_months >= 12
RETURN e.name,
       e.city,
       active_months,
       loyal_consignees,
       total_repeat_business,
       total_repeat_business * 1.0 / active_months as avg_monthly_repeat_business
ORDER BY loyal_consignees DESC, active_months DESC
LIMIT 20;

// Q23: How to simulate profitability under different scenarios?
// Example: USA market, December month, size ranges
MATCH (s:Shipment)-[:EXPORTED_TO]->(country:Country {name: 'UNITED STATES'})
MATCH (s)-[:OCCURRED_IN]->(tm:TimeMonth {month: 12})
MATCH (s)-[c:CONTAINS]->(p:Product)
MATCH (e:Exporter)-[:SHIPPED]->(s)
RETURN e.name,
       c.goods_description,
       sum(c.quantity) as total_quantity,
       avg(c.unit_price_usd) as avg_unit_price,
       sum(c.fob_usd) as total_fob,
       avg(s.exchange_rate_usd) as avg_exchange_rate,
       // Simulate 5% price increase
       sum(c.fob_usd) * 1.05 as simulated_fob_5pct_increase,
       // Simulate 10% volume discount
       sum(c.quantity) * 1.10 as simulated_quantity_10pct_increase
ORDER BY total_fob DESC
LIMIT 20;


// =========================================
// ADVANCED QUERIES
// =========================================

// Q24: Find similar exporters (same destination + similar product profile)
MATCH (e1:Exporter {name: 'KALYAN AQUA AND MARINE EXPORTS INDIA PRIVATE LIMITED'})-[:SHIPPED]->(s1:Shipment)-[:EXPORTED_TO]->(country:Country)
WITH DISTINCT country
MATCH (e2:Exporter)-[:SHIPPED]->(s2:Shipment)-[:EXPORTED_TO]->(country)
WHERE e2.name <> 'KALYAN AQUA AND MARINE EXPORTS INDIA PRIVATE LIMITED'
WITH e2, count(DISTINCT country) as common_countries
WHERE common_countries >= 2
MATCH (e2)-[:SHIPPED]->(s3:Shipment)-[c:CONTAINS]->(p:Product)
RETURN e2.name,
       common_countries,
       count(DISTINCT s3) as total_shipments,
       sum(c.fob_usd) as total_fob,
       avg(c.unit_price_usd) as avg_unit_price
ORDER BY common_countries DESC, total_fob DESC
LIMIT 10;

// Q25: Exporter market diversification score
MATCH (e:Exporter)-[:SHIPPED]->(s:Shipment)-[:EXPORTED_TO]->(country:Country)
WITH e, 
     count(DISTINCT country) as country_count,
     count(DISTINCT s) as total_shipments
MATCH (e)-[:SHIPPED]->(s2:Shipment)-[c:CONTAINS]->(p:Product)
RETURN e.name,
       country_count,
       total_shipments,
       sum(c.fob_usd) as total_fob,
       country_count * 1.0 / total_shipments as diversification_ratio
ORDER BY country_count DESC, total_fob DESC
LIMIT 20;