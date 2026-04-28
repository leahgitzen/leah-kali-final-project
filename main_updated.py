import sqlite3
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "clothing_store.db")
CSV_FILE = os.path.join(BASE_DIR, "clothing_store_database-3.csv")


def connect_db():
    return sqlite3.connect(DB_NAME)


def init_db():
    """On every startup: create tables if missing, then load CSV if DB is empty."""
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                store_id INTEGER PRIMARY KEY,
                store_name TEXT NOT NULL,
                store_type TEXT,
                location TEXT,
                website_url TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                item_id INTEGER PRIMARY KEY,
                store_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                clothing_type TEXT,
                price REAL,
                product_url TEXT,
                image_url TEXT,
                FOREIGN KEY (store_id) REFERENCES stores(store_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY,
                item_id INTEGER NOT NULL,
                review_count INTEGER,
                average_rating REAL,
                FOREIGN KEY (item_id) REFERENCES items(item_id)
            )
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS index_items_store_id ON items(store_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS index_items_clothing_type ON items(clothing_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS index_items_price ON items(price)")

        cur.execute("CREATE INDEX IF NOT EXISTS index_reviews_item_id ON reviews(item_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS index_reviews_rating ON reviews(average_rating)")
        cur.execute("CREATE INDEX IF NOT EXISTS index_reviews_count ON reviews(review_count)")

        cur.execute("CREATE INDEX IF NOT EXISTS index_stores_name ON stores(store_name)")
        cur.execute("CREATE INDEX IF NOT EXISTS index_stores_type ON stores(store_type)")

        conn.commit()
        
        cur.execute("SELECT COUNT(*) FROM stores")
        is_empty = cur.fetchone()[0] == 0
        conn.close()
        if is_empty:
            load_csv_data()
    except sqlite3.Error as e:
        print("Startup error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def create_database():
    """Wipe and recreate all tables. Asks for confirmation first."""
    confirm = input("This will delete ALL data. Type YES to confirm: ").strip()
    if confirm != "YES":
        print("Cancelled.")
        return
    try:
        conn = connect_db()
        cur = conn.cursor()

        cur.execute("DROP TABLE IF EXISTS reviews")
        cur.execute("DROP TABLE IF EXISTS items")
        cur.execute("DROP TABLE IF EXISTS stores")

        cur.execute("""
            CREATE TABLE stores (
                store_id INTEGER PRIMARY KEY,
                store_name TEXT NOT NULL,
                store_type TEXT,
                location TEXT,
                website_url TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE items (
                item_id INTEGER PRIMARY KEY,
                store_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                clothing_type TEXT,
                price REAL,
                product_url TEXT,
                image_url TEXT,
                FOREIGN KEY (store_id) REFERENCES stores(store_id)
            )
        """)

        cur.execute("""
            CREATE TABLE reviews (
                review_id INTEGER PRIMARY KEY,
                item_id INTEGER NOT NULL,
                review_count INTEGER,
                average_rating REAL,
                FOREIGN KEY (item_id) REFERENCES items(item_id)
            )
        """)

        conn.commit()
        print("Database wiped and recreated successfully.")

    except sqlite3.Error as e:
        print("Database error:", e)

    finally:
        if "conn" in locals():
            conn.close()


def load_csv_data():
    try:
        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM reviews")
        if cur.fetchone()[0] > 0:
            print("Data already loaded. Run 'Create database' first to reload.")
            conn.close()
            return

        seen_stores = set()
        seen_items = set()

        review_id = 1

        with open(CSV_FILE, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    store_id = int(row["store_id"])
                    item_id = int(row["item_id"])
                    price = float(row["price"])
                    average_rating = float(row["average_rating"])
                    review_count = int(row["review_count"])

                    if store_id not in seen_stores:
                        cur.execute("""
                            INSERT INTO stores (store_id, store_name, store_type, location, website_url)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            store_id,
                            row["store_name"],
                            row["store_type"],
                            row["location"],
                            row["website_url"]
                        ))
                        seen_stores.add(store_id)

                    if item_id not in seen_items:
                        cur.execute("""
                            INSERT INTO items (
                                item_id, store_id, item_name, clothing_type,
                                price, product_url, image_url
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            item_id,
                            store_id,
                            row["item_name"],
                            row["clothing_type"],
                            price,
                            row["product_url"],
                            row["image_url"]
                        ))
                        seen_items.add(item_id)

                    cur.execute("""
                        INSERT INTO reviews (review_id, item_id, review_count, average_rating)
                        VALUES (?, ?, ?, ?)
                    """, (
                        review_id,
                        item_id,
                        review_count,
                        average_rating
                    ))
                    review_id += 1

                except ValueError:
                    print("Skipped one bad row because of a type error.")
                except KeyError as e:
                    print("Missing CSV column:", e)

        conn.commit()
        print("CSV data loaded successfully.")

    except FileNotFoundError:
        print("CSV file not found. Make sure it is in the same folder as main.py.")
    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def add_store():
    try:
        store_id = int(input("Enter store id: "))
        store_name = input("Enter store name: ").strip()
        store_type = input("Enter store type: ").strip()
        location = input("Enter location: ").strip()
        website_url = input("Enter website url: ").strip()

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO stores (store_id, store_name, store_type, location, website_url)
            VALUES (?, ?, ?, ?, ?)
        """, (store_id, store_name, store_type, location, website_url))

        conn.commit()
        print("Store added successfully.")

    except ValueError:
        print("Store id must be a number.")
    except sqlite3.IntegrityError:
        print("That store id already exists.")
    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def add_item():
    try:
        item_id = int(input("Enter item id: "))
        store_id = int(input("Enter store id: "))
        item_name = input("Enter item name: ").strip()
        clothing_type = input("Enter clothing type: ").strip()
        price = float(input("Enter price: "))
        product_url = input("Enter product url: ").strip()
        image_url = input("Enter image url: ").strip()

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM stores WHERE store_id = ?", (store_id,))
        if not cur.fetchone():
            print("That store id does not exist.")
            conn.close()
            return

        cur.execute("""
            INSERT INTO items (
                item_id, store_id, item_name, clothing_type,
                price, product_url, image_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id, store_id, item_name, clothing_type,
            price, product_url, image_url
        ))

        conn.commit()
        print("Item added successfully.")

    except ValueError:
        print("Item id, store id, and price must be valid numbers.")
    except sqlite3.IntegrityError:
        print("That item id already exists.")
    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def add_review():
    try:
        review_id = int(input("Enter review id: "))
        item_id = int(input("Enter item id: "))
        review_count = int(input("Enter review count: "))
        average_rating = float(input("Enter average rating: "))

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
        if not cur.fetchone():
            print("That item id does not exist.")
            conn.close()
            return

        cur.execute("""
            INSERT INTO reviews (review_id, item_id, review_count, average_rating)
            VALUES (?, ?, ?, ?)
        """, (review_id, item_id, review_count, average_rating))

        conn.commit()
        print("Review added successfully.")

    except ValueError:
        print("Review id, item id, review count, and average rating must be valid numbers.")
    except sqlite3.IntegrityError:
        print("That review id already exists.")
    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def view_all_stores():
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM stores ORDER BY store_id")
        rows = cur.fetchall()

        if rows:
            for row in rows:
                print(row[1])
        else:
            print("No stores found.")

    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def view_all_items():
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM items ORDER BY item_id")
        rows = cur.fetchall()

        if rows:
            for row in rows:
                print(row[2])
        else:
            print("No items found.")

    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def view_all_reviews():
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT r.review_id, i.item_name, r.average_rating, r.review_count
            FROM reviews r
            JOIN items i ON r.item_id = i.item_id
            ORDER BY r.review_id
        """)
        rows = cur.fetchall()

        if rows:
            for row in rows:
                print(f"Review {row[0]} — {row[1]}: {row[2]} stars ({row[3]} reviews)")
        else:
            print("No reviews found.")

    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def update_store():
    try:
        store_id = int(input("Enter store id to update: "))

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM stores WHERE store_id = ?", (store_id,))
        row = cur.fetchone()

        if not row:
            print("Store not found.")
            conn.close()
            return

        new_name = input(f"New store name ({row[1]}): ").strip()
        new_type = input(f"New store type ({row[2]}): ").strip()
        new_location = input(f"New location ({row[3]}): ").strip()
        new_website = input(f"New website url ({row[4]}): ").strip()

        if new_name == "":
            new_name = row[1]
        if new_type == "":
            new_type = row[2]
        if new_location == "":
            new_location = row[3]
        if new_website == "":
            new_website = row[4]

        cur.execute("""
            UPDATE stores
            SET store_name = ?, store_type = ?, location = ?, website_url = ?
            WHERE store_id = ?
        """, (new_name, new_type, new_location, new_website, store_id))

        conn.commit()
        print("Store updated successfully.")

    except ValueError:
        print("Store id must be a number.")
    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def update_item():
    try:
        item_id = int(input("Enter item id to update: "))

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
        row = cur.fetchone()

        if not row:
            print("Item not found.")
            conn.close()
            return

        new_store_id = input(f"New store id ({row[1]}): ").strip()
        new_name = input(f"New item name ({row[2]}): ").strip()
        new_type = input(f"New clothing type ({row[3]}): ").strip()
        new_price = input(f"New price ({row[4]}): ").strip()
        new_product = input(f"New product url ({row[5]}): ").strip()
        new_image = input(f"New image url ({row[6]}): ").strip()

        if new_store_id == "":
            new_store_id = row[1]
        else:
            new_store_id = int(new_store_id)
            cur.execute("SELECT * FROM stores WHERE store_id = ?", (new_store_id,))
            if not cur.fetchone():
                print("That store id does not exist.")
                conn.close()
                return

        if new_name == "":
            new_name = row[2]
        if new_type == "":
            new_type = row[3]
        if new_price == "":
            new_price = row[4]
        else:
            new_price = float(new_price)
        if new_product == "":
            new_product = row[5]
        if new_image == "":
            new_image = row[6]

        cur.execute("""
            UPDATE items
            SET store_id = ?, item_name = ?, clothing_type = ?, price = ?, product_url = ?, image_url = ?
            WHERE item_id = ?
        """, (new_store_id, new_name, new_type, new_price, new_product, new_image, item_id))

        conn.commit()
        print("Item updated successfully.")

    except ValueError:
        print("One of the values was the wrong type.")
    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def update_review():
    try:
        review_id = int(input("Enter review id to update: "))

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM reviews WHERE review_id = ?", (review_id,))
        row = cur.fetchone()

        if not row:
            print("Review not found.")
            conn.close()
            return

        new_item_id = input(f"New item id ({row[1]}): ").strip()
        new_count = input(f"New review count ({row[2]}): ").strip()
        new_rating = input(f"New average rating ({row[3]}): ").strip()

        if new_item_id == "":
            new_item_id = row[1]
        else:
            new_item_id = int(new_item_id)
            cur.execute("SELECT * FROM items WHERE item_id = ?", (new_item_id,))
            if not cur.fetchone():
                print("That item id does not exist.")
                conn.close()
                return

        if new_count == "":
            new_count = row[2]
        else:
            new_count = int(new_count)

        if new_rating == "":
            new_rating = row[3]
        else:
            new_rating = float(new_rating)

        cur.execute("""
            UPDATE reviews
            SET item_id = ?, review_count = ?, average_rating = ?
            WHERE review_id = ?
        """, (new_item_id, new_count, new_rating, review_id))

        conn.commit()
        print("Review updated successfully.")

    except ValueError:
        print("One of the values was the wrong type.")
    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def delete_store():
    try:
        store_id = int(input("Enter store id to delete: "))

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM items WHERE store_id = ?", (store_id,))
        if cur.fetchall():
            print("Cannot delete this store because items are still linked to it.")
            conn.close()
            return

        cur.execute("DELETE FROM stores WHERE store_id = ?", (store_id,))
        conn.commit()

        if cur.rowcount == 0:
            print("No store found with that id.")
        else:
            print("Store deleted successfully.")

    except ValueError:
        print("Store id must be a number.")
    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def delete_item():
    try:
        item_id = int(input("Enter item id to delete: "))

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM reviews WHERE item_id = ?", (item_id,))
        if cur.fetchall():
            print("Cannot delete this item because reviews are still linked to it.")
            conn.close()
            return

        cur.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
        conn.commit()

        if cur.rowcount == 0:
            print("No item found with that id.")
        else:
            print("Item deleted successfully.")

    except ValueError:
        print("Item id must be a number.")
    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def delete_review():
    try:
        review_id = int(input("Enter review id to delete: "))

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM reviews WHERE review_id = ?", (review_id,))
        conn.commit()

        if cur.rowcount == 0:
            print("No review found with that id.")
        else:
            print("Review deleted successfully.")

    except ValueError:
        print("Review id must be a number.")
    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def run_search(query, values):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute(query, values)
        rows = cur.fetchall()

        if rows:
            for row in rows:
                print(row)
        else:
            print("No results found.")

    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def search_store_name():
    value = input("Enter store name: ").strip()
    run_search("SELECT * FROM stores WHERE store_name LIKE ?", ('%' + value + '%',))


def search_store_type():
    value = input("Enter store type: ").strip()
    run_search("SELECT * FROM stores WHERE store_type LIKE ?", ('%' + value + '%',))


def search_item_name():
    value = input("Enter item name: ").strip()
    run_search("SELECT * FROM items WHERE item_name LIKE ?", ('%' + value + '%',))


def search_clothing_type():
    value = input("Enter clothing type: ").strip()
    run_search("SELECT * FROM items WHERE clothing_type LIKE ?", ('%' + value + '%',))


def search_price_range():
    try:
        low = float(input("Enter minimum price: "))
        high = float(input("Enter maximum price: "))
        run_search("SELECT * FROM items WHERE price BETWEEN ? AND ?", (low, high))
    except ValueError:
        print("Price values must be numbers.")


def search_average_rating():
    try:
        value = float(input("Enter minimum average rating: "))
        run_search("SELECT * FROM reviews WHERE average_rating >= ?", (value,))
    except ValueError:
        print("Average rating must be a number.")


def search_review_count():
    try:
        value = int(input("Enter minimum review count: "))
        run_search("SELECT * FROM reviews WHERE review_count >= ?", (value,))
    except ValueError:
        print("Review count must be a number.")


def search_menu():
    while True:
        print("\nSearch Menu")
        print("1. Search by store name")
        print("2. Search by store type")
        print("3. Search by item name")
        print("4. Search by clothing type")
        print("5. Search by price range")
        print("6. Search by average rating")
        print("7. Search by review count")
        print("8. Back")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            search_store_name()
        elif choice == "2":
            search_store_type()
        elif choice == "3":
            search_item_name()
        elif choice == "4":
            search_clothing_type()
        elif choice == "5":
            search_price_range()
        elif choice == "6":
            search_average_rating()
        elif choice == "7":
            search_review_count()
        elif choice == "8":
            break
        else:
            print("Invalid choice.")
            
def stat_analysis():
    try:
        conn = connect_db()
        cur = conn.cursor()
        
        cur.execute("SELECT MIN(price), MAX(price), AVG(price) FROM items")
        result = cur.fetchone()

        if result[0] is None:
            print("\nPrice Stats:\nNo data available.")
        else:
            min_price, max_price, avg_price = result
            print(f"\nPrice Stats:\nMin: ${min_price:.2f}, Max: ${max_price:.2f}, Avg: ${avg_price:.2f}")
        
        cur.execute("SELECT MIN(average_rating), MAX(average_rating), AVG(average_rating) FROM reviews")
        result = cur.fetchone()

        if result[0] is None:
            print("\nRating Stats:\nNo data available.")
        else:
            min_rating, max_rating, avg_rating = result
            print(f"\nRating Stats:\nMin: {min_rating:.2f}, Max: {max_rating:.2f}, Avg: {avg_rating:.2f}")
        
        cur.execute("SELECT MIN(review_count), MAX(review_count), AVG(review_count) FROM reviews")
        result = cur.fetchone()

        if result[0] is None:
            print("\nReview Count Stats:\nNo data available.")
        else:
            min_reviews, max_reviews, avg_reviews = result
            print(f"\nReview Count Stats:\nMin: {min_reviews}, Max: {max_reviews}, Avg: {avg_reviews:.2f}")

        
    except sqlite3.Error as e:
        print("Database error:", e)
    finally:
        if "conn" in locals():
            conn.close()


def menu():
    while True:
        print("\nClothing Store Database Menu")
        print("1. Create database")
        print("2. Load CSV data")
        print("3. Add store")
        print("4. Add item")
        print("5. Add review")
        print("6. View all stores")
        print("7. View all items")
        print("8. View all reviews")
        print("9. Update store")
        print("10. Update item")
        print("11. Update review")
        print("12. Delete store")
        print("13. Delete item")
        print("14. Delete review")
        print("15. Search/query menu")
        print("16. Statistical Analysis")
        print("17. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            create_database()
        elif choice == "2":
            load_csv_data()
        elif choice == "3":
            add_store()
        elif choice == "4":
            add_item()
        elif choice == "5":
            add_review()
        elif choice == "6":
            view_all_stores()
        elif choice == "7":
            view_all_items()
        elif choice == "8":
            view_all_reviews()
        elif choice == "9":
            update_store()
        elif choice == "10":
            update_item()
        elif choice == "11":
            update_review()
        elif choice == "12":
            delete_store()
        elif choice == "13":
            delete_item()
        elif choice == "14":
            delete_review()
        elif choice == "15":
            search_menu()
        elif choice == "16":
            stat_analysis()
        elif choice == "17":
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 16.")


init_db()
menu()