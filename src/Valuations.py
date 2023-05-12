from src.Company import Company
import numpy as np

# TODO: Add P/E Valuation
def ebitda_val(company:Company, growth_rate, discount_rate):
    # Calculate the coefficient from growth/discount rates
    assert growth_rate < discount_rate, 'The growth Rate for the DCF must be less than the discount rate'
    profit_coeff = (1 + discount_rate) / (discount_rate - growth_rate)
    # Get the profit from operations
    ebitda = company.get_ebitda()
    # Apply the coefficient to find continuous value
    ent_value = ebitda * profit_coeff
    # Apply the net debt measures
    net_debt = company.get_net_debt()
    net_value = ent_value - net_debt

    return np.round(net_value, 2)