from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from models import db
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.user import User
from models.reservation import Reservation
from datetime import datetime


admin = Blueprint('admin', __name__)

@admin.route('/admin/dashboard')
def dashboard():
    return render_template('admin_dashboard.html')


@admin.route('/admin/add_lot', methods=['GET', 'POST'])
def add_lot():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        pin_code = request.form['pin_code']
        max_spots = request.form['max_spots']
        new_lot = ParkingLot(
            prime_location_name=name,
            price=float(price),
            pin_code=pin_code,
            maximum_number_of_spots=int(max_spots)
        )
        db.session.add(new_lot)
        db.session.commit()

        # Create parking spots automatically
        for i in range(int(max_spots)):
            new_spot = ParkingSpot(lot_id=new_lot.id, status='A')
            db.session.add(new_spot)
        
        db.session.commit()

        
        flash('Parking lot created successfully!', 'success')
        return redirect(url_for('admin.view_lots'))
    
    

    
    return render_template('add_lot.html')

@admin.route('/admin/view_lots')
def view_lots():
    all_lots = ParkingLot.query.all()
    return render_template('view_lots.html', lots=all_lots)

@admin.route('/admin/view_users')
def view_users():
    all_users = User.query.all()
    return render_template('view_users.html', users=all_users)

@admin.route('/admin/view_spots')
def view_spots():
    all_spots = ParkingSpot.query.all()
    spots_data = []
    
    for spot in all_spots:
        lot = ParkingLot.query.get(spot.lot_id)
        
        # Get vehicle details if spot is occupied
        vehicle_info = None
        if spot.status == 'O':
            # Find active reservation for this spot
            active_reservation = Reservation.query.filter_by(
                spot_id=spot.id, 
                leaving_timestamp=None
            ).first()
            
            if active_reservation:
                user = User.query.get(active_reservation.user_id)
                vehicle_info = {
                    'vehicle_number': active_reservation.vehicle_number,
                    'vehicle_model': active_reservation.vehicle_model,
                    'user_name': user.full_name if user else 'Unknown',
                    'parked_since': active_reservation.parking_timestamp
                }
        
        spots_data.append({
            'spot': spot,
            'lot': lot,
            'vehicle_info': vehicle_info
        })
    
    return render_template('view_spots.html', spots=spots_data)

@admin.route('/admin/delete_lot/<int:lot_id>')
def delete_lot(lot_id):
    lot = ParkingLot.query.get(lot_id)
    # Check if all spots are available (empty)
    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot_id, status='O').count()
    
    if occupied_spots > 0:
        flash (f"Cannot delete {lot.prime_location_name}! {occupied_spots} spots are occupied." , 'danger')
        return redirect(url_for('admin.view_lots'))
    
    # Delete all spots first, then the lot
    ParkingSpot.query.filter_by(lot_id=lot_id).delete()
    db.session.delete(lot)
    db.session.commit()
    
    #return f"Deleted {lot.prime_location_name} and all its spots successfully!"
    flash (f"Deleted {lot.prime_location_name} and all its spots successfully!" , 'success')
    return redirect(url_for('admin.view_lots'))



@admin.route('/admin/all_parking_records')
def all_parking_records():
    all_reservations = Reservation.query.all()
    
    if not all_reservations:
        return render_template('parking_records.html', records=[], summary={
            'total_sessions': 0,
            'completed_sessions': 0,
            'active_sessions': 0,
            'total_revenue': 0
        })
    
    # Summary calculations
    total_sessions = len(all_reservations)
    completed_sessions = len([r for r in all_reservations if r.leaving_timestamp])
    active_sessions = total_sessions - completed_sessions
    total_revenue = sum([r.parking_cost or 0 for r in all_reservations])
    
    # Prepare records data
    # Prepare records data
    records_data = []
    for reservation in all_reservations:
        spot = ParkingSpot.query.get(reservation.spot_id)
        
        # Skip if spot was deleted
        if not spot:
            continue
            
        lot = ParkingLot.query.get(spot.lot_id)
        
        # Skip if lot was deleted
        if not lot:
            continue
            
        user = User.query.get(reservation.user_id)
        
        # Skip if user was deleted
        if not user:
            continue
        
        duration_minutes = None
        if reservation.leaving_timestamp:
            duration = reservation.leaving_timestamp - reservation.parking_timestamp
            duration_minutes = int(duration.total_seconds() / 60)
        
        records_data.append({
            'reservation': reservation,
            'spot': spot,
            'lot': lot,
            'user': user,
            'duration_minutes': duration_minutes
        })
    
    summary = {
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'active_sessions': active_sessions,
        'total_revenue': total_revenue
    }
    
    return render_template('parking_records.html', records=records_data, summary=summary)


@admin.route('/admin/charts')
def charts():
    # Get chart data
    total_spots = ParkingSpot.query.count()
    occupied_spots = ParkingSpot.query.filter_by(status='O').count()
    available_spots = total_spots - occupied_spots
    
    # Get lots data
    all_lots = ParkingLot.query.all()
    lots_data = []
    max_spots = 0
    
    for lot in all_lots:
        lots_data.append({
            'name': lot.prime_location_name,
            'total_spots': lot.maximum_number_of_spots
        })
        if lot.maximum_number_of_spots > max_spots:
            max_spots = lot.maximum_number_of_spots
    
    chart_data = {
        'total_spots': total_spots,
        'available_spots': available_spots,
        'occupied_spots': occupied_spots,
        'lots': lots_data,
        'max_spots': max_spots if max_spots > 0 else 1
    }
    
    return render_template('admin_charts.html', chart_data=chart_data)

#just to push


@admin.route('/admin/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return redirect(url_for('admin.view_lots'))
    
    if request.method == 'POST':
        # Update basic details (always safe)
        lot.prime_location_name = request.form['name']
        lot.price = float(request.form['price'])
        lot.pin_code = request.form['pin_code']
        
        # Handle spot count changes with validation
        old_spots = lot.maximum_number_of_spots
        new_spots = int(request.form['max_spots'])
        
        if new_spots > old_spots:
            # Add more spots (always safe)
            for i in range(new_spots - old_spots):
                new_spot = ParkingSpot(lot_id=lot.id, status='A')
                db.session.add(new_spot)
            lot.maximum_number_of_spots = new_spots
            
        elif new_spots < old_spots:
            # Check if we can safely reduce spots
            occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
            
            if new_spots < occupied_count:
                flash(f'Cannot reduce spots! {occupied_count} spots are currently occupied. Minimum spots required: {occupied_count}', 'danger')
                occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
                return render_template('edit_lot.html', lot=lot, occupied_count=occupied_count)
            
            # Safe to reduce - remove available spots only
            spots_to_remove = old_spots - new_spots
            available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').limit(spots_to_remove).all()
            
            for spot in available_spots:
                db.session.delete(spot)
            
            lot.maximum_number_of_spots = new_spots
        
        db.session.commit()
        flash('Parking lot updated successfully!', 'success')
        return redirect(url_for('admin.view_lots'))
    
    # Get current occupation info for display
    occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
    return render_template('edit_lot.html', lot=lot, occupied_count=occupied_count) 
