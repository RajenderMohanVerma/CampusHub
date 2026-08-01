"""Notifications Controller providing JSON API badge refresh and centralized inbox management."""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.blueprints.notifications import notifications_bp
from app.models import Notification


@notifications_bp.route('/inbox')
@login_required
def inbox():
    """Detailed in-app notification center and telemetry alerts."""
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(100).all()
    unread_count = sum(1 for n in notifs if not n.is_read)
    return render_template('notifications/inbox.html', notifs=notifs, unread_count=unread_count)


@notifications_bp.route('/api/unread-count')
@login_required
def api_unread_count():
    """JSON endpoint for real-time frontend badge updates without reloading."""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'unread_count': count, 'status': 'success'})


@notifications_bp.route('/api/latest')
@login_required
def api_latest():
    """JSON endpoint returning latest unread alerts for dynamic dropdown notification feed."""
    notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'category': n.category,
        'link_url': n.link_url or url_for('notifications.inbox'),
        'timestamp': n.created_at.strftime('%I:%M %p, %b %d')
    } for n in notifs]
    return jsonify({'notifications': data, 'count': len(data)})


@notifications_bp.route('/read/<int:notif_id>', methods=['POST', 'GET'])
@login_required
def mark_read(notif_id):
    """Mark single notification read and route user to action link."""
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    if not notif.is_read:
        notif.is_read = True
        db.session.commit()
        
    if notif.link_url:
        return redirect(notif.link_url)
    return redirect(request.referrer or url_for('notifications.inbox'))


@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    """Clear all unread notification badges for the current account."""
    unreads = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for u in unreads:
        u.is_read = True
    db.session.commit()
    flash("All notification telemetry items marked as read.", "success")
    return redirect(request.referrer or url_for('notifications.inbox'))
