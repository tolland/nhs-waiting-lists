import numpy as np
import pandas as pd
from scipy import stats


# Statistical tests for normality
def test_normality(data: pd.Series, name: str) -> dict:
    """Test normality using multiple statistical tests."""
    # Remove any infinite or NaN values
    clean_data = data.dropna().replace([np.inf, -np.inf], np.nan).dropna()

    if len(clean_data) < 8:
        return {"name": name, "error": "Insufficient data"}

    # Sample if too large (some tests have limits)
    if len(clean_data) > 5000:
        clean_data = clean_data.sample(5000, random_state=42)

    shapiro_stat, shapiro_p = stats.shapiro(clean_data)
    jb_stat, jb_p = stats.jarque_bera(clean_data)

    return {
        "return_type": name,
        "n_obs": len(clean_data),
        "mean": clean_data.mean(),
        "std": clean_data.std(),
        "skewness": stats.skew(clean_data),
        "kurtosis": stats.kurtosis(clean_data),
        "shapiro_stat": shapiro_stat,
        "shapiro_p": shapiro_p,
        "jb_stat": jb_stat,
        "jb_p": jb_p,
        "is_normal_shapiro": shapiro_p > 0.05,
        "is_normal_jb": jb_p > 0.05
    }
