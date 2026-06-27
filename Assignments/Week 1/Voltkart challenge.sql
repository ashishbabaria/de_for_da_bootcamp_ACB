CREATE DATABASE Voltkart;
USE Voltkart;
SELECT 'dim_category' AS table_name, COUNT(*) AS rows FROM dim_category
UNION ALL SELECT 'dim_employee', COUNT(*) FROM dim_employee
UNION ALL SELECT 'dim_customer', COUNT(*) FROM dim_customer
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'fact_orders', COUNT(*) FROM fact_orders
UNION ALL SELECT 'fact_order_items', COUNT(*) FROM fact_order_items
UNION ALL SELECT 'stg_orders_incr', COUNT(*) FROM stg_orders_incr
UNION ALL SELECT 'cdc_product_changes', COUNT(*) FROM cdc_product_changes;


/* =============================================================
   Q1 — Top 20 completed orders by value
 
   Voltkart's commercial team wants a quick look at the biggest
   sales. Return the top 20 completed orders by value, with the
   customer and the sales rep behind each one.
 
   Required output:
     order_id, order_date, customer_name, sales_rep_name, order_total
   ============================================================= */
SELECT TOP 20
    o.order_id,
    o.order_date,
    c.customer_name,
    e.employee_name AS sales_rep_name,
    o.order_total
FROM fact_orders AS o
INNER JOIN dim_customer AS c ON c.customer_id = o.customer_id
INNER JOIN dim_employee AS e ON e.employee_id = o.sales_rep_id
WHERE o.order_status = 'Completed'
ORDER BY o.order_total DESC;
GO

/* =============================================================
   Q2 — Customers who have never placed an order
 
   Marketing wants to re-engage people who registered but never
   bought. List the customers who have never placed an order.
 
   Required output:
     customer_id, customer_name, signup_date
 
   Note: Using anti-semi-join, which is efficient.
   ============================================================= */
SELECT 
    c.customer_id,
    c.customer_name,
    c.signup_date
FROM dim_customer AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM fact_orders AS o
    WHERE o.customer_id = c.customer_id
)
ORDER BY c.customer_id;
GO

/* =============================================================
   Q3 — Top 3 products per category by completed revenue
 
   Merchandising wants the stars of each category. For every
   category, return the top 3 products by completed revenue.
 
   Required output:
     category_name, product_name, total_revenue, revenue_rank
 
   Note: RANK() keeps ties in (a tie for 3rd would return 4 rows
   in that category). Swap to ROW_NUMBER() for exactly 3 per
   category.
   ============================================================= */
WITH product_revenue AS (
    SELECT 
        cat.category_name,
        p.product_name,
        SUM(oi.line_amount) AS total_revenue
    FROM fact_order_items AS oi
    INNER JOIN fact_orders  AS o   ON o.order_id      = oi.order_id
    INNER JOIN dim_product  AS p   ON p.product_id    = oi.product_id
    INNER JOIN dim_category AS cat ON cat.category_id = p.category_id
    WHERE o.order_status = 'Completed'
    GROUP BY cat.category_name, p.product_name
),
ranked AS (
    SELECT 
        category_name,
        product_name,
        total_revenue,
        RANK() OVER (PARTITION BY category_name ORDER BY total_revenue DESC) AS revenue_rank
    FROM product_revenue
)
SELECT category_name, product_name, total_revenue, revenue_rank
FROM ranked
WHERE revenue_rank <= 3
ORDER BY category_name, revenue_rank;
GO

/* =============================================================
   Q4 — Monthly revenue with running total and MoM % change
 
   Finance wants the revenue trend with momentum. Produce monthly
   completed revenue with a cumulative running total and the
   month-over-month % change.
 
   Required output:
     order_month (YYYY-MM), monthly_revenue, running_total,
     mom_pct_change
   ============================================================= */
WITH monthly AS (
    SELECT 
        CONVERT(char(7), order_date, 126) AS order_month,
        SUM(order_total) AS monthly_revenue
    FROM fact_orders
    WHERE order_status = 'Completed'
    GROUP BY CONVERT(char(7), order_date, 126)
)
SELECT 
    order_month,
    monthly_revenue,
    SUM(monthly_revenue) OVER (
        ORDER BY order_month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total,
    CAST(
        (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY order_month)) * 100.0
        / NULLIF(LAG(monthly_revenue) OVER (ORDER BY order_month), 0)
        AS DECIMAL(10, 2)
    ) AS mom_pct_change
FROM monthly
ORDER BY order_month;
GO


/* =============================================================
   Q5 — Customer quartiles by lifetime completed spend
 
   The CRM team wants to size up the customer base by value.
   Split customers into four quartiles by lifetime completed
   spend, and for each quartile report how many customers fall
   in it and their average spend.
 
   Required output:
     spend_quartile, customer_count, avg_lifetime_spend
 
   ============================================================= */
WITH customer_spend AS (
    SELECT 
        customer_id,
        SUM(order_total) AS lifetime_spend
    FROM fact_orders
    WHERE order_status = 'Completed'
    GROUP BY customer_id
),
quartiles AS (
    SELECT 
        customer_id,
        lifetime_spend,
        NTILE(4) OVER (ORDER BY lifetime_spend) AS spend_quartile
    FROM customer_spend
)
SELECT 
    spend_quartile,
    COUNT(*)            AS customer_count,
    AVG(lifetime_spend) AS avg_lifetime_spend
FROM quartiles
GROUP BY spend_quartile
ORDER BY spend_quartile;
GO

/* =============================================================
   Q6 — Recursive CTE: all categories under 'Computers'
 
   The catalogue team needs to see everything under a part of the
   tree. Using a recursive query, list all categories in the
   subtree rooted at 'Computers' at any depth, with how deep each
   sits and a readable path from Computers.
 
   Required output:
     category_id, category_name, depth_level, category_path
   ============================================================= */
WITH category_tree AS (
    -- Anchor: 'Computers'
    SELECT 
        category_id,
        category_name,
        0 AS depth_level,
        CAST(category_name AS NVARCHAR(1000)) AS category_path
    FROM dim_category
    WHERE category_name = 'Computers'
 
    UNION ALL
 
    -- Recursive: children at every depth
    SELECT 
        c.category_id,
        c.category_name,
        ct.depth_level + 1,
        CAST(ct.category_path + ' > ' + c.category_name AS NVARCHAR(1000))
    FROM dim_category AS c
    INNER JOIN category_tree AS ct ON c.parent_category_id = ct.category_id
)
SELECT category_id, category_name, depth_level, category_path
FROM category_tree
ORDER BY depth_level, category_name
OPTION (MAXRECURSION 100);
GO

/* =============================================================
   Q7 - Team revenue rolled up the org chart
 
   Sales leadership wants performance rolled up the org chart.
   For every employee, compute the total completed order value generated by their whole team — that is, 
   themselves plus everyone reporting under them at any depth. 
   A Sales Rep's team is just themselves; a manager's is their entire subtree.
 
   Required output:
     employee_id, employee_name, role, team_total_revenue
   ============================================================= */
WITH emp_subtree AS (
    -- Pair every employee with every descendant in their subtree
    -- (including themselves). Used to roll up the order totals.
    SELECT 
        employee_id AS root_id,
        employee_id AS descendant_id
    FROM dim_employee
 
    UNION ALL
 
    SELECT 
        es.root_id,
        e.employee_id
    FROM emp_subtree AS es
    INNER JOIN dim_employee AS e ON e.manager_id = es.descendant_id
),
org_path AS (
    -- Anchor: the CEO (the only employee with no manager).
    SELECT 
        employee_id,
        CAST(RIGHT('00000' + CAST(employee_id AS VARCHAR(5)), 5)
             AS NVARCHAR(1000)) AS sort_path,
        0 AS depth
    FROM dim_employee
    WHERE manager_id IS NULL
 
    UNION ALL
 
    -- Recursive: append each child's zero-padded id to the
    -- parent's path. Zero-padding (5 digits) ensures correct
    -- lexicographic ordering — without it '10' would sort
    -- before '2'.
    SELECT 
        e.employee_id,
        CAST(op.sort_path + '>' +
             RIGHT('00000' + CAST(e.employee_id AS VARCHAR(5)), 5)
             AS NVARCHAR(1000)),
        op.depth + 1
    FROM dim_employee AS e
    INNER JOIN org_path AS op ON e.manager_id = op.employee_id
)
SELECT 
    e.employee_id,
    REPLICATE('  ', op.depth) + e.employee_name AS employee_name,
    e.role,
    op.depth,
    ISNULL(SUM(o.order_total), 0) AS team_total_revenue
FROM dim_employee AS e
INNER JOIN org_path   AS op ON op.employee_id = e.employee_id
LEFT  JOIN emp_subtree AS es ON es.root_id     = e.employee_id
LEFT  JOIN fact_orders AS o
       ON o.sales_rep_id = es.descendant_id
      AND o.order_status = 'Completed'
GROUP BY 
    e.employee_id, 
    e.employee_name, 
    e.role, 
    op.depth, 
    op.sort_path
ORDER BY op.sort_path
OPTION (MAXRECURSION 100);
GO
 
/* =============================================================
   Q8 — Incremental MERGE: stg_orders_incr -> fact_orders
 
   The platform team is moving off nightly full reloads. You've
   been handed today's batch in stg_orders_incr. Write a single
   MERGE that performs an incremental load into fact_orders:
   update orders that changed, insert ones that are new.
 
   Acceptance criteria:
     - one MERGE statement
     - matched orders are updated (status and total) and new
       orders inserted
     - include a verification query showing the fact_orders row
       count before versus after and a sample of updated rows
   ============================================================= */
-- Pre-load verification
SELECT COUNT(*) AS rows_before FROM fact_orders;
 
MERGE fact_orders AS tgt
USING stg_orders_incr AS src
    ON tgt.order_id = src.order_id
WHEN MATCHED THEN
    UPDATE SET 
        tgt.order_date   = src.order_date,
        tgt.customer_id  = src.customer_id,
        tgt.sales_rep_id = src.sales_rep_id,
        tgt.order_status = src.order_status,
        tgt.order_total  = src.order_total
WHEN NOT MATCHED BY TARGET THEN
    INSERT (order_id, order_date, customer_id, sales_rep_id, order_status, order_total)
    VALUES (src.order_id, src.order_date, src.customer_id,
            src.sales_rep_id, src.order_status, src.order_total);
 
-- Post-load verification
SELECT COUNT(*) AS rows_after FROM fact_orders;
 
-- Sample of rows touched by this batch
SELECT TOP 20 f.*
FROM fact_orders AS f
INNER JOIN stg_orders_incr AS s ON s.order_id = f.order_id
ORDER BY f.order_id;
GO


/* =============================================================
   Q9 — CDC MERGE: cdc_product_changes -> dim_product
 
   The catalogue source now emits a change feed
   (cdc_product_changes) with operation codes. Apply it to
   dim_product in a single MERGE that honours the codes:
     I = insert a new product
     U = update an existing one
     D = delete it
 
   Acceptance criteria:
     - one MERGE handling all three operations
     - include a verification query showing inserted, updated,
       and deleted products
   ============================================================= */
-- Snapshot before
SELECT 'before' AS phase, COUNT(*) AS product_count FROM dim_product;
 
MERGE dim_product AS tgt
USING cdc_product_changes AS src
    ON tgt.product_id = src.product_id
WHEN MATCHED AND src.operation = 'U' THEN
    UPDATE SET 
        tgt.product_name = src.product_name,
        tgt.category_id  = src.category_id,
        tgt.unit_price   = src.unit_price,
        tgt.unit_cost    = src.unit_cost,
        tgt.launch_date  = src.launch_date
WHEN MATCHED AND src.operation = 'D' THEN
    DELETE
WHEN NOT MATCHED BY TARGET AND src.operation = 'I' THEN
    INSERT (product_id, product_name, category_id, unit_price, unit_cost, launch_date)
    VALUES (src.product_id, src.product_name, src.category_id,
            src.unit_price, src.unit_cost, src.launch_date);
 
-- Snapshot after
SELECT 'after' AS phase, COUNT(*) AS product_count FROM dim_product;
 
-- Feed composition
SELECT operation, COUNT(*) AS feed_rows
FROM cdc_product_changes
GROUP BY operation;
 
-- Inserted + updated rows are visible; deletes have been removed
SELECT c.operation, p.*
FROM cdc_product_changes AS c
LEFT JOIN dim_product AS p ON p.product_id = c.product_id
ORDER BY c.operation, c.product_id;
GO

/* =============================================================
   Q10 — Optimize the slow query
 
   A report is slow. Here is the query analysts are running:
 
       SELECT o.customer_id, COUNT(*) AS orders_2024,
              (SELECT SUM(oi.line_amount)
                 FROM fact_order_items oi
                 JOIN fact_orders o2 ON o2.order_id = oi.order_id
                WHERE o2.customer_id = o.customer_id) AS lifetime_value
         FROM fact_orders o
        WHERE YEAR(o.order_date) = 2024
        GROUP BY o.customer_id;
 
   Turn on SET STATISTICS IO, TIME ON and "Include Actual
   Execution Plan", run it, then make it fast: explain what the
   plan is doing, rewrite the query, and add an index that helps.
 
   Required output:
     - the rewritten query
     - the CREATE INDEX statement(s)
     - a short note giving the logical reads before versus after
       and why the plan changed.
 
   What's wrong with the original:
     1) YEAR(o.order_date) = 2024 wraps the column in a function,
        so the optimizer cannot seek any index on order_date.
        The fix is a half-open date range.
     2) The correlated subquery for lifetime_value re-runs the
        join + aggregate per customer. The fix is to pre-aggregate
        once in a CTE and join.
   ============================================================= */
 
 SET STATISTICS IO, TIME ON;
 SELECT o.customer_id, COUNT(*) AS orders_2024,
              (SELECT SUM(oi.line_amount)
                 FROM fact_order_items oi
                 JOIN fact_orders o2 ON o2.order_id = oi.order_id
                WHERE o2.customer_id = o.customer_id) AS lifetime_value
         FROM fact_orders o
        WHERE YEAR(o.order_date) = 2024
        GROUP BY o.customer_id;


-- Covering indexes
CREATE INDEX IX_fact_orders_customer_date
    ON fact_orders (customer_id, order_date)
    INCLUDE (order_id);
 
CREATE INDEX IX_fact_orders_orderdate_customer
    ON fact_orders (order_date)
    INCLUDE (customer_id);
 
CREATE INDEX IX_fact_order_items_order
    ON fact_order_items (order_id)
    INCLUDE (line_amount);
GO
 
-- Rewritten query
WITH orders_2024 AS (
    SELECT customer_id, COUNT(*) AS orders_2024
    FROM fact_orders
    WHERE order_date >= '2024-01-01'
      AND order_date <  '2025-01-01'
    GROUP BY customer_id
),
ltv AS (
    SELECT o.customer_id, SUM(oi.line_amount) AS lifetime_value
    FROM fact_orders AS o
    INNER JOIN fact_order_items AS oi ON oi.order_id = o.order_id
    GROUP BY o.customer_id
)
SELECT 
    o24.customer_id,
    o24.orders_2024,
    l.lifetime_value
FROM orders_2024 AS o24
LEFT JOIN ltv AS l ON l.customer_id = o24.customer_id
ORDER BY o24.customer_id;
GO

/* =============================================================
   Q11 (Bonus) — Longest consecutive-month streak per customer
 
   The retention team wants loyalty streaks. For each customer,
   find the longest run of consecutive calendar months in which
   they placed at least one completed order.
 
   Required output:
     customer_id, customer_name, longest_streak_months
 
   Approach: classic gaps-and-islands. Subtract a per-customer
   ROW_NUMBER from a monotonic month number; rows in the same
   consecutive run share the same difference, which becomes the
   island id.
   ============================================================= */
WITH customer_months AS (
    SELECT DISTINCT
        customer_id,
        DATEDIFF(month, '1900-01-01', order_date) AS month_num
    FROM fact_orders
    WHERE order_status = 'Completed'
),
labelled AS (
    SELECT 
        customer_id,
        month_num,
        month_num - ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY month_num) AS island_id
    FROM customer_months
),
islands AS (
    SELECT 
        customer_id,
        island_id,
        COUNT(*) AS streak_length
    FROM labelled
    GROUP BY customer_id, island_id
),
longest AS (
    SELECT 
        customer_id,
        MAX(streak_length) AS longest_streak_months
    FROM islands
    GROUP BY customer_id
)
SELECT 
    l.customer_id,
    c.customer_name,
    l.longest_streak_months
FROM longest AS l
INNER JOIN dim_customer AS c ON c.customer_id = l.customer_id
ORDER BY l.longest_streak_months DESC, l.customer_id;
GO