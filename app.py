from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import math
from datetime import datetime
import os

app = Flask(__name__)

# Load initial product data
def load_product_data():
    df = pd.read_csv('data/products.csv')
    return df.to_dict('records')

# Load or initialize inventory data
def load_inventory_data():
    if os.path.exists('data/inventory.json'):
        with open('data/inventory.json', 'r') as f:
            return json.load(f)
    return {}

# Save inventory data
def save_inventory_data(inventory):
    with open('data/inventory.json', 'w') as f:
        json.dump(inventory, f)

def load_movement_history():
    if os.path.exists('data/movement_history.json'):
        with open('data/movement_history.json', 'r') as f:
            return json.load(f)
    return []

def save_movement_history(history):
    with open('data/movement_history.json', 'w') as f:
        json.dump(history, f)

# Initialize data
PRODUCTS = load_product_data()
INVENTORY = load_inventory_data()
MOVEMENT_HISTORY = load_movement_history()

# Constants
STORAGE_COST_PER_PALLET = 7.50
MOVEMENT_COST_PER_PALLET = 4.25

@app.route('/')
def index():
    return render_template('inventory.html')

@app.route('/api/products')
def get_products():
    return jsonify(PRODUCTS)

@app.route('/api/inventory')
def get_inventory():
    return jsonify(INVENTORY)

@app.route('/api/update_stock', methods=['POST'])
def update_stock():
    data = request.json
    sage_id = data['sageId']
    quantity = int(data['quantity'])  # Positive for import, negative for export
    
    # Find product details
    product = next((p for p in PRODUCTS if p['Sage ID'] == sage_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Calculate pallets
    cases_per_pallet = product['Cases Per Pallet']
    pallets_needed = math.ceil(abs(quantity) / cases_per_pallet)

    # Initialize inventory record if it doesn't exist
    if sage_id not in INVENTORY:
        INVENTORY[sage_id] = {
            'current_stock': 0,
            'pallets_moved': 0,
            'max_pallets': 0
        }

    # Update inventory
    INVENTORY[sage_id]['current_stock'] += quantity
    INVENTORY[sage_id]['pallets_moved'] += pallets_needed
    
    # Update max pallets if current stock requires more pallets
    current_pallets = math.ceil(INVENTORY[sage_id]['current_stock'] / cases_per_pallet)
    INVENTORY[sage_id]['max_pallets'] = max(INVENTORY[sage_id]['max_pallets'], current_pallets)

    # Save updated inventory
    save_inventory_data(INVENTORY)

    # Record movement in history
    movement_record = {
        'date': data.get('date') or datetime.now().isoformat(),
        'sage_id': sage_id,
        'quantity': quantity,
        'type': 'import' if quantity > 0 else 'export'
    }
    MOVEMENT_HISTORY.append(movement_record)
    save_movement_history(MOVEMENT_HISTORY)
    
    return jsonify(INVENTORY[sage_id])

@app.route('/api/delete_movement', methods=['POST'])
def delete_movement():
    data = request.json
    date_to_delete = data['date']
    
    global MOVEMENT_HISTORY, INVENTORY
    
    # Find the movement record
    record = next((r for r in MOVEMENT_HISTORY if r['date'] == date_to_delete), None)
    if record:
        # Reverse the stock change
        sage_id = record['sage_id']
        quantity = -record['quantity']  # Reverse the quantity
        
        if sage_id in INVENTORY:
            # Update current stock
            INVENTORY[sage_id]['current_stock'] += quantity
            
            # Update pallets moved
            product = next((p for p in PRODUCTS if p['Sage ID'] == sage_id), None)
            if product:
                pallets = math.ceil(abs(record['quantity']) / product['Cases Per Pallet'])
                INVENTORY[sage_id]['pallets_moved'] -= pallets
                
                # Recalculate max pallets
                current_pallets = math.ceil(INVENTORY[sage_id]['current_stock'] / product['Cases Per Pallet'])
                INVENTORY[sage_id]['max_pallets'] = max(0, current_pallets)
        
        # Remove the record
        MOVEMENT_HISTORY.remove(record)
        save_movement_history(MOVEMENT_HISTORY)
        save_inventory_data(INVENTORY)
        
        return jsonify({'success': True})
    
    return jsonify({'error': 'Movement record not found'}), 404

@app.route('/api/movement_history')
def get_movement_history():
    month = request.args.get('month')
    if month:
        filtered_history = [
            record for record in MOVEMENT_HISTORY 
            if datetime.fromisoformat(record['date']).strftime('%Y-%m') <= month
        ]
        return jsonify(filtered_history)
    return jsonify(MOVEMENT_HISTORY)

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/api/monthly_stats')
def get_monthly_stats():
    month = request.args.get('month')
    if not month:
        return jsonify({'error': 'Month parameter required'}), 400

    # Filter movements for the specified month exactly
    monthly_movements = [
        record for record in MOVEMENT_HISTORY 
        if datetime.fromisoformat(record['date']).strftime('%Y-%m') == month
    ]

    # Calculate statistics
    pallets_imported = 0
    pallets_exported = 0
    max_pallets_stored = 0
    
    # Track running total of pallets for the month
    current_pallets = {}
    
    # Calculate only for the specified month
    for record in monthly_movements:
        product = next((p for p in PRODUCTS if p['Sage ID'] == record['sage_id']), None)
        if product:
            cases_per_pallet = product['Cases Per Pallet']
            sage_id = record['sage_id']
            if sage_id not in current_pallets:
                current_pallets[sage_id] = 0
            current_pallets[sage_id] += record['quantity']

    # Calculate statistics for the specified month
    for record in monthly_movements:
        product = next((p for p in PRODUCTS if p['Sage ID'] == record['sage_id']), None)
        if product:
            cases_per_pallet = product['Cases Per Pallet']
            pallets = math.ceil(abs(record['quantity']) / cases_per_pallet)
            
            if record['quantity'] > 0:
                pallets_imported += pallets
            else:
                pallets_exported += pallets

            # Update running total
            sage_id = record['sage_id']
            if sage_id not in current_pallets:
                current_pallets[sage_id] = 0
            current_pallets[sage_id] += record['quantity']
            
            # Calculate total pallets currently stored
            total_stored = sum(math.ceil(cases / product['Cases Per Pallet']) 
                             for sage_id, cases in current_pallets.items())
            max_pallets_stored = max(max_pallets_stored, total_stored)

    return jsonify({
        'pallets_imported': pallets_imported,
        'pallets_exported': pallets_exported,
        'max_pallets_stored': max_pallets_stored
    })

@app.route('/api/calculate_charges')
def calculate_charges():
    month = request.args.get('month')
    
    total_storage = 0
    total_movement = 0
    total_max_pallets = 861  # Initialize with August 2024 value
    
    if month:
        # Get all months up to and including the selected month
        all_months = []
        current_date = datetime.strptime('2024-08', '%Y-%m')  # Start from August 2024
        end_date = datetime.strptime(month, '%Y-%m')
        
        while current_date <= end_date:
            all_months.append(current_date.strftime('%Y-%m'))
            current_date = datetime(current_date.year + (current_date.month // 12), 
                                  ((current_date.month % 12) + 1) or 12, 
                                  1)
        
        # Calculate month by month
        for current_month in all_months[1:]:  # Skip first month as it's our base
            # Get movements for just this month
            monthly_movements = [
                record for record in MOVEMENT_HISTORY 
                if datetime.fromisoformat(record['date']).strftime('%Y-%m') == current_month
            ]
            
            # Calculate imports and exports for this month
            pallets_imported = 0
            pallets_exported = 0
            
            for record in monthly_movements:
                product = next((p for p in PRODUCTS if p['Sage ID'] == record['sage_id']), None)
                if product:
                    pallets = math.ceil(abs(record['quantity']) / product['Cases Per Pallet'])
                    if record['quantity'] > 0:
                        pallets_imported += pallets
                    else:
                        pallets_exported += pallets
                    total_movement += pallets * MOVEMENT_COST_PER_PALLET
            
            # Update running total of max pallets
            total_max_pallets = total_max_pallets + pallets_imported - pallets_exported
        
        # Calculate storage charge based on final max pallets
        total_storage = total_max_pallets * STORAGE_COST_PER_PALLET

    return jsonify({
        'storage_charge': total_storage,
        'movement_charge': total_movement,
        'total_charge': total_storage + total_movement,
        'total_max_pallets': total_max_pallets
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
