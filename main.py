from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, text

app = Flask(__name__)
conn_str = "mysql://root:cset155@localhost/boatdb"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)

@app.route('/boats/')
@app.route('/boats/<int:page>')
def get_boats(page=1):
    page = int(page)
    per_page = 10
    order_by = request.args.get('order', 'id')
    if order_by not in ['id', 'name', 'rental_price']:
        order_by = 'id'
    boats = conn.execute(
        text(f"SELECT * FROM boats ORDER BY {order_by} LIMIT :limit OFFSET :offset"),
        {"limit": per_page, "offset": (page-1)*per_page}
    ).all()
    return render_template('boats.html', boats=boats, page=page, per_page=per_page, order_by=order_by)

@app.route('/boats/<int:boat_id>/detail')
def boat_detail(boat_id):
    boat = conn.execute(
        text("SELECT * FROM boats WHERE id = :id"),
        {"id": boat_id}
    ).first()
    if not boat:
        return f"No boat found with ID {boat_id}", 404
    return render_template('boat_detail.html', boat=boat)

@app.route('/create', methods=['GET', 'POST'])
def create_boat():
    if request.method == 'POST':
        try:
            conn.execute(
                text("INSERT INTO boats values (:id, :name, :type, :owner_id, :rental_price)"),
                request.form
            )
            return render_template('boats_create.html', success="Boat added successfully!", error=None)
        except Exception as e:
            error = e.orig.args[1] if hasattr(e, 'orig') else str(e)
            return render_template('boats_create.html', success=None, error=error)
    return render_template('boats_create.html')

@app.route('/search', methods=['GET'])
def search_get_request():
    return render_template('boats_search.html')

@app.route('/search', methods=['POST'])
def search_boat():
    boat_id = request.form.get('id_filter')
    search_term = request.form.get('search_term')
    type_filter = request.form.get('type_filter')
    min_price = request.form.get('min_price')
    max_price = request.form.get('max_price')

    query = "SELECT * FROM boats WHERE 1=1"
    params = {}

    if boat_id:
        query += " AND id = :boat_id"
        params["boat_id"] = boat_id
    if search_term:
        query += " AND name LIKE :term"
        params["term"] = f"%{search_term}%"
    if type_filter:
        query += " AND type = :type_filter"
        params["type_filter"] = type_filter
    if min_price:
        query += " AND rental_price >= :min_price"
        params["min_price"] = min_price
    if max_price:
        query += " AND rental_price <= :max_price"
        params["max_price"] = max_price

    results = conn.execute(text(query), params).all()

    return render_template(
        'boats_search.html',
        results=results,
        id_filter=boat_id,
        search_term=search_term,
        type_filter=type_filter,
        min_price=min_price,
        max_price=max_price
    )

@app.route('/update/<int:boat_id>', methods=['GET', 'POST'])
def update_boat(boat_id):
    boat = conn.execute(
        text("SELECT * FROM boats WHERE id = :id"),
        {"id": boat_id}
    ).first()
    if not boat:
        return f"No boat found with ID {boat_id}", 404
    if request.method == 'POST':
        try:
            conn.execute(
                text("""
                    UPDATE boats 
                    SET name=:name, type=:type, owner_id=:owner_id, rental_price=:rental_price
                    WHERE id=:id
                """),
                {
                    "name": request.form['name'],
                    "type": request.form['type'],
                    "owner_id": request.form['owner_id'],
                    "rental_price": request.form['rental_price'],
                    "id": boat_id
                }
            )
            return render_template('boats_update.html', boat=request.form, success="Boat updated successfully!", error=None)
        except Exception as e:
            error = e.orig.args[1] if hasattr(e, 'orig') else str(e)
            return render_template('boats_update.html', boat=request.form, success=None, error=error)
    return render_template('boats_update.html', boat=boat)

@app.route('/delete', methods=['GET', 'POST'])
def delete_boat():
    if request.method == 'POST':
        boat_id = request.form.get('id')
        try:
            conn.execute(text("DELETE FROM boats WHERE id = :id"), {"id": boat_id})
            return render_template('boats_delete.html', success=f"Boat {boat_id} deleted successfully!", error=None)
        except Exception as e:
            error = e.orig.args[1] if hasattr(e, 'orig') else str(e)
            return render_template('boats_delete.html', success=None, error=error)
    return render_template('boats_delete.html')

@app.route('/search_delete', methods=['GET', 'POST'])
def search_delete_by_id():
    if request.method == 'POST':
        boat_id = request.form.get('boat_id')
        if not boat_id:
            return render_template('boats_search_delete.html', boat=None, error="Please enter a Boat ID", success=None)
        boat = conn.execute(text("SELECT * FROM boats WHERE id = :id"), {"id": boat_id}).first()
        if not boat:
            return render_template('boats_search_delete.html', boat=None, error="No boat found with that ID", success=None)
        if 'delete' in request.form:
            try:
                conn.execute(text("DELETE FROM boats WHERE id = :id"), {"id": boat_id})
                return render_template('boats_search_delete.html', boat=None, error=None, success=f"Boat {boat_id} deleted successfully!")
            except Exception as e:
                error = e.orig.args[1] if hasattr(e, 'orig') else str(e)
                return render_template('boats_search_delete.html', boat=None, error=error, success=None)
        return render_template('boats_search_delete.html', boat=boat, error=None, success=None)
    return render_template('boats_search_delete.html', boat=None, error=None, success=None)

if __name__ == '__main__':
    app.run(debug=True)