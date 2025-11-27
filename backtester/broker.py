"""
Backtesting Broker

Simulates a trading exchange. Manages account balance, positions,
and order execution.
"""


class Broker:
    """
    A simulated broker that handles trades, commissions, and portfolio value.
    """

    def __init__(self, initial_cash: float = 10_000.0, commission: float = 0.0):
        """
        Initializes the Broker.

        Args:
            initial_cash: The starting cash balance.
            commission: The commission rate for trades (e.g., 0.001 for 0.1%).
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.commission = commission
        self.positions = {}  # Holds the quantity of each asset

    def get_portfolio_value(self, current_prices: dict[str, float]) -> float:
        """
        Calculates the total current value of the portfolio.

        Args:
            current_prices: A dictionary mapping symbols to their current price.

        Returns:
            The total portfolio value (cash + value of all positions).
        """
        value = self.cash
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                value += quantity * current_prices.get(symbol, 0)
        return value

    def buy(self, symbol: str, quantity: float, price: float):
        """
        Simulates a buy order.

        Args:
            symbol: The symbol to buy.
            quantity: The amount to buy.
            price: The price per unit.
        """
        cost = quantity * price
        commission_cost = cost * self.commission
        total_cost = cost + commission_cost

        if self.cash < total_cost:
            return

        self.cash -= total_cost
        self.positions[symbol] = self.positions.get(symbol, 0) + quantity
        return

    def sell(self, symbol: str, quantity: float, price: float):
        """
        Simulates a sell order.

        Args:
            symbol: The symbol to sell.
            quantity: The amount to sell.
            price: The price per unit.
        """
        if self.positions.get(symbol, 0) < quantity:
            return

        revenue = quantity * price
        commission_cost = revenue * self.commission
        total_revenue = revenue - commission_cost

        self.cash += total_revenue
        self.positions[symbol] -= quantity
        return
