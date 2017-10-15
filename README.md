# simplesql

`simplesql` offers a simplified SQL syntax that hides the complexity of joins on foreign keys. It compiles to valid
PostgreSQL (MySQL to come, using `WHERE EXISTS (...) OR EXISTS (...) AND EXISTS(...)` clauses rather than 
`UNION`/`INTERSECT`).

## Example Query

This `simplesql` query, where there are tables `part` (with foreign key to:), `supplier` (with foreign key to:),
 `warehouse`:
```
(part.status = "ACTIVE") & (part >>> supplier.name = "Acme") 
& (part >>> warehouse >>> location.id = "BM10-00400")
```

compiles to this:

```SQL
(( 
    SELECT *
    FROM part
    WHERE status = "ACTIVE"
 )) INTERSECT (( 
    SELECT *
    FROM part q1
    RIGHT JOIN (
        SELECT *
        FROM supplier
        WHERE name = "Acme"
        ) q0 ON q0.id = q1.supplier_id
)) INTERSECT (( 
            SELECT *
            FROM part q5
            RIGHT JOIN (
                SELECT *
                FROM warehouse q3
                RIGHT JOIN (
                    SELECT *
                    FROM location
                    WHERE id = "BM10-00400"
                        ) q2 ON q2.id = q3.location_id
                        ) q4 ON q4.id = q5.warehouse_id
))
```