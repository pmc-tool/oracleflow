"""OracleFlow billing API endpoints — Stripe Checkout, Portal, Webhooks."""

import logging
import os

import stripe
from flask import jsonify, request

logger = logging.getLogger(__name__)
from sqlalchemy import select, func

from . import billing_bp
from app.oracleflow.database import get_session
from app.oracleflow.auth.middleware import require_auth
from app.oracleflow.auth.models import Organization, Subscription, User, PLAN_LIMITS, UserPreferences
from app.oracleflow.models.site import MonitoredSite
from app.oracleflow.models.signal import Simulation

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')

STRIPE_PRICE_IDS = {
    'scout': os.environ.get('STRIPE_PRICE_SCOUT', ''),
    'strategist': os.environ.get('STRIPE_PRICE_STRATEGIST', ''),
    'commander': os.environ.get('STRIPE_PRICE_COMMANDER', ''),
    'sovereign': os.environ.get('STRIPE_PRICE_SOVEREIGN', ''),
}


@billing_bp.route('/create-checkout', methods=['POST'])
@require_auth
def create_checkout():
    from flask import g
    db = get_session()
    try:
        data = request.get_json()
        plan = data.get('plan', 'scout')

        if plan not in STRIPE_PRICE_IDS or not STRIPE_PRICE_IDS[plan]:
            return jsonify({"success": False, "error": "Stripe not configured. Contact admin."}), 400

        org = db.execute(select(Organization).where(Organization.id == g.org_id)).scalar_one_or_none()
        if not org:
            return jsonify({"success": False, "error": "Organization not found"}), 404

        # Create or get Stripe customer
        if not org.stripe_customer_id:
            user = db.execute(select(User).where(User.id == g.user_id)).scalar_one_or_none()
            customer = stripe.Customer.create(
                email=user.email,
                name=org.name,
                metadata={"org_id": str(org.id)},
            )
            org.stripe_customer_id = customer.id
            db.commit()

        session = stripe.checkout.Session.create(
            customer=org.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{"price": STRIPE_PRICE_IDS[plan], "quantity": 1}],
            mode='subscription',
            success_url=request.host_url + 'dashboard?billing=success',
            cancel_url=request.host_url + 'dashboard?billing=cancel',
            metadata={"org_id": str(org.id), "plan": plan},
        )
        return jsonify({"success": True, "data": {"checkout_url": session.url}})
    except stripe.error.StripeError as e:
        logger.exception("Stripe checkout error: %s", e)
        return jsonify({"success": False, "error": "Payment processing error"}), 400
    except Exception as e:
        db.rollback()
        logger.exception("Billing API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@billing_bp.route('/portal', methods=['POST'])
@require_auth
def create_portal():
    from flask import g
    db = get_session()
    try:
        org = db.execute(select(Organization).where(Organization.id == g.org_id)).scalar_one_or_none()
        if not org or not org.stripe_customer_id:
            return jsonify({"success": False, "error": "No billing configured"}), 400

        session = stripe.billing_portal.Session.create(
            customer=org.stripe_customer_id,
            return_url=request.host_url + 'settings',
        )
        return jsonify({"success": True, "data": {"portal_url": session.url}})
    except Exception as e:
        logger.exception("Billing API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@billing_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig = request.headers.get('Stripe-Signature', '')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

    if not webhook_secret:
        return jsonify({"error": "Webhook not configured"}), 500

    try:
        event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
    except Exception:
        return jsonify({"error": "Invalid webhook"}), 400

    db = get_session()
    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            org_id = int(session['metadata']['org_id'])
            plan = session['metadata']['plan']
            sub_id = session.get('subscription', '')

            org = db.execute(select(Organization).where(Organization.id == org_id)).scalar_one_or_none()
            if org:
                limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['free'])
                org.plan = plan
                org.max_users = limits['max_users']
                org.max_sites = limits['max_sites']
                org.max_simulations_per_month = limits['max_simulations']

                sub = Subscription(
                    organization_id=org_id,
                    stripe_subscription_id=sub_id,
                    plan=plan,
                    status='active',
                    monthly_price=limits['price'],
                )
                db.add(sub)
                db.commit()

        elif event['type'] == 'customer.subscription.deleted':
            sub_data = event['data']['object']
            customer_id = sub_data['customer']
            org = db.execute(
                select(Organization).where(Organization.stripe_customer_id == customer_id)
            ).scalar_one_or_none()
            if org:
                limits = PLAN_LIMITS['free']
                org.plan = 'free'
                org.max_users = limits['max_users']
                org.max_sites = limits['max_sites']
                org.max_simulations_per_month = limits['max_simulations']
                db.commit()

        return jsonify({"received": True}), 200
    except Exception as e:
        db.rollback()
        logger.exception("Billing webhook error: %s", e)
        return jsonify({"error": "An internal error occurred"}), 500
    finally:
        db.close()


@billing_bp.route('/subscription', methods=['GET'])
@require_auth
def get_subscription():
    from flask import g
    db = get_session()
    try:
        org = db.execute(select(Organization).where(Organization.id == g.org_id)).scalar_one_or_none()
        sub = db.execute(
            select(Subscription)
            .where(Subscription.organization_id == g.org_id)
            .order_by(Subscription.created_at.desc())
        ).scalar_one_or_none()
        return jsonify({"success": True, "data": {
            "plan": org.plan if org else 'free',
            "status": sub.status if sub else 'none',
            "monthly_price": sub.monthly_price if sub else 0,
        }})
    except Exception as e:
        logger.exception("Billing API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@billing_bp.route('/usage', methods=['GET'])
@require_auth
def get_usage():
    from flask import g
    db = get_session()
    try:
        from datetime import datetime, timezone
        org = db.execute(select(Organization).where(Organization.id == g.org_id)).scalar_one_or_none()
        sites_count = db.execute(
            select(func.count()).select_from(MonitoredSite).where(
                MonitoredSite.organization_id == g.org_id
            )
        ).scalar() or 0
        limits = PLAN_LIMITS.get(org.plan, PLAN_LIMITS['free']) if org else PLAN_LIMITS['free']

        # Count simulations created this month for the org
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        simulations_used = db.execute(
            select(func.count()).select_from(Simulation).where(
                Simulation.organization_id == g.org_id,
                Simulation.created_at >= month_start,
            )
        ).scalar() or 0

        # Count org users
        users_used = db.execute(
            select(func.count()).select_from(User).where(
                User.organization_id == g.org_id,
                User.is_active == True,
            )
        ).scalar() or 1

        # Get panels/categories usage from user preferences
        prefs = db.execute(
            select(UserPreferences).where(UserPreferences.user_id == g.user_id)
        ).scalar_one_or_none()
        panels_visible = 26  # default: all grid panels
        categories_selected = 0
        if prefs:
            categories_selected = len(prefs.interest_categories or [])
            config = prefs.dashboard_config or {}
            removed = config.get('removed_panels', [])
            panel_order = config.get('panel_order', [])
            if panel_order:
                panels_visible = len([p for p in panel_order if p not in removed])
            else:
                panels_visible = 26 - len(removed)

        return jsonify({"success": True, "data": {
            "plan": org.plan if org else 'free',
            "sites_used": sites_count,
            "sites_limit": limits['max_sites'],
            "simulations_used": simulations_used,
            "simulations_limit": limits['max_simulations'],
            "users_used": users_used,
            "users_limit": limits['max_users'],
            "panels_used": panels_visible,
            "panels_limit": limits['max_panels'],
            "categories_used": categories_selected,
            "categories_limit": limits['max_categories'],
        }})
    except Exception as e:
        logger.exception("Billing API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()
