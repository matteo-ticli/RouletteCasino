import random
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


class RouletteWheel:
    """Class to simulate a French Roulette wheel."""

    def __init__(self):
        # Define the number-color mapping for French Roulette
        # 0 is green, 1-36 are either red or black
        self.numbers = list(range(37))  # 0 to 36
        self.colors = self._assign_colors()

    def _assign_colors(self):
        # French Roulette color assignments
        red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        colors = {}
        for number in self.numbers:
            if number == 0:
                colors[number] = 'Green'
            elif number in red_numbers:
                colors[number] = 'Red'
            else:
                colors[number] = 'Black'
        return colors

    def spin(self):
        """Simulate a spin of the roulette wheel."""
        number = random.choice(self.numbers)
        color = self.colors[number]
        return number, color


class Strategy(ABC):
    """Abstract base class for betting strategies."""

    def __init__(self, name, initial_bankroll=1000, base_bet=10):
        """
        :param name: Name of the strategy.
        :param initial_bankroll: Starting amount of money.
        :param base_bet: Initial bet amount.
        """
        self.name = name
        self.initial_bankroll = initial_bankroll
        self.bankroll = initial_bankroll
        self.base_bet = base_bet
        self.current_bet = base_bet
        self.history = []  # To track bankroll over time

    @abstractmethod
    def place_bet(self):
        """Determine the bet for the current spin."""
        pass

    @abstractmethod
    def update(self, result):
        """Update the strategy based on the spin result."""
        pass

    def reset(self):
        """Reset the strategy to initial state."""
        self.bankroll = self.initial_bankroll
        self.current_bet = self.base_bet
        self.history = []


class MartingaleStrategy(Strategy):
    """Martingale betting strategy: double the bet after a loss."""

    def __init__(self, initial_bankroll=1000, base_bet=10):
        super().__init__('Martingale', initial_bankroll, base_bet)

    def place_bet(self):
        """Bet on Red."""
        return {'type': 'Color', 'value': 'Red', 'amount': self.current_bet}

    def update(self, result):
        """Update bankroll based on the spin result."""
        number, color = result
        bet = self.place_bet()
        if color == bet['value']:
            self.bankroll += bet['amount']
            self.current_bet = self.base_bet  # Reset bet after win
        else:
            self.bankroll -= bet['amount']
            self.current_bet *= 2  # Double bet after loss
            # Prevent bet from exceeding bankroll
            if self.current_bet > self.bankroll:
                self.current_bet = self.bankroll
        self.history.append(self.bankroll)


class FlatBettingStrategy(Strategy):
    """Flat betting strategy: bet the same amount each spin."""

    def __init__(self, initial_bankroll=1000, base_bet=10):
        super().__init__('Flat Betting', initial_bankroll, base_bet)

    def place_bet(self):
        """Bet on Black."""
        return {'type': 'Color', 'value': 'Black', 'amount': self.current_bet}

    def update(self, result):
        """Update bankroll based on the spin result."""
        number, color = result
        bet = self.place_bet()
        if color == bet['value']:
            self.bankroll += bet['amount']
        else:
            self.bankroll -= bet['amount']
        self.history.append(self.bankroll)


class ReverseMartingaleStrategy(Strategy):
    """Reverse Martingale: double the bet after a win."""

    def __init__(self, initial_bankroll=1000, base_bet=10):
        super().__init__('Reverse Martingale', initial_bankroll, base_bet)

    def place_bet(self):
        """Bet on Odd numbers."""
        return {'type': 'Parity', 'value': 'Odd', 'amount': self.current_bet}

    def update(self, result):
        """Update bankroll based on the spin result."""
        number, color = result
        bet = self.place_bet()
        if number == 0:
            # 0 is neither odd nor even; treat as loss
            self.bankroll -= bet['amount']
            self.current_bet = self.base_bet
        elif (number % 2 == 1 and bet['value'] == 'Odd') or (number % 2 == 0 and bet['value'] == 'Even'):
            self.bankroll += bet['amount']
            self.current_bet *= 2  # Double bet after win
        else:
            self.bankroll -= bet['amount']
            self.current_bet = self.base_bet  # Reset after loss
        # Prevent bet from exceeding bankroll
        if self.current_bet > self.bankroll:
            self.current_bet = self.bankroll
        self.history.append(self.bankroll)


class Simulation:
    """Class to manage the roulette simulation."""

    def __init__(self, strategies, num_spins=100, initial_bankroll=1000, base_bet=10):
        """
        :param strategies: List of Strategy instances.
        :param num_spins: Number of roulette spins to simulate.
        :param initial_bankroll: Starting amount for each strategy.
        :param base_bet: Base bet amount for each strategy.
        """
        self.wheel = RouletteWheel()
        self.strategies = strategies
        self.num_spins = num_spins
        self.initial_bankroll = initial_bankroll
        self.base_bet = base_bet

    def run(self):
        """Execute the simulation."""
        # Reset all strategies
        for strategy in self.strategies:
            strategy.reset()

        for spin in range(self.num_spins):
            result = self.wheel.spin()
            for strategy in self.strategies:
                if strategy.bankroll < strategy.current_bet:
                    # Skip if bankroll is insufficient
                    strategy.history.append(strategy.bankroll)
                    continue
                strategy.update(result)

    def get_results(self):
        """Retrieve the cumulative bankroll history for each strategy."""
        results = {}
        for strategy in self.strategies:
            results[strategy.name] = strategy.history
        return pd.DataFrame(results)


class Dashboard:
    """Class to visualize the simulation results."""

    def __init__(self, results_df):
        """
        :param results_df: DataFrame containing cumulative bankroll histories.
        """
        self.results_df = results_df

    def plot_cumulative_returns(self):
        """Plot the cumulative returns of each strategy."""
        plt.figure(figsize=(12, 8))
        for column in self.results_df.columns:
            plt.plot(self.results_df.index, self.results_df[column], label=column)
        plt.title('Cumulative Returns of Betting Strategies')
        plt.xlabel('Spin Number')
        plt.ylabel('Bankroll')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_percentage_change(self):
        """Plot the percentage change in bankroll over time."""
        pct_change = self.results_df.pct_change().fillna(0)
        plt.figure(figsize=(12, 8))
        for column in pct_change.columns:
            plt.plot(pct_change.index, pct_change[column], label=column)
        plt.title('Percentage Change in Bankroll of Betting Strategies')
        plt.xlabel('Spin Number')
        plt.ylabel('Percentage Change')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def summary_statistics(self):
        """Print summary statistics for each strategy."""
        final_bankroll = self.results_df.iloc[-1]
        total_spins = len(self.results_df)
        initial_bankroll = self.results_df.iloc[0]

        print("Summary Statistics:")
        print("-------------------")
        for strategy in self.results_df.columns:
            final = final_bankroll[strategy]
            profit = final - initial_bankroll[strategy]
            roi = (profit / initial_bankroll[strategy]) * 100
            print(f"{strategy}: Final Bankroll = {final:.2f}, Profit = {profit:.2f}, ROI = {roi:.2f}%")


def main():
    # Define strategies
    strategies = [
        MartingaleStrategy(initial_bankroll=1000, base_bet=10),
        FlatBettingStrategy(initial_bankroll=1000, base_bet=10),
        ReverseMartingaleStrategy(initial_bankroll=1000, base_bet=10)
    ]

    # Initialize simulation
    simulation = Simulation(strategies=strategies, num_spins=100, initial_bankroll=1000, base_bet=10)

    # Run simulation
    simulation.run()

    # Get results
    results_df = simulation.get_results()

    # Initialize dashboard
    dashboard = Dashboard(results_df)

    # Plot cumulative returns
    dashboard.plot_cumulative_returns()

    # Plot percentage change
    dashboard.plot_percentage_change()

    # Print summary statistics
    dashboard.summary_statistics()


if __name__ == "__main__":
    main()
