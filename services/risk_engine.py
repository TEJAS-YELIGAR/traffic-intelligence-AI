def calculate_risk_score(probability, traffic_density):

    base = probability * 100

    traffic_weight = traffic_density * 5

    return round(base + traffic_weight, 2)
