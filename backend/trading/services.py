from django.db import transaction, F
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict
import logging

from .models import Portfolio, Holding, Transaction, Stock, User

logger = logging.getLogger(__name__)


class TradingService:
    
    @staticmethod
    @transaction.atomic
    def execute_buy_order(
        user: User,
        portfolio_id: str,
        stock_id: str,
        quantity: Decimal,
        price: Decimal,
        fees: Decimal = Decimal('0.00')
    ) -> Dict:
        try:
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if price <= 0:
                raise ValueError("Price must be positive")
            
            portfolio = Portfolio.objects.select_for_update().get(
                id=portfolio_id, 
                user=user,
                is_active=True
            )
            stock = Stock.objects.get(id=stock_id, is_active=True)
            
            total_cost = (quantity * price) + fees
            
            if portfolio.cash_balance < total_cost:
                return {
                    'success': False,
                    'error': 'Insufficient funds',
                    'required': float(total_cost),
                    'available': float(portfolio.cash_balance)
                }
            
            portfolio.cash_balance = F('cash_balance') - total_cost
            portfolio.save()
            
            holding, created = Holding.objects.select_for_update().get_or_create(
                portfolio=portfolio,
                stock=stock,
                defaults={
                    'quantity': Decimal('0'),
                    'average_cost': Decimal('0'),
                    'total_cost': Decimal('0'),
                    'current_value': Decimal('0'),
                    'first_purchase_date': timezone.now(),
                    'last_transaction_date': timezone.now(),
                }
            )
            
            old_quantity = holding.quantity
            old_total_cost = holding.total_cost
            
            new_quantity = old_quantity + quantity
            new_total_cost = old_total_cost + (quantity * price)
            new_average_cost = new_total_cost / new_quantity if new_quantity > 0 else Decimal('0')
            
            holding.quantity = new_quantity
            holding.average_cost = new_average_cost.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
            holding.total_cost = new_total_cost
            holding.current_value = new_quantity * stock.current_price
            holding.unrealized_gain_loss = holding.current_value - new_total_cost
            holding.unrealized_gain_loss_percent = (
                (holding.unrealized_gain_loss / new_total_cost * 100) 
                if new_total_cost > 0 else Decimal('0')
            )
            holding.last_transaction_date = timezone.now()
            
            if created:
                holding.first_purchase_date = timezone.now()
            
            holding.save()
            
            transaction_record = Transaction.objects.create(
                portfolio=portfolio,
                stock=stock,
                transaction_type='buy',
                status='executed',
                quantity=quantity,
                price=price,
                total_amount=total_cost,
                fees=fees,
                transaction_date=timezone.now(),
                notes=f"Buy {quantity} shares of {stock.symbol} at ${price}"
            )
            
            TradingService._update_portfolio_metrics(portfolio)
            
            logger.info(f"Buy order executed: {quantity} shares of {stock.symbol} for user {user.username}")
            
            return {
                'success': True,
                'transaction_id': str(transaction_record.id),
                'holding_id': str(holding.id),
                'new_quantity': float(holding.quantity),
                'new_average_cost': float(holding.average_cost),
                'total_cost': float(total_cost)
            }
            
        except Portfolio.DoesNotExist:
            return {'success': False, 'error': 'Portfolio not found'}
        except Stock.DoesNotExist:
            return {'success': False, 'error': 'Stock not found'}
        except Exception as e:
            logger.error(f"Error executing buy order: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    @transaction.atomic
    def execute_sell_order(
        user: User,
        portfolio_id: str,
        stock_id: str,
        quantity: Decimal,
        price: Decimal,
        fees: Decimal = Decimal('0.00')
    ) -> Dict:
        try:
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if price <= 0:
                raise ValueError("Price must be positive")

            portfolio = Portfolio.objects.select_for_update().get(
                id=portfolio_id, 
                user=user,
                is_active=True
            )
            stock = Stock.objects.get(id=stock_id, is_active=True)
            
            try:
                holding = Holding.objects.select_for_update().get(
                    portfolio=portfolio,
                    stock=stock
                )
            except Holding.DoesNotExist:
                return {'success': False, 'error': 'No holding found for this stock'}
            
            if holding.quantity < quantity:
                return {
                    'success': False,
                    'error': 'Insufficient shares',
                    'requested': float(quantity),
                    'available': float(holding.quantity)
                }
            
            gross_proceeds = quantity * price
            net_proceeds = gross_proceeds - fees
            
            portfolio.cash_balance = F('cash_balance') + net_proceeds
            portfolio.save()
            
            cost_basis = holding.average_cost * quantity
            realized_gain_loss = gross_proceeds - cost_basis
            
            new_quantity = holding.quantity - quantity
            if new_quantity > 0:
                new_total_cost = holding.total_cost - cost_basis
                holding.quantity = new_quantity
                holding.total_cost = new_total_cost
                holding.current_value = new_quantity * stock.current_price
                holding.unrealized_gain_loss = holding.current_value - new_total_cost
                holding.unrealized_gain_loss_percent = (
                    (holding.unrealized_gain_loss / new_total_cost * 100) 
                    if new_total_cost > 0 else Decimal('0')
                )
                holding.last_transaction_date = timezone.now()
                holding.save()
            else:
                holding.delete()
            
            transaction_record = Transaction.objects.create(
                portfolio=portfolio,
                stock=stock,
                transaction_type='sell',
                status='executed',
                quantity=quantity,
                price=price,
                total_amount=net_proceeds,
                fees=fees,
                transaction_date=timezone.now(),
                notes=f"Sell {quantity} shares of {stock.symbol} at ${price}. Realized P/L: ${realized_gain_loss:.2f}"
            )
            
            TradingService._update_portfolio_metrics(portfolio)
            
            logger.info(f"Sell order executed: {quantity} shares of {stock.symbol} for user {user.username}")
            
            return {
                'success': True,
                'transaction_id': str(transaction_record.id),
                'remaining_quantity': float(new_quantity) if new_quantity > 0 else 0,
                'realized_gain_loss': float(realized_gain_loss),
                'net_proceeds': float(net_proceeds)
            }
            
        except Portfolio.DoesNotExist:
            return {'success': False, 'error': 'Portfolio not found'}
        except Stock.DoesNotExist:
            return {'success': False, 'error': 'Stock not found'}
        except Exception as e:
            logger.error(f"Error executing sell order: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    @transaction.atomic
    def add_cash(user: User, portfolio_id: str, amount: Decimal) -> Dict:
        try:
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            portfolio = Portfolio.objects.select_for_update().get(
                id=portfolio_id, 
                user=user,
                is_active=True
            )
            
            portfolio.cash_balance = F('cash_balance') + amount
            portfolio.save()
            
            transaction_record = Transaction.objects.create(
                portfolio=portfolio,
                transaction_type='deposit',
                status='executed',
                total_amount=amount,
                transaction_date=timezone.now(),
                notes=f"Cash deposit of ${amount}"
            )
            
            TradingService._update_portfolio_metrics(portfolio)
            
            return {
                'success': True,
                'transaction_id': str(transaction_record.id),
                'new_balance': float(portfolio.cash_balance)
            }
            
        except Portfolio.DoesNotExist:
            return {'success': False, 'error': 'Portfolio not found'}
        except Exception as e:
            logger.error(f"Error adding cash: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _update_portfolio_metrics(portfolio: Portfolio):
        portfolio.refresh_from_db()
        
        holdings = portfolio.holdings.all()
        
        total_invested = sum(holding.total_cost for holding in holdings)
        total_current_value = sum(holding.current_value for holding in holdings)
        total_portfolio_value = total_current_value + portfolio.cash_balance
        total_return = total_current_value - total_invested
        total_return_percent = (
            (total_return / total_invested * 100) 
            if total_invested > 0 else Decimal('0')
        )
        
        Portfolio.objects.filter(id=portfolio.id).update(
            total_value=total_portfolio_value,
            invested_amount=total_invested,
            total_return=total_return,
            total_return_percent=total_return_percent.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        )
    
    @staticmethod
    def get_portfolio_summary(user: User, portfolio_id: str) -> Dict:
        try:
            portfolio = Portfolio.objects.get(
                id=portfolio_id, 
                user=user,
                is_active=True
            )
            
            holdings = portfolio.holdings.select_related('stock').all()
            
            for holding in holdings:
                holding.current_value = holding.quantity * holding.stock.current_price
                holding.unrealized_gain_loss = holding.current_value - holding.total_cost
                holding.unrealized_gain_loss_percent = (
                    (holding.unrealized_gain_loss / holding.total_cost * 100) 
                    if holding.total_cost > 0 else Decimal('0')
                )
                holding.save()
            
            TradingService._update_portfolio_metrics(portfolio)
            portfolio.refresh_from_db()
            
            return {
                'success': True,
                'portfolio': {
                    'id': str(portfolio.id),
                    'name': portfolio.name,
                    'total_value': float(portfolio.total_value),
                    'cash_balance': float(portfolio.cash_balance),
                    'invested_amount': float(portfolio.invested_amount),
                    'total_return': float(portfolio.total_return),
                    'total_return_percent': float(portfolio.total_return_percent),
                    'holdings_count': holdings.count()
                }
            }
            
        except Portfolio.DoesNotExist:
            return {'success': False, 'error': 'Portfolio not found'}
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {str(e)}")
            return {'success': False, 'error': str(e)}


class MarketDataService:
    
    @staticmethod
    @transaction.atomic
    def update_stock_price(stock_symbol: str, new_price: Decimal) -> bool:
        try:
            stock = Stock.objects.get(symbol=stock_symbol, is_active=True)
            old_price = stock.current_price
            
            stock.previous_close = old_price
            stock.current_price = new_price
            stock.day_change = new_price - old_price
            stock.day_change_percent = (
                (stock.day_change / old_price * 100) 
                if old_price > 0 else Decimal('0')
            )
            stock.last_price_update = timezone.now()
            stock.save()
            
            holdings = Holding.objects.filter(stock=stock)
            for holding in holdings:
                holding.current_value = holding.quantity * new_price
                holding.unrealized_gain_loss = holding.current_value - holding.total_cost
                holding.unrealized_gain_loss_percent = (
                    (holding.unrealized_gain_loss / holding.total_cost * 100) 
                    if holding.total_cost > 0 else Decimal('0')
                )
                holding.save()
                
                TradingService._update_portfolio_metrics(holding.portfolio)
            
            logger.info(f"Updated {stock_symbol} price to {new_price}")
            return True
            
        except Stock.DoesNotExist:
            logger.error(f"Stock {stock_symbol} not found")
            return False
        except Exception as e:
            logger.error(f"Error updating stock price: {str(e)}")
            return False