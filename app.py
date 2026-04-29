from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sqlite3

app = Flask(__name__)

# this loads the main html page when the site first opens
@app.route("/")
def home():
    return send_file("closet_app.html")

CORS(app)

# database file that the app connects to
DB_NAME = "clothing_store.db"


# opens the database and makes rows easier to turn into dictionaries
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn





# this is here for the setup button, but the database is already made
@app.route("/setup-db", methods=["POST"])
def setup_db():
    return jsonify({"message": "database already loaded"})

# gets all items with their store info and review stats
@app.route("/items", methods=["GET"])
def get_items():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        items.item_id,
        items.item_name,
        items.clothing_type,
        items.price,
        items.product_url,
        items.image_url,
        stores.store_name,
        ROUND(AVG(reviews.average_rating),1) AS average_rating,
        SUM(reviews.review_count) AS review_count
    FROM items
    LEFT JOIN stores
        ON items.store_id = stores.store_id
    LEFT JOIN reviews
        ON items.item_id = reviews.item_id
    GROUP BY items.item_id
    ORDER BY items.item_name
    """)

    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)

# gets each clothing type once for the filter/dropdown
@app.route("/items/types", methods=["GET"])
def item_types():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT DISTINCT clothing_type
    FROM items
    ORDER BY clothing_type
    """)

    rows = [row["clothing_type"] for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)


# gets all the stores in alphabetical order
@app.route("/stores", methods=["GET"])
def get_stores():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM stores ORDER BY store_name")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)


# adds a new store from the form data
@app.route("/stores", methods=["POST"])
def add_store():
    data = request.get_json()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO stores (store_name, store_type, location, website_url)
    VALUES (?, ?, ?, ?)
    """, (
        data["store_name"],
        data["store_type"],
        data["location"],
        data["website_url"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "store added"})

# gets review averages and review counts for each item
@app.route("/reviews")
def get_reviews():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        items.item_id,
        items.item_name,
        stores.store_name,
        ROUND(AVG(reviews.average_rating),1) AS average_rating,
        SUM(reviews.review_count) AS review_count
    FROM reviews
    JOIN items ON reviews.item_id = items.item_id
    LEFT JOIN stores ON items.store_id = stores.store_id
    GROUP BY items.item_id
    ORDER BY average_rating DESC
    """)

    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)


# adds a new clothing item to the database
@app.route("/items", methods=["POST"])
def add_item():
    data = request.get_json()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO items (item_name, clothing_type, price, product_url, store_id)
    VALUES (?, ?, ?, ?, ?)
    """, (
        data["item_name"],
        data["clothing_type"],
        data["price"],
        data["product_url"],
        data["store_id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "item added"})


# updates an item that already exists
@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    data = request.get_json()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE items
    SET item_name=?, clothing_type=?, price=?, product_url=?, store_id=?
    WHERE item_id=?
    """, (
        data["item_name"],
        data["clothing_type"],
        data["price"],
        data["product_url"],
        data["store_id"],
        item_id
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "item updated"})

# runs a custom select query from the front end
@app.route("/query")
def run_query():
    q = request.args.get("q", "")

    # keeps users from running anything besides select queries here
    if not q.lower().startswith("select"):
        return jsonify([])

    conn = get_db()
    cur = conn.cursor()
    cur.execute(q)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()

    return jsonify(rows)

# deletes an item and its reviews
@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM reviews WHERE item_id=?", (item_id,))
    cur.execute("DELETE FROM items WHERE item_id=?", (item_id,))

    conn.commit()
    conn.close()

    return jsonify({"message": "item deleted"})


# runs a custom query from a post request
@app.route("/custom-query", methods=["POST"])
def custom_query():
    data = request.get_json()
    query = data["query"]

    # only lets select queries run so the database does not get changed here
    if not query.lower().startswith("select"):
        return jsonify({"error": "only select queries allowed"})

    conn = get_db()
    cur = conn.cursor()

    cur.execute(query)
    rows = [dict(row) for row in cur.fetchall()]

    conn.close()
    return jsonify(rows)


# gets basic numbers for the dashboard/stat section
@app.route("/stats", methods=["GET"])
def stats():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total_items FROM items")
    total_items = cur.fetchone()["total_items"]

    cur.execute("SELECT COUNT(*) AS total_stores FROM stores")
    total_stores = cur.fetchone()["total_stores"]

    cur.execute("SELECT ROUND(AVG(price),2) AS avg_price FROM items")
    avg_price = cur.fetchone()["avg_price"]

    conn.close()

    return jsonify({
        "total_items": total_items,
        "total_stores": total_stores,
        "average_price": avg_price
    })


# starts the flask server on port 5000
if __name__ == "__main__":
    app.run(debug=True, port=5000)