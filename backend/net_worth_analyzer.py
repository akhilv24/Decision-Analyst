"""
Net Worth Tracker and Analysis Module
Calculates total assets, liabilities, and net worth trends
"""

from backend.models import db, Asset, Liability
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class NetWorthAnalyzer:
    """Analyze and track user net worth over time."""
    
    @staticmethod
    def get_current_net_worth(user):
        """Calculate current net worth."""
        try:
            active_assets = Asset.query.filter_by(user_id=user.id, is_active=True).all()
            active_liabilities = Liability.query.filter_by(user_id=user.id, is_active=True).all()
            
            total_assets = sum(asset.value for asset in active_assets)
            total_liabilities = sum(liability.amount for liability in active_liabilities)
            
            net_worth = total_assets - total_liabilities
            
            return {
                'net_worth': net_worth,
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'assets_count': len(active_assets),
                'liabilities_count': len(active_liabilities)
            }
        except Exception as e:
            logger.error(f"Error calculating net worth: {str(e)}")
            return None
    
    @staticmethod
    def get_asset_breakdown(user):
        """Get breakdown of assets by type."""
        try:
            assets = Asset.query.filter_by(user_id=user.id, is_active=True).all()
            
            breakdown = {}
            for asset in assets:
                if asset.asset_type not in breakdown:
                    breakdown[asset.asset_type] = {'count': 0, 'value': 0}
                breakdown[asset.asset_type]['count'] += 1
                breakdown[asset.asset_type]['value'] += asset.value
            
            return breakdown
        except Exception as e:
            logger.error(f"Error getting asset breakdown: {str(e)}")
            return {}
    
    @staticmethod
    def get_liability_breakdown(user):
        """Get breakdown of liabilities by type."""
        try:
            liabilities = Liability.query.filter_by(user_id=user.id, is_active=True).all()
            
            breakdown = {}
            estimated_interest = 0
            
            for liability in liabilities:
                if liability.liability_type not in breakdown:
                    breakdown[liability.liability_type] = {'count': 0, 'amount': 0, 'interest': 0}
                
                breakdown[liability.liability_type]['count'] += 1
                breakdown[liability.liability_type]['amount'] += liability.amount
                
                # Calculate annual interest
                if liability.interest_rate:
                    annual_interest = (liability.amount * liability.interest_rate) / 100
                    breakdown[liability.liability_type]['interest'] += annual_interest
                    estimated_interest += annual_interest
            
            return {
                'breakdown': breakdown,
                'estimated_annual_interest': estimated_interest
            }
        except Exception as e:
            logger.error(f"Error getting liability breakdown: {str(e)}")
            return {}
    
    @staticmethod
    def add_asset(user_id, name, asset_type, value, description=''):
        """Add a new asset."""
        try:
            asset = Asset(
                user_id=user_id,
                name=name,
                asset_type=asset_type,
                value=value,
                description=description
            )
            db.session.add(asset)
            db.session.commit()
            logger.info(f"Asset added for user {user_id}: {name} ₹{value}")
            return asset
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding asset: {str(e)}")
            return None
    
    @staticmethod
    def add_liability(user_id, name, liability_type, amount, interest_rate=0, monthly_payment=0):
        """Add a new liability."""
        try:
            liability = Liability(
                user_id=user_id,
                name=name,
                liability_type=liability_type,
                amount=amount,
                interest_rate=interest_rate,
                monthly_payment=monthly_payment
            )
            db.session.add(liability)
            db.session.commit()
            logger.info(f"Liability added for user {user_id}: {name} ₹{amount}")
            return liability
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding liability: {str(e)}")
            return None
    
    @staticmethod
    def update_asset_value(asset_id, new_value):
        """Update asset value."""
        try:
            asset = Asset.query.get(asset_id)
            if asset:
                asset.value = new_value
                asset.updated_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"Asset {asset_id} updated to ₹{new_value}")
                return asset
            return None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating asset: {str(e)}")
            return None
    
    @staticmethod
    def get_net_worth_trend(user, months=12):
        """Get net worth trend over time (projection based on current data)."""
        try:
            current = NetWorthAnalyzer.get_current_net_worth(user)
            
            # For now, return current value repeated (would need historical data for real trend)
            trend = {
                'current': current['net_worth'],
                'months': months,
                'annual_projected': current['net_worth']  # Would calculate based on savings/debt payoff
            }
            
            return trend
        except Exception as e:
            logger.error(f"Error getting net worth trend: {str(e)}")
            return None
    
    @staticmethod
    def get_net_worth_summary(user):
        """Get comprehensive net worth summary."""
        try:
            nw = NetWorthAnalyzer.get_current_net_worth(user)
            assets_breakdown = NetWorthAnalyzer.get_asset_breakdown(user)
            liabilities_breakdown = NetWorthAnalyzer.get_liability_breakdown(user)
            
            return {
                'net_worth': nw,
                'assets_breakdown': assets_breakdown,
                'liabilities': liabilities_breakdown,
                'calculated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting net worth summary: {str(e)}")
            return None
