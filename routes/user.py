from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from models import db
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.reservation import Reservation
from datetime import datetime

user = Blueprint('user', __name__)

@user.route('/user/dashboard')
def dashboard():
    return render_template('user_dashboard.html')


@user.route('/user/view_lots')
def view_lots():
    all_lots = ParkingLot.query.all()
    lots_data = []
    
    for lot in all_lots:
        available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
        lots_data.append({
            'lot': lot,
            'available_spots': available_spots
        })
    
    return render_template('user_view_lots.html', lots=lots_data)

@user.route('/user/reserve_form/<int:lot_id>')
def reserve_form(lot_id):
    user_id = session.get('user_id')
    
    # Check if user already has an active reservation
    existing_reservation = Reservation.query.filter_by(user_id=user_id, leaving_timestamp=None).first()
    if existing_reservation:
        flash('You already have an active reservation! Please complete it first.', 'danger')
        return redirect(url_for('user.view_lots'))
    
    # Get lot details
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        flash('Parking lot not found!', 'danger')
        return redirect(url_for('user.view_lots'))
    
    # Check available spots
    available_spots = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').count()
    if available_spots == 0:
        flash('Sorry, no available spots in this parking lot!', 'danger')
        return redirect(url_for('user.view_lots'))
    
    return render_template('reserve_form.html', lot=lot, available_spots=available_spots)

@user.route('/user/reserve_spot/<int:lot_id>', methods=['POST'])
def reserve_spot(lot_id):
    user_id = session.get('user_id')
    
    # Check if user already has an active reservation
    existing_reservation = Reservation.query.filter_by(user_id=user_id, leaving_timestamp=None).first()
    if existing_reservation:
        flash('You already have an active reservation! Please complete it first.', 'danger')
        return redirect(url_for('user.view_lots'))
    
    # Find first available spot in this lot
    available_spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()
    
    if not available_spot:
        flash('Sorry, no available spots in this parking lot!', 'danger')
        return redirect(url_for('user.view_lots'))
    
    # Get vehicle details from form
    vehicle_number = request.form.get('vehicle_number')
    vehicle_model = request.form.get('vehicle_model')
    
    # Create reservation with vehicle details
    new_reservation = Reservation(
        spot_id=available_spot.id, 
        user_id=user_id,
        vehicle_number=vehicle_number,
        vehicle_model=vehicle_model
    )
    
    # Update spot status to occupied
    available_spot.status = 'O'
    
    # Save to database
    db.session.add(new_reservation)
    db.session.commit()
    
    # Flash success message
    flash(f'Successfully reserved spot {available_spot.id} for vehicle {vehicle_number}!', 'success')
    return redirect(url_for('user.my_reservation'))

@user.route('/user/my_reservation')
def my_reservation():
    user_id = session.get('user_id')
    # Find user's current reservation (no leaving timestamp)
    current_reservation = Reservation.query.filter_by(user_id=user_id, leaving_timestamp=None).first()
    
    if not current_reservation:
        return render_template('user_reservation.html', reservation=None)
    
    spot = ParkingSpot.query.get(current_reservation.spot_id)
    lot = ParkingLot.query.get(spot.lot_id)
    
    reservation_data = {
        'reservation': current_reservation,
        'spot': spot,
        'lot': lot
    }
    
    return render_template('user_reservation.html', reservation=reservation_data)


@user.route('/user/occupy_spot')
def occupy_spot():
    user_id = session.get('user_id')
    reservation = Reservation.query.filter_by(user_id=user_id, leaving_timestamp=None).first()
    
    if not reservation:
        flash('No active reservation found!', 'danger')
        return redirect(url_for('user.dashboard'))
    
    flash(f'Spot {reservation.spot_id} occupied! You can now park your vehicle.', 'success')
    return redirect(url_for('user.my_reservation'))


@user.route('/user/release_spot')
def release_spot():
    user_id = session.get('user_id')
    reservation = Reservation.query.filter_by(user_id=user_id, leaving_timestamp=None).first()
    
    if not reservation:
        flash('No active reservation found!', 'danger')
        return redirect(url_for('user.dashboard'))
    
    # Update leaving timestamp
    reservation.leaving_timestamp = datetime.now()
    
    # Calculate cost
    spot = ParkingSpot.query.get(reservation.spot_id)
    lot = ParkingLot.query.get(spot.lot_id)
    
    duration = reservation.leaving_timestamp - reservation.parking_timestamp
    duration_hours = duration.total_seconds() / 3600  # Convert to hours
    total_cost = duration_hours * lot.price
    
    reservation.parking_cost = round(total_cost, 2)
    
    # Make spot available again
    spot.status = 'A'
    
    db.session.commit()
    
    flash(f'Successfully released spot {reservation.spot_id}! Total cost: ₹{reservation.parking_cost}', 'success')
    return redirect(url_for('user.parking_history'))


@user.route('/user/parking_history')
def parking_history():
    user_id = session.get('user_id')
    all_reservations = Reservation.query.filter_by(user_id=user_id).all()
    
    if not all_reservations:
        return render_template('user_history.html', history=[], total_cost=0)
    
    history_data = []
    total_cost = 0
    
    for reservation in all_reservations:
        spot = ParkingSpot.query.get(reservation.spot_id)
        
        # Skip this reservation if spot was deleted
        if not spot:
            continue
            
        lot = ParkingLot.query.get(spot.lot_id)
        
        # Skip this reservation if lot was deleted
        if not lot:
            continue
        
        duration_minutes = None
        if reservation.leaving_timestamp:
            duration = reservation.leaving_timestamp - reservation.parking_timestamp
            duration_minutes = int(duration.total_seconds() / 60)
        
        # Add to total cost
        if reservation.parking_cost:
            total_cost += reservation.parking_cost
        
        history_data.append({
            'reservation': reservation,
            'spot': spot,
            'lot': lot,
            'duration_minutes': duration_minutes
        })
    
    return render_template('user_history.html', history=history_data, total_cost=round(total_cost, 2))





@user.route('/user/charts')
def charts():
    user_id = session.get('user_id')
    all_reservations = Reservation.query.filter_by(user_id=user_id).all()
    
    # Calculate user statistics
    total_sessions = len(all_reservations)
    completed_sessions = len([r for r in all_reservations if r.leaving_timestamp])
    active_sessions = total_sessions - completed_sessions
    total_spent = sum([r.parking_cost or 0 for r in all_reservations])
    
    user_data = {
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'active_sessions': active_sessions,
        'total_spent': round(total_spent, 2)
    }
    
    return render_template('user_charts.html', user_data=user_data)