from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
from .models import Portfolio, Holding, Transaction, Stock
from .live_market_service import get_live_market_service
import logging

logger = logging.getLogger(__name__)

class TradingService:
    """Service for executing trades and managing portfolio"""
    
    def __init__(self, user):
        self.user = user
        self.default_portfolio = self._get_default_portfolio()
    
    def _get_default_portfolio(self):
        """Get or create default portfolio for user"""
        portfolio, created = Portfolio.objects.get_or_create(
            user=self.user,
            is_default=True,
            defaults={
                'name': 'Default Portfolio',
                'description': 'Main trading portfolio',
                'cash_balance': Decimal('10000.00'), 
                'is_active': True
            }
        )
        return portfolio
    
    def get_portfolio_summary(self):
        """Get comprehensive portfolio summary with live prices"""
        try:
            holdings = Holding.objects.filter(portfolio=self.default_portfolio)
            
            total_value = self.default_portfolio.cash_balance
            total_cost = Decimal('0.00')
            total_gain_loss = Decimal('0.00')
            
            holdings_data = []
            
            for holding in holdings:
                stock_detail = get_live_market_service().get_stock_detail(holding.stock.symbol)
                
                if stock_detail:
                    current_price = Decimal(str(stock_detail['current_price']))
                    market_value = current_price * holding.quantity
                    cost_basis = holding.average_cost * holding.quantity
                    gain_loss = market_value - cost_basis
                    
                    total_value += market_value
                    total_cost += cost_basis
                    total_gain_loss += gain_loss
                    
                    holdings_data.append({
                        'id': holding.id,
                        'symbol': holding.stock.symbol,
                        'name': holding.stock.name,
                        'quantity': holding.quantity,
                        'average_cost': float(holding.average_cost),
                        'current_price': float(current_price),
                        'market_value': float(market_value),
                        'cost_basis': float(cost_basis),
                        'gain_loss': float(gain_loss),
                        'gain_loss_percent': float((gain_loss / cost_basis * 100) if cost_basis > 0 else 0),
                        'day_change': float(stock_detail['day_change']),
                        'day_change_percent': float(stock_detail['day_change_percent'])
                    })
                else:
                    current_price = holding.stock.current_price
                    market_value = current_price * holding.quantity
                    cost_basis = holding.average_cost * holding.quantity
                    gain_loss = market_value - cost_basis
                    
                    total_value += market_value
                    total_cost += cost_basis
                    total_gain_loss += gain_loss
                    
                    holdings_data.append({
                        'id': holding.id,
                        'symbol': holding.stock.symbol,
                        'name': holding.stock.name,
                        'quantity': holding.quantity,
                        'average_cost': float(holding.average_cost),
                        'current_price': float(current_price),
                        'market_value': float(market_value),
                        'cost_basis': float(cost_basis),
                        'gain_loss': float(gain_loss),
                        'gain_loss_percent': float((gain_loss / cost_basis * 100) if cost_basis > 0 else 0),
                        'day_change': float(holding.stock.day_change),
                        'day_change_percent': float(holding.stock.day_change_percent)
                    })
            
            total_gain_loss_percent = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
            
            return {
                'portfolio_id': self.default_portfolio.id,
                'portfolio_name': self.default_portfolio.name,
                'cash_balance': float(self.default_portfolio.cash_balance),
                'total_value': float(total_value),
                'total_cost': float(total_cost),
                'total_gain_loss': float(total_gain_loss),
                'total_gain_loss_percent': float(total_gain_loss_percent),
                'holdings': holdings_data,
                'holdings_count': len(holdings_data),
                'last_updated': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            raise
    
    def buy_stock(self, symbol, quantity, price=None):
        """Buy stock with live pricing"""
        try:
            with transaction.atomic():
                # Convert quantity to Decimal to ensure type compatibility
                quantity = Decimal(str(quantity))
                
                stock = Stock.objects.filter(symbol=symbol.upper(), is_active=True).first()
                if not stock:
                    raise ValueError(f"Stock {symbol} not found or inactive")
                
                if price is None:
                    stock_detail = get_live_market_service().get_stock_detail(symbol.upper())
                    if stock_detail:
                        price = Decimal(str(stock_detail['current_price']))
                    else:
                        price = stock.current_price
                else:
                    # Convert price to Decimal to ensure type compatibility
                    price = Decimal(str(price))

                total_cost = price * quantity
                
                if total_cost > self.default_portfolio.cash_balance:
                    raise ValueError(f"Insufficient funds. Need ${total_cost}, have ${self.default_portfolio.cash_balance}")
                
                self.default_portfolio.cash_balance -= total_cost
                self.default_portfolio.save()

                holding, created = Holding.objects.get_or_create(
                    portfolio=self.default_portfolio,
                stock=stock,
                defaults={
                        'quantity': quantity,
                        'average_cost': price,
                        'total_cost': total_cost,
                    'first_purchase_date': timezone.now(),
                        'last_transaction_date': timezone.now()
                    }
                )
                
                if not created:
                    total_quantity = holding.quantity + quantity
                    total_invested = (holding.average_cost * holding.quantity) + total_cost
                    new_average_cost = total_invested / total_quantity
                    
                    holding.quantity = total_quantity
                    holding.average_cost = new_average_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    holding.total_cost = total_invested
            holding.last_transaction_date = timezone.now()
            holding.save()
            
            transaction_record = Transaction.objects.create(
                    portfolio=self.default_portfolio,
                stock=stock,
                    transaction_type='BUY',
                quantity=quantity,
                price=price,
                total_amount=total_cost,
                transaction_date=timezone.now()
            )
            
            logger.info(f"Buy order executed: {quantity} shares of {symbol} at ${price}")
            
            return {
                'success': True,
                'transaction_id': transaction_record.id,
                'symbol': symbol,
                'quantity': quantity,
                'price': float(price),
                'total_cost': float(total_cost),
                'new_cash_balance': float(self.default_portfolio.cash_balance)
            }
                
        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
            raise
    
    def sell_stock(self, symbol, quantity, price=None):
        """Sell stock with live pricing"""
        try:
            with transaction.atomic():
                # Convert quantity to Decimal to ensure type compatibility
                quantity = Decimal(str(quantity))

                stock = Stock.objects.filter(symbol=symbol.upper(), is_active=True).first()
                if not stock:
                    raise ValueError(f"Stock {symbol} not found or inactive")
                
                holding = Holding.objects.filter(
                    portfolio=self.default_portfolio,
                    stock=stock
                ).first()
                
                if not holding or holding.quantity < quantity:
                    raise ValueError(f"Insufficient shares. Have {holding.quantity if holding else 0}, trying to sell {quantity}")

                if price is None:
                    stock_detail = get_live_market_service().get_stock_detail(symbol.upper())
                    if stock_detail:
                        price = Decimal(str(stock_detail['current_price']))
                    else:
                        price = stock.current_price
                else:
                    # Convert price to Decimal to ensure type compatibility
                    price = Decimal(str(price))
                
                total_proceeds = price * quantity
                
                cost_basis = holding.average_cost * quantity
                gain_loss = total_proceeds - cost_basis
                
                self.default_portfolio.cash_balance += total_proceeds
                self.default_portfolio.save()

                remaining_quantity = holding.quantity - quantity
                if remaining_quantity > 0:
                    holding.quantity = remaining_quantity
                    holding.total_cost = holding.average_cost * remaining_quantity
                    holding.last_transaction_date = timezone.now()
                    holding.save()
                else:
                    holding.delete()
            
            transaction_record = Transaction.objects.create(
                portfolio=self.default_portfolio,
                stock=stock,
                transaction_type='SELL',
                quantity=quantity,
                price=price,
                total_amount=total_proceeds,
                gain_loss=gain_loss,
                transaction_date=timezone.now()
            )
            
            logger.info(f"Sell order executed: {quantity} shares of {symbol} at ${price}")
            
            return {
                'success': True,
                'transaction_id': transaction_record.id,
                'symbol': symbol,
                'quantity': quantity,
                'price': float(price),
                'total_proceeds': float(total_proceeds),
                'gain_loss': float(gain_loss),
                'new_cash_balance': float(self.default_portfolio.cash_balance)
            }
                
        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
            raise
    
    def get_transaction_history(self, limit=50):
        """Get transaction history for portfolio"""
        try:
            transactions = Transaction.objects.filter(
                portfolio=self.default_portfolio
            ).order_by('-transaction_date')[:limit]
            
            return [
                {
                    'id': t.id,
                    'symbol': t.stock.symbol,
                    'name': t.stock.name,
                    'transaction_type': t.transaction_type,
                    'quantity': t.quantity,
                    'price': float(t.price),
                    'total_amount': float(t.total_amount),
                    'gain_loss': float(t.gain_loss) if t.gain_loss else None,
                    'timestamp': t.transaction_date.isoformat()
                }
                for t in transactions
            ]
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            raise
    
    def get_holding_detail(self, symbol):
        """Get detailed holding information for a specific stock"""
        try:
            holding = Holding.objects.filter(
                portfolio=self.default_portfolio,
                stock__symbol=symbol.upper()
            ).first()
            
            if not holding:
                return None
            
            # Get live price
            stock_detail = get_live_market_service().get_stock_detail(symbol.upper())
            current_price = Decimal(str(stock_detail['current_price'])) if stock_detail else holding.stock.current_price
            
            market_value = current_price * holding.quantity
            cost_basis = holding.average_cost * holding.quantity
            gain_loss = market_value - cost_basis
            gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
            
            return {
                'symbol': holding.stock.symbol,
                'name': holding.stock.name,
                'quantity': holding.quantity,
                'average_cost': float(holding.average_cost),
                'current_price': float(current_price),
                'market_value': float(market_value),
                'cost_basis': float(cost_basis),
                'gain_loss': float(gain_loss),
                'gain_loss_percent': float(gain_loss_percent),
                'day_change': float(stock_detail['day_change']) if stock_detail else float(holding.stock.day_change),
                'day_change_percent': float(stock_detail['day_change_percent']) if stock_detail else float(holding.stock.day_change_percent)
            }
            
        except Exception as e:
            logger.error(f"Error getting holding detail: {e}")
            raise